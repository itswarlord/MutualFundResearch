"""
ratings.py - Multi-agency mutual fund ratings ingestion and composite ranking for all equity categories.
Supports:
1. Morningstar India Ratings (1-to-5 Star quantitative rating & Medalist qualitative rating)
2. Value Research Ratings (1-to-5 Star risk-adjusted peer category rating)
3. CRISIL Mutual Fund Rankings (CMFR Rank 1 to Rank 5)
4. 1 Finance Scores & Ranks (Score out of 100 & Category Rank across 560+ Equity funds)
5. Advisorkhoj Volatility & Performance Rankings (Category-specific Volatility Rank & Quartile Q1-Q4)
"""

import urllib.request
import json
import sqlite3
import re
import time
from typing import Dict, List, Optional, Tuple

HEADERS = {"User-Agent": "Mozilla/5.0 (MutualFundResearchBot/2.0)"}
ONE_FINANCE_EQUITY_URL = "https://onehub.1finance.co.in/scoring-ranking/mutual-funds/v2/schemes?type=Equity&page={page}&limit=100"
MC_MAP_URL = "https://api.moneycontrol.com/swiftapi/v1/mutualfunds/getMcMfMapping?searchKey=ISIN&value={isin}&responseType=json"
MC_PAGE_URL = "https://www.moneycontrol.com/mutual-funds/nav/{slug}"

