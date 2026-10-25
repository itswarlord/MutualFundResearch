"""
fetcher.py - Ingests mutual fund data from official and community sources across all equity categories:
1. AMFI Official Daily NAV Master (portal.amfiindia.com)
2. MFAPI.in for complete historical daily NAV series (with ThreadPool concurrent batching)
3. AMFI Total Expense Ratio (TER) Tracker
"""

import urllib.request
import json
import csv
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

AMFI_NAV_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
MFAPI_BASE_URL = "https://api.mfapi.in/mf"
TER_DATA_URL = "https://raw.githubusercontent.com/captn3m0/india-mutual-fund-ter-tracker/main/data.csv"

HEADERS = {"User-Agent": "Mozilla/5.0 (MutualFundResearchBot/2.0)"}


def fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch text content from a URL with browser User-Agent."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def normalize_category_name(cat_str: str) -> Optional[str]:
    """Normalizes raw AMFI category heading into standard SEBI equity categories."""
    c = cat_str.lower()
    if "large cap" in c and "mid" not in c:
        return "Large Cap"
    if "mid cap" in c and "large" not in c:
        return "Mid Cap"
    if "small cap" in c:
        return "Small Cap"
    if "flexi cap" in c:
        return "Flexi Cap"
    if "multi cap" in c:
        return "Multi Cap"
    if "large & mid" in c or "large and mid" in c:
        return "Large & Mid Cap"
    if "elss" in c:
        return "ELSS"
    if "focused" in c:
        return "Focused Fund"
    if "value" in c or "contra" in c:
        return "Value & Contra"
    if "dividend" in c:
        return "Dividend Yield"
    if "sectoral" in c or "thematic" in c:
        return "Sectoral & Thematic"
    return None


def fetch_all_amfi_equity_schemes(plan_filter: str = "Direct", target_categories: Optional[List[str]] = None) -> List[Dict]:
    """
    Parses AMFI's official NAV master file and extracts all Equity schemes categorized by SEBI type.
    """
    raw_content = fetch_url(AMFI_NAV_URL)
    lines = raw_content.splitlines()

    current_cat = None
    current_amc = ""
    schemes = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("Open Ended Schemes("):
            m = re.search(r"Open Ended Schemes\((Equity Scheme[^\)]*)\)", line)
            if m:
                norm = normalize_category_name(m.group(1))
                if target_categories is None or (norm in target_categories):
                    current_cat = norm
                else:
                    current_cat = None
            else:
                current_cat = None
            continue

        if current_cat:
            if ";" not in line:
                current_amc = line
            else:
                parts = line.split(";")
                if len(parts) >= 8:
                    scheme_code = parts[0].strip()
                    isin_growth = parts[1].strip() if parts[1] != "-" else None
                    isin_div = parts[2].strip() if parts[2] != "-" else None
                    scheme_name = parts[3].strip()
                    plan = parts[4].strip()
                    option = parts[5].strip()
                    nav_str = parts[6].strip()
                    nav_date = parts[7].strip()

                    # Filter for Growth option (primary wealth generation vehicle)
                    if "growth" not in option.lower():
                        continue

                    # Filter for Direct / Regular plan
                    if plan_filter and plan_filter.lower() not in plan.lower():
                        continue

                    try:
                        nav_val = float(nav_str)
                    except ValueError:
                        nav_val = None

                    schemes.append({
                        "scheme_code": int(scheme_code),
                        "scheme_name": scheme_name,
                        "amc": current_amc,
                        "category": current_cat,
                        "isin_growth": isin_growth,
                        "isin_div": isin_div,
                        "plan": plan,
                        "option": option,
                        "latest_nav": nav_val,
                        "nav_date": nav_date,
                    })

    return schemes


def fetch_ter_map() -> Dict[str, Dict[str, float]]:
    """Downloads and indexes the Total Expense Ratio (TER) tracker data."""
    try:
        raw_csv = fetch_url(TER_DATA_URL)
        reader = csv.DictReader(io.StringIO(raw_csv))
        ter_lookup = {}

        for row in reader:
            raw_name = row.get("Scheme Name", "")
            if not raw_name:
                continue

            norm_name = re.sub(r"[^a-z0-9]", "", raw_name.lower().replace("flexicap", "flexi cap"))

            def parse_num(val):
                try:
                    return float(val.strip())
                except (ValueError, TypeError, AttributeError):
                    return None

            ter_lookup[norm_name] = {
                "raw_name": raw_name,
                "direct_ter": parse_num(row.get("Direct Plan - Total TER (%)")),
                "regular_ter": parse_num(row.get("Regular Plan - Total TER (%)")),
                "direct_base_ter": parse_num(row.get("Direct Plan - Base Expense Ratio (BER) (%)")),
                "regular_base_ter": parse_num(row.get("Regular Plan - Base Expense Ratio (BER) (%)")),
            }

        return ter_lookup
    except Exception as e:
        print(f"[Warning] Failed to fetch TER data: {e}")
        return {}


def match_ter_for_scheme(scheme_name: str, ter_lookup: Dict[str, Dict]) -> Dict:
    """Matches an AMFI scheme name with the corresponding TER entry."""
    clean_name = re.sub(r"(?:-|\b)(Direct|Regular|Plan|Growth|Option|Dividend|IDCW)(?:\b|-)", "", scheme_name, flags=re.I)
    norm = re.sub(r"[^a-z0-9]", "", clean_name.lower().replace("flexicap", "flexi cap"))

    if norm in ter_lookup:
        return ter_lookup[norm]

    for k, v in ter_lookup.items():
        if norm in k or k in norm:
            return v

    tokens = [t for t in norm.split() if len(t) > 3]
    for k, v in ter_lookup.items():
        if all(token in k for token in tokens):
            return v

    return {"direct_ter": None, "regular_ter": None}


def fetch_nav_history(scheme_code: int, max_retries: int = 3) -> Tuple[Optional[Dict], List[Dict]]:
    """Fetches full historical NAV array for a scheme code from mfapi.in."""
    url = f"{MFAPI_BASE_URL}/{scheme_code}"
    for attempt in range(max_retries):
        try:
            content = fetch_url(url, timeout=12)
            data = json.loads(content)
            if data.get("status") == "SUCCESS" or "data" in data:
                meta = data.get("meta", {})
                nav_list = data.get("data", [])
                return meta, nav_list
        except Exception as e:
            if attempt == max_retries - 1:
                pass
            time.sleep(0.5)
    return None, []


def fetch_nav_history_batch(scheme_codes: List[int], max_workers: int = 8) -> Dict[int, List[Dict]]:
    """
    Fetches full historical NAV series concurrently across multiple scheme codes.
    Returns mapping: {scheme_code: nav_records_list}.
    """
    results: Dict[int, List[Dict]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_code = {executor.submit(fetch_nav_history, code): code for code in scheme_codes}
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                meta, navs = future.result()
                if navs:
                    results[code] = navs
            except Exception as e:
                print(f"[Error] Batch fetch failed for code {code}: {e}")
    return results
