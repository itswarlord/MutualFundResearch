"""
main.py - Comprehensive pipeline runner for all Indian Equity Mutual Fund Categories:
- Large Cap
- Mid Cap
- Small Cap
- Flexi Cap
- Multi Cap
- Large & Mid Cap
- ELSS (Tax Saver)
- Focused Fund
- Value & Contra
- Dividend Yield

Generates:
1. Separate CSV files for each category in data/ (e.g., data/large_cap_summary.csv)
2. Master all-equity CSV (data/all_equity_summary.csv)
3. Single multi-sheet Excel workbook (data/Indian_Equity_Mutual_Funds_Master.xlsx)
   with dedicated tabs per category, sorted from "BEST" to "WORST".
"""

import argparse
import sys
import time
import sqlite3
from fetcher import (
    fetch_all_amfi_equity_schemes,
    fetch_ter_map,
    match_ter_for_scheme,
    fetch_nav_history,
    fetch_nav_history_batch
)
from analytics import (
    calculate_metrics,
    calculate_benchmark_metrics,
    CATEGORY_BENCHMARKS,
    get_category_benchmark_info,
    get_all_benchmark_scheme_codes
)
from storage import (
    init_db,
    save_scheme_meta,
    save_nav_history,
    save_fund_metrics,
    save_fund_ratings,
    export_all_equity_data,
    get_connection
)
from ratings import (
    fetch_all_equity_one_finance_data,
    fetch_morningstar_rating_via_mc,
    compute_advisorkhoj_category_volatility_rankings,
    compute_composite_rating,
    VR_CRISIL_MEDALIST_MAP,
    get_or_load_vr_pdf_ratings,
    match_scheme_to_vr_pdf,
    get_or_load_crisil_rankings,
    match_scheme_to_crisil,
)

DIVERSIFIED_EQUITY_CATEGORIES = [
    "Large Cap",
    "Mid Cap",
    "Small Cap",
    "Flexi Cap",
    "Multi Cap",
    "Large & Mid Cap",
    "ELSS",
    "Focused Fund",
    "Value & Contra",
    "Dividend Yield",
]


