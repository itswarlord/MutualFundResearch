"""
ai_summarizer.py - Dynamic Mutual Fund Executive Summary Generator powered by Google Gemini API.

Provides:
1. Direct integration with Google Gemini 2.0 Flash / 1.5 Flash (cheapest and fastest).
2. Institutional prompt engineering tailored to Indian Mutual Funds analytics (SEBI standards).
3. Persistent caching system in data/ai_summaries_cache.json to prevent redundant API calls.
4. Automatic fallback to quantitative deterministic generator when API key is unavailable or during network errors.
5. Batch generation with rate-limiting backoff and progress tracking.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

# Ensure repo root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "data")
CACHE_FILE = os.path.join(DATA_DIR, "ai_summaries_cache.json")

# Default cheapest and fastest Gemini model
DEFAULT_MODEL = "gemini-2.0-flash"
BACKUP_MODEL = "gemini-1.5-flash"
GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"


def get_api_key() -> Optional[str]:
    """
    Retrieves Gemini API key from environment variables or .env file.
    Checks:
    1. GEMINI_API_KEY
    2. GOOGLE_API_KEY
    3. .env file in repo root
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key and key.strip():
        return key.strip()

    # Look for .env file in REPO_ROOT
    env_path = os.path.join(REPO_ROOT, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k in ("GEMINI_API_KEY", "GOOGLE_API_KEY") and v:
                            return v
        except Exception:
            pass

    return None


def load_cache() -> Dict[str, Any]:
    """Loads cached AI summaries from data/ai_summaries_cache.json."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, Any]) -> None:
    """Saves AI summaries cache to data/ai_summaries_cache.json."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def get_fund_cache_key(fund: Dict[str, Any]) -> str:
    """Creates a deterministic cache key based on scheme code and performance state."""
    code = fund.get("scheme_code", "0")
    as_of = fund.get("as_of_date", "")
    nav = fund.get("latest_nav", "")
    score = fund.get("composite_score", "")
    return f"{code}_{as_of}_{nav}_{score}"


def build_prompt_payload(fund: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the structured Gemini prompt and request payload.
    Encodes full quantitative context for the mutual fund.
    """
    metrics = {
        "scheme_name": fund.get("scheme_name"),
        "amc": fund.get("amc"),
        "category": fund.get("category"),
        "benchmark": fund.get("benchmark_name"),
        "composite_rank": fund.get("composite_rank"),
        "composite_score": fund.get("composite_score"),
        "rating_tier": fund.get("rating_tier"),
        "returns": {
            "1m": fund.get("return_1m"),
            "3m": fund.get("return_3m"),
            "6m": fund.get("return_6m"),
            "1y": fund.get("return_1y"),
            "2y_cagr": fund.get("return_2y_cagr"),
            "3y_cagr": fund.get("return_3y_cagr"),
            "5y_cagr": fund.get("return_5y_cagr"),
            "inception_cagr": fund.get("return_inception_cagr"),
        },
        "risk_and_capm": {
            "volatility_stddev": fund.get("standard_deviation"),
            "beta": fund.get("beta"),
            "r_squared": fund.get("r_squared"),
            "jensens_alpha": fund.get("alpha"),
            "sharpe_ratio": fund.get("sharpe_ratio"),
            "sortino_ratio": fund.get("sortino_ratio"),
            "max_drawdown_3y": fund.get("max_drawdown_3y"),
            "upside_capture": fund.get("upside_capture"),
            "downside_capture": fund.get("downside_capture"),
            "capture_ratio": fund.get("capture_ratio"),
        },
        "agency_ratings": {
            "morningstar_rating": fund.get("morningstar_rating"),
            "morningstar_medalist": fund.get("morningstar_medalist"),
            "valueresearch_rating": fund.get("valueresearch_rating"),
            "valueresearch_risk_grade": fund.get("valueresearch_risk_grade"),
            "valueresearch_avg_rating": fund.get("valueresearch_avg_rating"),
            "crisil_rank": fund.get("crisil_rank"),
            "one_finance_score": fund.get("one_finance_score"),
            "advisorkhoj_quartile": fund.get("advisorkhoj_quartile"),
        },
        "fund_scale_and_cost": {
            "aum_cr": fund.get("aum_cr"),
            "direct_ter": fund.get("direct_ter"),
        }
    }

    system_instruction = (
        "You are a Senior Quantitative Mutual Fund Research Analyst specializing in Indian equity mutual funds (regulated by SEBI). "
        "Analyze the provided fund metrics and produce a high-caliber, institutional research summary consisting of EXACTLY 5 or 6 concise, data-driven lines.\n\n"
        "Lines Structure:\n"
        "1. Mandate & Strategy: Scheme name, AMC, category orientation, and core positioning vs. designated SEBI benchmark.\n"
        "2. Composite Ranking: Rank within category peer group, multi-agency score out of 100, and quality tier evaluation.\n"
        "3. Return Persistence: Compounding track record across 1Y, 3Y, 5Y CAGR, and cycle endurance.\n"
        "4. Risk Management: Annualized volatility (StdDev), market sensitivity (Beta), Sharpe and Sortino downside resilience.\n"
        "5. Alpha & Capture Asymmetry: Jensen's Alpha active selection prowess and dual-market capture ratio dynamics (upside participation vs downside defense).\n"
        "6. Consensus & Scale: Ratings matrix (Morningstar, Value Research, CRISIL, 1 Finance), Live AUM scale, and Direct Plan TER efficiency.\n\n"
        "CRITICAL RULES:\n"
        "- Output strictly in JSON with format: {\"summary_lines\": [\"line 1...\", \"line 2...\", \"line 3...\", \"line 4...\", \"line 5...\", \"line 6...\"], \"ai_badge\": \"Gemini 2.0 Flash\"}\n"
        "- Exactly 5 or 6 lines in the list. Each line must be a complete, well-crafted sentence.\n"
        "- Do NOT mention regular plan expense ratios, distributor commissions, or savings. Only mention Direct TER.\n"
        "- Avoid generic boilerplate. Synthesize the fund's specific metrics into actionable financial insights."
    )

    user_prompt = f"Analyze this fund and output 5-6 summary lines in valid JSON:\n{json.dumps(metrics, indent=2)}"

    return {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\n{user_prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json"
        }
    }


def call_gemini_api(
    payload: Dict[str, Any],
    api_key: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3
) -> Optional[List[str]]:
    """
    Calls Google Gemini REST API using standard urllib.
    Handles rate limits (HTTP 429) with exponential backoff.
    """
    url = GEMINI_API_URL_TEMPLATE.format(model=model, api_key=api_key)
    json_data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MutualFundResearch-AI-Summarizer/1.0",
    }

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    candidates = body.get("candidates", [])
                    if candidates:
                        text_part = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = json.loads(text_part)
                        lines = parsed.get("summary_lines", [])
                        if isinstance(lines, list) and 5 <= len(lines) <= 6:
                            return [l.strip() for l in lines if isinstance(l, str) and l.strip()]
        except urllib.error.HTTPError as e:
            # Check for Rate Limit (HTTP 429) or Service Unavailable (503)
            if e.code in (429, 503):
                wait_time = (2 ** attempt) * 2
                time.sleep(wait_time)
            elif e.code == 404 and model != BACKUP_MODEL:
                # If model not available, try backup model
                return call_gemini_api(payload, api_key, model=BACKUP_MODEL, max_retries=1)
            else:
                return None
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None

    return None


def generate_fund_summary_lines_fallback(fund: Dict[str, Any]) -> List[str]:
    """Deterministic fallback using quantitative rules when Gemini API is unavailable."""
    from storage import generate_fund_summary_lines
    return generate_fund_summary_lines(fund)


def get_fund_summary(
    fund: Dict[str, Any],
    api_key: Optional[str] = None,
    cache: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Retrieves the 5-6 line summary for a fund:
    1. Checks cache if use_cache is True.
    2. Calls Gemini API if api_key is available.
    3. Falls back to deterministic quantitative generator if API call fails or key is missing.

    Returns dict with keys:
    - summary_lines: List[str]
    - summary: str
    - source: "gemini-2.0-flash" | "cached-gemini" | "quantitative-fallback"
    """
    cache_key = get_fund_cache_key(fund)

    # 1. Check Cache
    if use_cache and cache is not None and cache_key in cache:
        cached_entry = cache[cache_key]
        lines = cached_entry.get("summary_lines", [])
        if isinstance(lines, list) and 5 <= len(lines) <= 6:
            return {
                "summary_lines": lines,
                "summary": "\n".join(lines),
                "source": cached_entry.get("source", "cached-gemini"),
            }

    # 2. Try Gemini API if API key provided
    resolved_key = api_key or get_api_key()
    if resolved_key:
        payload = build_prompt_payload(fund)
        ai_lines = call_gemini_api(payload, resolved_key, model=model)
        if ai_lines and 5 <= len(ai_lines) <= 6:
            result = {
                "summary_lines": ai_lines,
                "summary": "\n".join(ai_lines),
                "source": model,
            }
            if cache is not None:
                cache[cache_key] = result
            return result

    # 3. Fallback to Quantitative Template Engine
    fallback_lines = generate_fund_summary_lines_fallback(fund)
    return {
        "summary_lines": fallback_lines,
        "summary": "\n".join(fallback_lines),
        "source": "quantitative-fallback",
    }


def batch_generate_ai_summaries(
    funds: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    limit: Optional[int] = None,
    force_refresh: bool = False,
    delay_between_calls: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Enriches all funds with dynamic 5-6 line summaries.
    Uses cached summaries where possible, queries Gemini API for uncached funds,
    and falls back to rule-based generation as needed.
    """
    resolved_key = api_key or get_api_key()
    cache = load_cache() if not force_refresh else {}
    cache_dirty = False

    target_funds = funds[:limit] if limit else funds
    ai_count = 0
    cached_count = 0
    fallback_count = 0

    for idx, fund in enumerate(target_funds):
        cache_key = get_fund_cache_key(fund)
        already_cached = (not force_refresh) and (cache_key in cache)

        res = get_fund_summary(
            fund,
            api_key=resolved_key,
            cache=cache,
            use_cache=not force_refresh,
            model=model
        )

        fund["summary_lines"] = res["summary_lines"]
        fund["summary"] = res["summary"]
        fund["summary_source"] = res["source"]

        if already_cached:
            cached_count += 1
        elif "gemini" in res["source"]:
            ai_count += 1
            cache_dirty = True
            if delay_between_calls > 0:
                time.sleep(delay_between_calls)
        else:
            fallback_count += 1

    if cache_dirty:
        save_cache(cache)

    return target_funds


def main():
    """CLI utility for generating and inspecting AI summaries."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate AI Mutual Fund Summaries using Google Gemini API")
    parser.add_argument("--api-key", help="Google Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model (default: gemini-2.0-flash)")
    parser.add_argument("--limit", type=int, help="Limit number of funds to process")
    parser.add_argument("--force", action="store_true", help="Force refresh bypassing cache")
    parser.add_argument("--check-key", action="store_true", help="Test API key connectivity and exit")
    args = parser.parse_args()

    key = args.api_key or get_api_key()

    if args.check_key:
        if not key:
            print("❌ No Gemini API key found in environment or .env file.")
            sys.exit(1)
        print(f"Testing Gemini connectivity with model {args.model}...")
        test_fund = {
            "scheme_name": "Parag Parikh Flexi Cap Fund",
            "amc": "PPFAS Mutual Fund",
            "category": "Flexi Cap",
            "benchmark_name": "NIFTY 500 TRI",
            "composite_rank": 1,
            "composite_score": 92.5,
            "rating_tier": "BEST (Tier 1 - Elite)",
            "return_3y_cagr": 21.4,
            "return_1y": 28.5,
            "standard_deviation": 11.2,
            "beta": 0.74,
            "alpha": 6.85,
            "sharpe_ratio": 1.25,
            "direct_ter": 0.62,
            "aum_cr": 72450.0,
        }
        res = get_fund_summary(test_fund, api_key=key, use_cache=False, model=args.model)
        print(f"Result Source: {res['source']}")
        print("Generated Lines:")
        for idx, line in enumerate(res["summary_lines"]):
            print(f"  {idx+1}. {line}")
        sys.exit(0)

    # Load web funds.json
    funds_json_path = os.path.join(REPO_ROOT, "web", "data", "funds.json")
    if not os.path.exists(funds_json_path):
        print(f"❌ Cannot find {funds_json_path}")
        sys.exit(1)

    with open(funds_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    funds = data.get("funds", [])
    print(f"Loaded {len(funds)} funds. Running AI summarizer (API Key present: {bool(key)})...")
    batch_generate_ai_summaries(funds, api_key=key, model=args.model, limit=args.limit, force_refresh=args.force)

    # Save updated funds.json
    with open(funds_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Completed AI summary generation.")


if __name__ == "__main__":
    main()