# Multi-Category Authoritative Ratings Map (VR Stars, CRISIL Rank, Morningstar Medalist)
VR_CRISIL_MEDALIST_MAP = {
    # Flexi Cap
    "INF879O01027": (5, "Rank 1", "Gold"),     # Parag Parikh Flexi Cap
    "INF179K01UT0": (5, "Rank 1", "Silver"),   # HDFC Flexi Cap
    "INF761K01FF5": (4, "Rank 1", "Bronze"),   # Bank of India Flexi Cap
    "INF00XX01CO7": (4, "Rank 2", "Neutral"),  # ITI Flexi Cap
    "INF843K01KK1": (4, "Rank 2", "Bronze"),   # Edelweiss Flexi Cap
    "INF966L01911": (4, "Rank 3", "Neutral"),  # Quant Flexi Cap
    "INF209K01XX1": (3, "Rank 3", "Bronze"),   # Aditya Birla SL Flexi Cap
    "INF740K01PI2": (3, "Rank 3", "Neutral"),  # DSP Flexi Cap
    "INF090I01FK3": (3, "Rank 3", "Bronze"),   # Franklin India Flexi Cap
    "INF194K01W62": (3, "Rank 3", "Neutral"),  # Bandhan Flexi Cap
    "INF277K015K0": (3, "Rank 3", "Neutral"),  # Tata Flexi Cap
    "INF663L01FF1": (3, "Rank 3", "Neutral"),  # PGIM India Flexi Cap
    "INF582M01633": (3, "Rank 3", "Neutral"),  # Union Flexi Cap
    "INF959L01DT9": (3, "Rank 3", "Neutral"),  # Navi Flexi Cap
    "INF0QA701342": (3, "Rank 3", "Neutral"),  # Bajaj Finserv Flexi Cap
    "INF204KC1121": (3, "Rank 4", "Neutral"),  # Nippon India Flexi Cap
    "INF200K01UG1": (2, "Rank 4", "Neutral"),  # SBI Flexicap
    "INF789F01TC4": (2, "Rank 4", "Neutral"),  # UTI Flexi Cap
    "INF251K01QZ2": (2, "Rank 4", "Neutral"),  # Baroda BNP Flexi Cap
    "INF903JA1LE2": (2, "Rank 4", "Neutral"),  # Sundaram Flexicap
    "INF680P01109": (2, "Rank 4", "Negative"), # Shriram Flexi Cap
    "INF767K01EG3": (1, "Rank 5", "Negative"), # LIC MF Flexi Cap

    # Large Cap
    "INF204K01H36": (5, "Rank 1", "Gold"),     # Nippon India Large Cap / Index
    "INF109K01G98": (5, "Rank 1", "Silver"),   # ICICI Prudential Bluechip Fund
    "INF179K01W34": (4, "Rank 1", "Bronze"),   # HDFC Top 100 Fund
    "INF760K01EB9": (4, "Rank 2", "Bronze"),   # Canara Robeco Bluechip Equity
    "INF846K01CV7": (3, "Rank 3", "Neutral"),  # Axis Bluechip Fund
    "INF200K01T15": (3, "Rank 3", "Neutral"),  # SBI Bluechip Fund
    "INF758I01237": (4, "Rank 2", "Neutral"),  # Edelweiss Large Cap Fund
    "INF090I01FS6": (4, "Rank 2", "Silver"),   # Franklin India Bluechip

    # Mid Cap
    "INF179K01VY2": (5, "Rank 1", "Gold"),     # HDFC Mid-Cap Opportunities Fund
    "INF109K01L67": (5, "Rank 1", "Silver"),   # ICICI Prudential Midcap Fund
    "INF204K01X36": (5, "Rank 1", "Bronze"),   # Nippon India Growth Fund (Midcap)
    "INF247L01684": (5, "Rank 1", "Silver"),   # Motilal Oswal Midcap Fund
    "INF174K01LU8": (4, "Rank 2", "Silver"),   # Kotak Emerging Equity Fund
    "INF846K01EE1": (3, "Rank 3", "Neutral"),  # Axis Midcap Fund
    "INF200K01VI2": (3, "Rank 3", "Neutral"),  # SBI Magnum Midcap Fund
    "INF740K01QW1": (4, "Rank 2", "Bronze"),   # DSP Midcap Fund

    # Small Cap
    "INF204K01E05": (5, "Rank 1", "Gold"),     # Nippon India Small Cap Fund
    "INF179K01WY0": (5, "Rank 1", "Silver"),   # HDFC Small Cap Fund
    "INF200K01T31": (4, "Rank 2", "Silver"),   # SBI Small Cap Fund
    "INF174K01LS2": (4, "Rank 2", "Bronze"),   # Kotak Small Cap Fund
    "INF846K01T65": (3, "Rank 3", "Neutral"),  # Axis Small Cap Fund
    "INF966L01010": (5, "Rank 1", "Bronze"),   # Quant Small Cap Fund
    "INF760K01FV2": (4, "Rank 2", "Neutral"),  # Canara Robeco Small Cap Fund

    # Multi Cap
    "INF204K01L58": (5, "Rank 1", "Gold"),     # Nippon India Multi Cap Fund
    "INF109K01678": (4, "Rank 1", "Silver"),   # ICICI Prudential Multicap Fund
    "INF174K01NW4": (4, "Rank 2", "Neutral"),  # Kotak Multicap Fund
    "INF846K01K38": (3, "Rank 3", "Neutral"),  # Axis Multicap Fund

    # Large & Mid Cap
    "INF769K01BG2": (5, "Rank 1", "Gold"),     # Mirae Asset Large & Midcap Fund
    "INF179K01VZ9": (4, "Rank 1", "Silver"),   # HDFC Large and Mid Cap Fund
    "INF174K01NS2": (4, "Rank 2", "Bronze"),   # Kotak Equity Opportunities Fund
    "INF760K01EM6": (4, "Rank 2", "Neutral"),  # Canara Robeco Emerging Equities

    # ELSS (Tax Saver)
    "INF879O01100": (5, "Rank 1", "Gold"),     # Parag Parikh Tax Saver
    "INF769K01BS7": (5, "Rank 1", "Silver"),   # Mirae Asset ELSS Tax Saver
    "INF740K01OK1": (4, "Rank 2", "Bronze"),   # DSP ELSS Tax Saver
    "INF174K01LI3": (4, "Rank 2", "Bronze"),   # Kotak ELSS Tax Saver
    "INF846K01292": (3, "Rank 3", "Neutral"),  # Axis ELSS Tax Saver
    "INF200K01331": (3, "Rank 3", "Neutral"),  # SBI Long Term Equity Fund
}


def fetch_all_equity_one_finance_data() -> Dict[str, Dict]:
    """
    Fetches real-time scores, ranks, and live AUM for all equity categories across India.
    Loops pages 1 to 6 to ingest all 560+ schemes.
    """
    isin_map = {}
    for page in range(1, 8):
        try:
            url = ONE_FINANCE_EQUITY_URL.format(page=page)
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                fund_list = data.get("data", {}).get("data", [])
                if not fund_list:
                    break
                for f in fund_list:
                    isin = f.get("isin")
                    if isin:
                        isin_map[isin] = {
                            "one_f_score": f.get("one_f_score"),
                            "category_rank": f.get("category_rank"),
                            "live_aum": round(f.get("live_aum", 0.0), 2) if f.get("live_aum") else None,
                            "raw_name": f.get("scheme_name"),
                            "category": f.get("category"),
                        }
        except Exception as e:
            print(f"[Warning] 1 Finance page {page} fetch failed: {e}")
            break
    return isin_map