def run_full_equity_pipeline(categories=None, limit_per_cat=0, plan_filter="Direct"):
    if categories is None:
        categories = DIVERSIFIED_EQUITY_CATEGORIES

    print("=" * 80)
    print(" ALL EQUITY MUTUAL FUNDS RESEARCH PIPELINE (INDIA) 🇮🇳")
    print(f" Target Categories ({len(categories)}): {', '.join(categories)}")
    print("=" * 80)

    init_db()

    # 1. Fetch Benchmark Index Series per Category
    print("\n[1/6] Fetching SEBI Category Benchmark historical series...")
    bench_codes = get_all_benchmark_scheme_codes(categories)
    bench_histories = fetch_nav_history_batch(bench_codes, max_workers=6)
    for cat in categories:
        info = get_category_benchmark_info(cat)
        b_code = info["scheme_code"]
        b_hist = bench_histories.get(b_code, [])
        print(f"  - {cat:<20} -> {info['description']:<30} (Code: {b_code}, {len(b_hist)} daily NAVs)")

    # 2. Fetch all registered schemes from AMFI for target categories
    print(f"\n[2/6] Parsing AMFI NAV Master for '{plan_filter} Growth' equity schemes...")
    schemes = fetch_all_amfi_equity_schemes(plan_filter=plan_filter, target_categories=categories)
    print(f"Total schemes discovered: {len(schemes)}")

    # Filter/group by category
    schemes_by_cat = {}
    for s in schemes:
        schemes_by_cat.setdefault(s["category"], []).append(s)

    selected_schemes = []
    for cat in categories:
        cat_list = schemes_by_cat.get(cat, [])
        if limit_per_cat > 0:
            cat_list = cat_list[:limit_per_cat]
        selected_schemes.extend(cat_list)
        print(f"  - {cat:<20}: {len(cat_list)} schemes")

    print(f"Total schemes queued for processing: {len(selected_schemes)}")

    # 3. Fetch TER Mapping
    print("\n[3/6] Downloading Total Expense Ratio (TER) dataset...")
    ter_map = fetch_ter_map()
    print(f"Indexed {len(ter_map)} schemes with official TER data.")

    # 4. Fetch 1 Finance data across all equity schemes
    print("\n[4/6] Ingesting 1 Finance scores, ranks, and live AUM for all equity funds...")
    of_map = fetch_all_equity_one_finance_data()
    print(f"Loaded 1 Finance records for {len(of_map)} equity schemes.")

    # 5. Fetch NAV histories concurrently and compute analytics
    print(f"\n[5/6] Concurrently fetching historical NAV series (ThreadPoolExecutor)...")
    scheme_codes = [s["scheme_code"] for s in selected_schemes]
    t0 = time.time()
    nav_batch = fetch_nav_history_batch(scheme_codes, max_workers=8)
    print(f"Fetched historical NAVs for {len(nav_batch)}/{len(scheme_codes)} schemes in {time.time()-t0:.1f}s.")

    # Compute Performance & Risk Metrics
    print("Computing rolling returns, risk ratios, and CAPM benchmark metrics...")
    cat_vol_tuples = {}

    for idx, s in enumerate(selected_schemes, 1):
        code = s["scheme_code"]
        name = s["scheme_name"]
        cat = s["category"]

        save_scheme_meta(s)

        navs = nav_batch.get(code, [])
        if not navs:
            continue

        save_nav_history(code, navs)

        # Performance & Volatility
        metrics = calculate_metrics(navs)

        # CAPM & Capture Ratios against category-specific benchmark
        bench_info = get_category_benchmark_info(cat)
        bench_code = bench_info["scheme_code"]
        bench_history = bench_histories.get(bench_code, [])

        # Fallback to secondary benchmark if insufficient history
        if len(bench_history) < 250 and bench_info.get("fallback_code"):
            bench_history = bench_histories.get(bench_info["fallback_code"], [])

        bench_metrics = calculate_benchmark_metrics(navs, bench_history)
        if bench_metrics.get("beta") is None and bench_info.get("fallback_code"):
            fallback_hist = bench_histories.get(bench_info["fallback_code"], [])
            if fallback_hist:
                bench_metrics = calculate_benchmark_metrics(navs, fallback_hist)

        bench_metrics["benchmark_name"] = bench_info["description"]
        metrics.update(bench_metrics)

        # Match TER
        ter_info = match_ter_for_scheme(name, ter_map)

        save_fund_metrics(code, cat, metrics, ter_info)

        vol = metrics.get("volatility_3y")
        if vol is not None:
            cat_vol_tuples.setdefault(cat, []).append((code, vol))

    # Compute Advisorkhoj Category Volatility Rankings
    print("\n[6/6] Ingesting multi-agency ratings, computing composite scores, and ranking BEST to WORST...")
    adv_cat_rankings = compute_advisorkhoj_category_volatility_rankings(cat_vol_tuples)

    # Ingest Value Research official Scoreboard ratings from reference PDF (Page 85 onwards)
    pdf_ratings = get_or_load_vr_pdf_ratings()
    print(f"Loaded Value Research Scoreboard records ({len(pdf_ratings)} funds from reference PDF).")

    # Ingest CRISIL official CMFR rankings from intelligence.crisil.com
    crisil_ratings = get_or_load_crisil_rankings()
    print(f"Loaded CRISIL CMFR records ({len(crisil_ratings)} funds from CRISIL Intelligence).")

    # Ingest ratings per category and rank BEST to WORST
    for cat in categories:
        cat_funds = [s for s in selected_schemes if s["category"] == cat]
        cat_ratings_list = []

        for s in cat_funds:
            code = s["scheme_code"]
            name = s["scheme_name"]
            isin = s["isin_growth"]

            of_info = of_map.get(isin, {})
            one_f_score = of_info.get("one_f_score")
            one_f_rank = of_info.get("category_rank")
            live_aum = of_info.get("live_aum")

            adv_rank, adv_q = adv_cat_rankings.get(code, (None, None))

            # Match with Value Research PDF Scoreboard
            vr_match = match_scheme_to_vr_pdf(name, cat, pdf_ratings)
            vr_rating = None
            vr_risk_grade = None
            vr_avg_rating = None
            if vr_match:
                raw_r = vr_match.get("rating")
                vr_rating = raw_r if (raw_r and raw_r > 0) else None
                vr_risk_grade = vr_match.get("risk_grade")
                vr_avg_rating = vr_match.get("avg_rating")

            # Match with CRISIL official rankings
            crisil_match = match_scheme_to_crisil(name, cat, crisil_ratings)
            crisil_rank = crisil_match.get("crisil_rank") if crisil_match else None

            # Fallback to curated map if not matched
            ms_medalist = None
            if isin in VR_CRISIL_MEDALIST_MAP:
                map_vr, map_cr, map_med = VR_CRISIL_MEDALIST_MAP[isin]
                if vr_rating is None:
                    vr_rating = map_vr
                if crisil_rank is None:
                    crisil_rank = map_cr
                ms_medalist = map_med

            ms_star = fetch_morningstar_rating_via_mc(isin)
            if ms_star is None and vr_rating:
                ms_star = vr_rating

            payload = {
                "scheme_code": code,
                "category": cat,
                "morningstar_rating": ms_star,
                "morningstar_medalist": ms_medalist,
                "valueresearch_rating": vr_rating,
                "valueresearch_risk_grade": vr_risk_grade,
                "valueresearch_avg_rating": vr_avg_rating,
                "crisil_rank": crisil_rank,
                "one_finance_score": one_f_score,
                "one_finance_rank": one_f_rank,
                "advisorkhoj_volatility_rank": adv_rank,
                "advisorkhoj_quartile": adv_q,
                "aum_cr": live_aum,
            }

            score, tier = compute_composite_rating(payload)
            payload["composite_score"] = score
            payload["rating_tier"] = tier
            cat_ratings_list.append(payload)

        # Sort category funds BEST (Rank 1) to WORST
        cat_ratings_list.sort(key=lambda x: (x["composite_score"], x.get("aum_cr") or 0.0), reverse=True)
        for rk, item in enumerate(cat_ratings_list, 1):
            item["composite_rank"] = rk
            save_fund_ratings(item["scheme_code"], cat, item)

    # Export all separate CSV files and single Excel workbook
    print("\nGenerating separate CSV sheets per category and Master Excel Workbook...")
    export_all_equity_data()
    print("\n[Pipeline Complete] All data generated successfully!")


def update_ratings_from_pdf(categories=None):
    """
    Directly incorporates Value Research PDF ratings for all schemes already stored in DB,
    re-computes composite scores/tiers, and exports updated datasets.
    Runs in seconds with zero network calls.
    """
    if categories is None:
        categories = DIVERSIFIED_EQUITY_CATEGORIES

    init_db()
    pdf_ratings = get_or_load_vr_pdf_ratings()
    print(f"Loaded Value Research Scoreboard records ({len(pdf_ratings)} funds parsed from reference PDF).")
    crisil_ratings = get_or_load_crisil_rankings()
    print(f"Loaded CRISIL CMFR records ({len(crisil_ratings)} funds from CRISIL Intelligence).")

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        schemes = cursor.execute("""
            SELECT 
                s.scheme_code, 
                s.scheme_name, 
                s.category, 
                s.isin_growth, 
                m.volatility_3y, 
                r.morningstar_rating, 
                r.morningstar_medalist, 
                r.crisil_rank, 
                r.one_finance_score, 
                r.one_finance_rank, 
                r.aum_cr
            FROM schemes s
            LEFT JOIN fund_metrics m ON s.scheme_code = m.scheme_code
            LEFT JOIN fund_ratings r ON s.scheme_code = r.scheme_code
            WHERE s.category IN ({seq})
        """.format(seq=",".join(["?"] * len(categories))), categories).fetchall()

    cat_vol_tuples = {}
    for row in schemes:
        cat = row["category"]
        code = row["scheme_code"]
        vol = row["volatility_3y"]
        if vol is not None and vol > 0:
            cat_vol_tuples.setdefault(cat, []).append((code, vol))

    adv_cat_rankings = compute_advisorkhoj_category_volatility_rankings(cat_vol_tuples)

    matched_count = 0
    rated_count = 0

    for cat in categories:
        cat_funds = [s for s in schemes if s["category"] == cat]
        cat_ratings_list = []

        for s in cat_funds:
            code = s["scheme_code"]
            name = s["scheme_name"]
            isin = s["isin_growth"]

            adv_rank, adv_q = adv_cat_rankings.get(code, (None, None))

            vr_match = match_scheme_to_vr_pdf(name, cat, pdf_ratings)
            vr_rating = None
            vr_risk_grade = None
            vr_avg_rating = None
            if vr_match:
                matched_count += 1
                raw_r = vr_match.get("rating")
                if raw_r and raw_r > 0:
                    vr_rating = raw_r
                    rated_count += 1
                vr_risk_grade = vr_match.get("risk_grade")
                vr_avg_rating = vr_match.get("avg_rating")

            # Match with CRISIL official rankings
            crisil_match = match_scheme_to_crisil(name, cat, crisil_ratings)
            crisil_rank = None
            if crisil_match:
                crisil_rank = crisil_match.get("crisil_rank")
            else:
                crisil_rank = s["crisil_rank"]

            # Fallback to curated map
            ms_medalist = s["morningstar_medalist"]
            if isin in VR_CRISIL_MEDALIST_MAP:
                map_vr, map_cr, map_med = VR_CRISIL_MEDALIST_MAP[isin]
                if vr_rating is None:
                    vr_rating = map_vr
                if not crisil_rank:
                    crisil_rank = map_cr
                if not ms_medalist:
                    ms_medalist = map_med

            ms_star = s["morningstar_rating"]
            if ms_star is None and vr_rating:
                ms_star = vr_rating

            payload = {
                "scheme_code": code,
                "category": cat,
                "morningstar_rating": ms_star,
                "morningstar_medalist": ms_medalist,
                "valueresearch_rating": vr_rating,
                "valueresearch_risk_grade": vr_risk_grade,
                "valueresearch_avg_rating": vr_avg_rating,
                "crisil_rank": crisil_rank,
                "one_finance_score": s["one_finance_score"],
                "one_finance_rank": s["one_finance_rank"],
                "advisorkhoj_volatility_rank": adv_rank,
                "advisorkhoj_quartile": adv_q,
                "aum_cr": s["aum_cr"],
            }

            score, tier = compute_composite_rating(payload)
            payload["composite_score"] = score
            payload["rating_tier"] = tier
            cat_ratings_list.append(payload)

        # Sort category funds BEST (Rank 1) to WORST
        cat_ratings_list.sort(key=lambda x: (x["composite_score"], x.get("aum_cr") or 0.0), reverse=True)
        for rk, item in enumerate(cat_ratings_list, 1):
            item["composite_rank"] = rk
            save_fund_ratings(item["scheme_code"], cat, item)

    print(f"\n[Value Research Ingestion] Matched {matched_count}/{len(schemes)} schemes with PDF scorecard.")
    print(f"[Value Research Ingestion] Assigned 1-to-5 star ratings to {rated_count} schemes.")
    print("\nRegenerating all separate CSV sheets and Master Excel Workbook...")
    export_all_equity_data()
    print("[Success] All ratings updated and exported!")