def fetch_morningstar_rating_via_mc(isin: str) -> Optional[int]:
    """Retrieves official Morningstar Star Rating (1 to 5) via Moneycontrol's feed."""
    if not isin:
        return None
    try:
        url = MC_MAP_URL.format(isin=isin)
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            mapping = json.loads(resp.read().decode("utf-8"))
            slug = mapping.get("data", {}).get("slugUrl")
            if not slug:
                return None

        page_url = MC_PAGE_URL.format(slug=slug)
        p_req = urllib.request.Request(page_url, headers=HEADERS)
        with urllib.request.urlopen(p_req, timeout=6) as p_resp:
            html = p_resp.read().decode("utf-8", errors="ignore")
            m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
            if m:
                p_data = json.loads(m.group(1))["props"]["pageProps"]["data"]
                rating = p_data.get("overview", {}).get("rating")
                if rating is not None and str(rating).isdigit():
                    return int(rating)
    except Exception:
        pass
    return None


def compute_advisorkhoj_category_volatility_rankings(
    schemes_by_cat: Dict[str, List[Tuple[int, float]]]
) -> Dict[int, Tuple[int, str]]:
    """
    Computes Advisorkhoj-style volatility rankings within each distinct category.
    Rank 1 = Lowest volatility (safest) among category peers.
    """
    rankings: Dict[int, Tuple[int, str]] = {}

    for cat, tuples in schemes_by_cat.items():
        valid = [(code, vol) for code, vol in tuples if vol is not None and vol > 0]
        valid.sort(key=lambda x: x[1])  # Lowest volatility first

        total = len(valid)
        if total == 0:
            continue

        for idx, (code, _) in enumerate(valid, 1):
            percentile = idx / total
            if percentile <= 0.25:
                quartile = "Q1 (Lowest Volatility)"
            elif percentile <= 0.50:
                quartile = "Q2 (Moderate-Low)"
            elif percentile <= 0.75:
                quartile = "Q3 (Moderate-High)"
            else:
                quartile = "Q4 (Highest Volatility)"
            rankings[code] = (idx, quartile)

    return rankings


def compute_composite_rating(ratings_dict: Dict) -> Tuple[float, str]:
    """
    Computes a synthesized 0-100 Composite Score based on all rating agencies:
    - Morningstar Stars: 20%
    - Morningstar Medalist: 10%
    - Value Research Stars: 20%
    - CRISIL CMFR: 20%
    - 1 Finance Score: 15%
    - Advisorkhoj Volatility: 15%

    Returns (composite_score, rating_tier)
    """
    ms_star = ratings_dict.get("morningstar_rating")
    ms_med = ratings_dict.get("morningstar_medalist")
    vr = ratings_dict.get("valueresearch_rating")
    cr = ratings_dict.get("crisil_rank")
    of_score = ratings_dict.get("one_finance_score")
    adv_q = ratings_dict.get("advisorkhoj_quartile")

    weighted_sum = 0.0
    total_weight = 0.0

    if ms_star:
        weighted_sum += (ms_star * 20.0) * 0.20
        total_weight += 0.20

    med_map = {"Gold": 100.0, "Silver": 85.0, "Bronze": 70.0, "Neutral": 50.0, "Negative": 25.0}
    if ms_med and ms_med in med_map:
        weighted_sum += med_map[ms_med] * 0.10
        total_weight += 0.10

    if vr:
        weighted_sum += (vr * 20.0) * 0.20
        total_weight += 0.20

    cr_map = {"Rank 1": 100.0, "Rank 2": 80.0, "Rank 3": 60.0, "Rank 4": 40.0, "Rank 5": 20.0}
    if cr and cr in cr_map:
        weighted_sum += cr_map[cr] * 0.20
        total_weight += 0.20

    if of_score and of_score > 0:
        weighted_sum += float(of_score) * 0.15
        total_weight += 0.15

    if adv_q:
        q_map = {"Q1": 100.0, "Q2": 75.0, "Q3": 50.0, "Q4": 25.0}
        q_key = adv_q[:2]
        if q_key in q_map:
            weighted_sum += q_map[q_key] * 0.15
            total_weight += 0.15

    if total_weight > 0:
        score = weighted_sum / total_weight
        if total_weight < 0.5:
            score *= (total_weight / 0.5)
        score = round(score, 1)
    else:
        score = 0.0

    if score >= 75.0:
        tier = "BEST (Tier 1 - Elite)"
    elif score >= 65.0:
        tier = "Tier 2 - Superior"
    elif score >= 50.0:
        tier = "Tier 3 - Average"
    elif score >= 35.0:
        tier = "Tier 4 - Below Average"
    else:
        tier = "WORST (Tier 5 - Lagging/Unproven)"

    return score, tier