def print_category_leaderboard(category="Flexi Cap"):
    """Prints leaderboard for a given category."""
    with get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT 
                r.composite_rank,
                r.rating_tier,
                r.composite_score,
                s.scheme_name,
                m.benchmark_name,
                m.return_3y_cagr,
                m.standard_deviation,
                m.sharpe_ratio,
                m.beta,
                m.alpha,
                m.capture_ratio,
                r.morningstar_rating,
                r.valueresearch_rating,
                r.crisil_rank,
                r.one_finance_score,
                r.aum_cr,
                r.valueresearch_risk_grade
            FROM schemes s
            JOIN fund_metrics m ON s.scheme_code = m.scheme_code
            LEFT JOIN fund_ratings r ON s.scheme_code = r.scheme_code
            WHERE s.category = ?
            ORDER BY r.composite_rank ASC NULLS LAST;
        """, (category,)).fetchall()

        if not rows:
            print(f"No data found for category '{category}'.")
            return

        bench_title = get_category_benchmark_info(category)["description"]
        print("\n" + "=" * 165)
        print(f" {category.upper()} LEADERBOARD (BENCHMARK: {bench_title}) - SORTED: BEST TO WORST")
        print("=" * 165)
        print(f"{'Rk':>2} | {'Scheme Name':<34} | {'Tier / Score':<18} | {'3Y CAGR':>7} | {'StdDev':>6} | {'Sharpe':>6} | {'Beta':>5} | {'Alpha':>6} | {'CapRat':>6} | {'Ratings (MS/VR/CR/1F)':<22} | {'AUM (₹Cr)':>10}")
        print("-" * 165)
        for r in rows[:15]:
            rk = f"{r[0]:02d}" if r[0] else "--"
            name = (r[3][:32] + "..") if len(r[3]) > 34 else r[3]
            score = f"{r[2]:.1f}/100" if r[2] is not None else "N/A"
            tier = "BEST" if "BEST" in (r[1] or "") else ("WORST" if "WORST" in (r[1] or "") else (r[1] or ""))
            tier_str = f"{tier:<5} ({score})"
            cagr = f"{r[5]:>6.2f}%" if r[5] is not None else "   N/A"
            sd = f"{r[6]:>5.2f}%" if r[6] is not None else "  N/A"
            shp = f"{r[7]:>6.2f}" if r[7] is not None else "   N/A"
            beta = f"{r[8]:>5.2f}" if r[8] is not None else "  N/A"
            alpha = f"{r[9]:>5.2f}%" if r[9] is not None else "   N/A"
            cpr = f"{r[10]:>6.2f}" if r[10] is not None else "   N/A"

            ms = f"{r[11]}★" if r[11] else "-"
            vr = f"{r[12]}★" if r[12] else "-"
            cr = r[13].replace("Rank ", "R") if r[13] else "-"
            of = f"{r[14]}" if r[14] is not None and r[14] > 0 else "-"
            rat_str = f"{ms}/{vr}/{cr}/{of}"

            aum = f"₹{r[15]:,.0f}" if r[15] else "-"
            print(f"{rk:>2} | {name:<34} | {tier_str:<18} | {cagr} | {sd} | {shp} | {beta} | {alpha} | {cpr} | {rat_str:<22} | {aum:>10}")
        print("=" * 165)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indian Equity Mutual Funds Data Pipeline")
    parser.add_argument("--sync", action="store_true", help="Run full pipeline across equity categories")
    parser.add_argument("--update-ratings", action="store_true", help="Incorporate Value Research PDF ratings and recompute rankings")
    parser.add_argument("--category", type=str, default="", help="Specific category to run or inspect")
    parser.add_argument("--report", action="store_true", help="Display leaderboard report")
    parser.add_argument("--limit-per-cat", type=int, default=0, help="Limit number of schemes per category")

    args = parser.parse_args()

    target_cats = [args.category] if args.category else DIVERSIFIED_EQUITY_CATEGORIES

    if args.sync:
        run_full_equity_pipeline(categories=target_cats, limit_per_cat=args.limit_per_cat)
        for cat in target_cats[:4]:
            print_category_leaderboard(cat)
    elif getattr(args, "update_ratings", False):
        update_ratings_from_pdf(categories=target_cats)
        for cat in target_cats[:4]:
            print_category_leaderboard(cat)
    elif args.report:
        for cat in target_cats:
            print_category_leaderboard(cat)
    else:
        parser.print_help()

