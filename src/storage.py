"""
storage.py - SQLite storage engine, CSV exporter (per-category sheets), and Multi-Sheet Excel generator.
"""

import sqlite3
import csv
import json
import os
import re
import datetime
import shutil
from typing import Dict, List, Any, Optional
from excel_writer import write_xlsx

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mutual_funds.db")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MASTER_EXCEL_PATH = os.path.join(DATA_DIR, "Indian_Equity_Mutual_Funds_Master.xlsx")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Creates directory if needed and returns SQLite connection."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_PATH):
    """Initializes tables and indexes."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Schemes metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schemes (
                scheme_code INTEGER PRIMARY KEY,
                scheme_name TEXT NOT NULL,
                amc TEXT NOT NULL,
                category TEXT NOT NULL,
                isin_growth TEXT,
                isin_div TEXT,
                plan TEXT,
                option TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Daily NAV historical series table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nav_history (
                scheme_code INTEGER,
                nav_date TEXT,
                nav REAL NOT NULL,
                PRIMARY KEY (scheme_code, nav_date),
                FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code) ON DELETE CASCADE
            );
        """)

        # 3. Processed Fund Performance & Risk Metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fund_metrics (
                scheme_code INTEGER PRIMARY KEY,
                category TEXT,
                benchmark_name TEXT,
                as_of_date TEXT,
                latest_nav REAL,
                return_1m REAL,
                return_3m REAL,
                return_6m REAL,
                return_1y REAL,
                return_2y_cagr REAL,
                return_3y_cagr REAL,
                return_5y_cagr REAL,
                return_inception_cagr REAL,
                standard_deviation REAL,
                volatility_3y REAL,
                sharpe_ratio REAL,
                sharpe_3y REAL,
                sortino_ratio REAL,
                sortino_3y REAL,
                beta REAL,
                r_squared REAL,
                alpha REAL,
                upside_capture REAL,
                downside_capture REAL,
                capture_ratio REAL,
                max_drawdown_3y REAL,
                direct_ter REAL,
                regular_ter REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code) ON DELETE CASCADE
            );
        """)

        # Migration check: ensure benchmark_name exists if table pre-dated it
        cursor.execute("PRAGMA table_info(fund_metrics);")
        fm_cols = [c[1] for c in cursor.fetchall()]
        if fm_cols and "benchmark_name" not in fm_cols:
            cursor.execute("ALTER TABLE fund_metrics ADD COLUMN benchmark_name TEXT;")

        # 4. Multi-Agency Ratings and Rankings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fund_ratings (
                scheme_code INTEGER PRIMARY KEY,
                category TEXT,
                composite_score REAL,
                composite_rank INTEGER,
                rating_tier TEXT,
                morningstar_rating INTEGER,
                morningstar_medalist TEXT,
                valueresearch_rating INTEGER,
                valueresearch_risk_grade TEXT,
                valueresearch_avg_rating REAL,
                crisil_rank TEXT,
                one_finance_score INTEGER,
                one_finance_rank TEXT,
                advisorkhoj_volatility_rank INTEGER,
                advisorkhoj_quartile TEXT,
                aum_cr REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scheme_code) REFERENCES schemes(scheme_code) ON DELETE CASCADE
            );
        """)

        # Migration check: ensure valueresearch columns exist in fund_ratings
        cursor.execute("PRAGMA table_info(fund_ratings);")
        fr_cols = [c[1] for c in cursor.fetchall()]
        if fr_cols:
            if "valueresearch_risk_grade" not in fr_cols:
                cursor.execute("ALTER TABLE fund_ratings ADD COLUMN valueresearch_risk_grade TEXT;")
            if "valueresearch_avg_rating" not in fr_cols:
                cursor.execute("ALTER TABLE fund_ratings ADD COLUMN valueresearch_avg_rating REAL;")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nav_history_date ON nav_history(nav_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_amc ON schemes(amc);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_cat ON schemes(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_isin ON schemes(isin_growth);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_composite ON fund_ratings(composite_score);")
        conn.commit()


def save_scheme_meta(scheme: Dict, db_path: str = DB_PATH):
    """Inserts or updates scheme metadata."""
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO schemes (scheme_code, scheme_name, amc, category, isin_growth, isin_div, plan, option, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(scheme_code) DO UPDATE SET
                scheme_name = excluded.scheme_name,
                amc = excluded.amc,
                category = excluded.category,
                isin_growth = excluded.isin_growth,
                isin_div = excluded.isin_div,
                plan = excluded.plan,
                option = excluded.option,
                updated_at = CURRENT_TIMESTAMP;
        """, (
            scheme["scheme_code"],
            scheme["scheme_name"],
            scheme["amc"],
            scheme.get("category", "Equity Scheme"),
            scheme.get("isin_growth"),
            scheme.get("isin_div"),
            scheme.get("plan"),
            scheme.get("option"),
        ))
        conn.commit()


def save_nav_history(scheme_code: int, nav_history: List[Dict], db_path: str = DB_PATH):
    """Batch inserts NAV history."""
    if not nav_history:
        return

    records = []
    for item in nav_history:
        d = item.get("date")
        n = item.get("nav")
        if d and n:
            try:
                parts = d.split("-")
                if len(parts) == 3 and len(parts[0]) == 2:
                    d_iso = f"{parts[2]}-{parts[1]}-{parts[0]}"
                else:
                    d_iso = d
                records.append((scheme_code, d_iso, float(n)))
            except (ValueError, TypeError):
                continue

    with get_connection(db_path) as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO nav_history (scheme_code, nav_date, nav)
            VALUES (?, ?, ?);
        """, records)
        conn.commit()


def save_fund_metrics(scheme_code: int, category: str, metrics: Dict[str, Any], ter_info: Dict[str, Any], db_path: str = DB_PATH):
    """Saves computed returns, ratios, beta, alpha, and capture ratios."""
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO fund_metrics (
                scheme_code, category, benchmark_name, as_of_date, latest_nav,
                return_1m, return_3m, return_6m, return_1y,
                return_2y_cagr, return_3y_cagr, return_5y_cagr,
                return_inception_cagr, standard_deviation, volatility_3y,
                sharpe_ratio, sharpe_3y, sortino_ratio, sortino_3y,
                beta, r_squared, alpha, upside_capture, downside_capture, capture_ratio,
                max_drawdown_3y, direct_ter, regular_ter, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(scheme_code) DO UPDATE SET
                category = excluded.category,
                benchmark_name = excluded.benchmark_name,
                as_of_date = excluded.as_of_date,
                latest_nav = excluded.latest_nav,
                return_1m = excluded.return_1m,
                return_3m = excluded.return_3m,
                return_6m = excluded.return_6m,
                return_1y = excluded.return_1y,
                return_2y_cagr = excluded.return_2y_cagr,
                return_3y_cagr = excluded.return_3y_cagr,
                return_5y_cagr = excluded.return_5y_cagr,
                return_inception_cagr = excluded.return_inception_cagr,
                standard_deviation = excluded.standard_deviation,
                volatility_3y = excluded.volatility_3y,
                sharpe_ratio = excluded.sharpe_ratio,
                sharpe_3y = excluded.sharpe_3y,
                sortino_ratio = excluded.sortino_ratio,
                sortino_3y = excluded.sortino_3y,
                beta = excluded.beta,
                r_squared = excluded.r_squared,
                alpha = excluded.alpha,
                upside_capture = excluded.upside_capture,
                downside_capture = excluded.downside_capture,
                capture_ratio = excluded.capture_ratio,
                max_drawdown_3y = excluded.max_drawdown_3y,
                direct_ter = excluded.direct_ter,
                regular_ter = excluded.regular_ter,
                updated_at = CURRENT_TIMESTAMP;
        """, (
            scheme_code,
            category,
            metrics.get("benchmark_name"),
            metrics.get("as_of_date"),
            metrics.get("latest_nav"),
            metrics.get("return_1m"),
            metrics.get("return_3m"),
            metrics.get("return_6m"),
            metrics.get("return_1y"),
            metrics.get("return_2y_cagr"),
            metrics.get("return_3y_cagr"),
            metrics.get("return_5y_cagr"),
            metrics.get("return_inception_cagr"),
            metrics.get("standard_deviation") or metrics.get("volatility_3y"),
            metrics.get("volatility_3y"),
            metrics.get("sharpe_ratio") or metrics.get("sharpe_3y"),
            metrics.get("sharpe_3y"),
            metrics.get("sortino_ratio") or metrics.get("sortino_3y"),
            metrics.get("sortino_3y"),
            metrics.get("beta"),
            metrics.get("r_squared"),
            metrics.get("alpha"),
            metrics.get("upside_capture"),
            metrics.get("downside_capture"),
            metrics.get("capture_ratio"),
            metrics.get("max_drawdown_3y"),
            ter_info.get("direct_ter"),
            ter_info.get("regular_ter"),
        ))
        conn.commit()


def save_fund_ratings(scheme_code: int, category: str, ratings: Dict[str, Any], db_path: str = DB_PATH):
    """Saves multi-agency rating indicators and composite rank."""
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO fund_ratings (
                scheme_code,
                category,
                composite_score,
                composite_rank,
                rating_tier,
                morningstar_rating,
                morningstar_medalist,
                valueresearch_rating,
                valueresearch_risk_grade,
                valueresearch_avg_rating,
                crisil_rank,
                one_finance_score,
                one_finance_rank,
                advisorkhoj_volatility_rank,
                advisorkhoj_quartile,
                aum_cr,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(scheme_code) DO UPDATE SET
                category = excluded.category,
                composite_score = excluded.composite_score,
                composite_rank = excluded.composite_rank,
                rating_tier = excluded.rating_tier,
                morningstar_rating = excluded.morningstar_rating,
                morningstar_medalist = excluded.morningstar_medalist,
                valueresearch_rating = excluded.valueresearch_rating,
                valueresearch_risk_grade = excluded.valueresearch_risk_grade,
                valueresearch_avg_rating = excluded.valueresearch_avg_rating,
                crisil_rank = excluded.crisil_rank,
                one_finance_score = excluded.one_finance_score,
                one_finance_rank = excluded.one_finance_rank,
                advisorkhoj_volatility_rank = excluded.advisorkhoj_volatility_rank,
                advisorkhoj_quartile = excluded.advisorkhoj_quartile,
                aum_cr = excluded.aum_cr,
                updated_at = CURRENT_TIMESTAMP;
        """, (
            scheme_code,
            category,
            ratings.get("composite_score"),
            ratings.get("composite_rank"),
            ratings.get("rating_tier"),
            ratings.get("morningstar_rating"),
            ratings.get("morningstar_medalist"),
            ratings.get("valueresearch_rating"),
            ratings.get("valueresearch_risk_grade"),
            ratings.get("valueresearch_avg_rating"),
            ratings.get("crisil_rank"),
            ratings.get("one_finance_score"),
            ratings.get("one_finance_rank"),
            ratings.get("advisorkhoj_volatility_rank"),
            ratings.get("advisorkhoj_quartile"),
            ratings.get("aum_cr"),
        ))
        conn.commit()


def generate_fund_summary_lines(f: Dict[str, Any]) -> List[str]:
    """
    Generates a concise 5-6 line institutional quantitative narrative summarizing
    a mutual fund's investment mandate, composite tier ranking, multi-year compounding,
    risk/CAPM characteristics, alpha/capture ratios, and agency ratings consensus.
    """
    name = f.get("scheme_name", "This fund")
    amc = f.get("amc", "AMC")
    cat = f.get("category", "Equity")
    bench = f.get("benchmark_name") or "Nifty 500 TRI"
    rank = f.get("composite_rank", "-")
    score = f.get("composite_score", 0)
    tier = f.get("rating_tier", "Tier 3 - Average")

    cat_stances = {
        "Large Cap": "investing primarily in top-100 blue-chip market leaders with proven balance sheet stability",
        "Mid Cap": "targeting high-growth emerging leaders positioned in the 101st-250th market capitalization segment",
        "Small Cap": "seeking rapid capital appreciation through high-potential companies ranked 251st and beyond",
        "Flexi Cap": "executing a flexible multi-cap equity mandate dynamically distributed across large, mid, and small cap equities",
        "Multi Cap": "maintaining a disciplined minimum 25% mandatory allocation across large, mid, and small cap market tiers",
        "Large & Mid Cap": "balancing established large-cap resilience with high-growth mid-cap opportunities across the top 250 universe",
        "ELSS": "combining long-term equity wealth generation with tax savings under Section 80C through a 3-year statutory lock-in",
        "Focused Fund": "concentrating high-conviction capital into a curated portfolio of up to 30 carefully chosen stocks",
        "Value & Contra": "pursuing deep-value and contrarian opportunities trading at attractive valuations relative to intrinsic potential",
        "Dividend Yield": "anchoring capital in cash-generative businesses offering robust dividend yields and defensive capital preservation"
    }
    stance = cat_stances.get(cat, "providing focused exposure to diversified Indian equities")

    # Line 1: Mandate & Investment Strategy
    line1 = f"{name} is an open-ended {cat} mutual fund offered by {amc}, benchmarked against the {bench} and {stance}."

    # Line 2: Composite Ranking & Quality Tier
    line2 = f"Under our multi-agency quantitative framework, the fund ranks #{rank} in the {cat} peer category with a composite score of {score}/100, placing it in {tier}."

    # Line 3: Compounding Track Record & Returns
    r3y = f"{f.get('return_3y_cagr', 0):.2f}% CAGR" if f.get("return_3y_cagr") is not None else None
    r1y = f"{f.get('return_1y', 0):.2f}%" if f.get("return_1y") is not None else None
    r5y = f"{f.get('return_5y_cagr', 0):.2f}% CAGR" if f.get("return_5y_cagr") is not None else None
    r_inc = f"{f.get('return_inception_cagr', 0):.2f}% CAGR" if f.get("return_inception_cagr") is not None else None

    if r3y:
        perf_bits = [f"3-year return of {r3y}"]
        if r1y:
            perf_bits.append(f"1-year return of {r1y}")
        if r5y:
            perf_bits.append(f"5-year CAGR of {r5y}")
        if r_inc:
            perf_bits.append(f"since inception: {r_inc}")
        line3 = f"In terms of historical wealth compounding, the scheme has delivered a {', '.join(perf_bits)}."
    elif r1y:
        line3 = f"The scheme has delivered a 1-year trailing return of {r1y} (since inception: {r_inc or 'N/A'}), while longer 3-year rolling horizons are steadily maturing."
    else:
        line3 = "As a relatively newly launched or seasoned scheme, full multi-year rolling CAGR track records are maturing over ongoing market cycles."

    # Line 4: Risk, Volatility & Risk-Adjusted Returns
    vol = f"{f.get('standard_deviation', 0):.2f}%" if f.get("standard_deviation") is not None else None
    beta = f"{f.get('beta', 0):.2f}" if f.get("beta") is not None else None
    sharpe = f"{f.get('sharpe_ratio', 0):.2f}" if f.get("sharpe_ratio") is not None else None
    sortino = f"{f.get('sortino_ratio', 0):.2f}" if f.get("sortino_ratio") is not None else None

    if vol and beta:
        line4 = f"From a risk perspective, it displays an annualized volatility of {vol} and a market Beta of {beta}, resulting in a Sharpe Ratio of {sharpe or 'N/A'} and Sortino Ratio of {sortino or 'N/A'}."
    elif vol:
        line4 = f"From a risk perspective, the fund demonstrates an annualized volatility of {vol}, with full CAPM market sensitivity metrics establishing over time."
    else:
        line4 = "Statistical risk parameters and annualized volatility are calibrating as the fund builds its historical trading series against the category benchmark."

    # Line 5: Alpha Generation & Market Capture Ratios
    alpha = f"{f.get('alpha', 0):+.2f}%" if f.get("alpha") is not None else None
    up = f"{round(f.get('upside_capture', 0))}%" if f.get("upside_capture") is not None else None
    dn = f"{round(f.get('downside_capture', 0))}%" if f.get("downside_capture") is not None else None
    cap = f"{f.get('capture_ratio', 0):.2f}" if f.get("capture_ratio") is not None else None

    if alpha and up and dn:
        line5 = f"Relative to its benchmark, the fund generates a Jensen's Alpha of {alpha}, accompanied by an upside capture of {up} and downside capture of {dn} (overall capture ratio: {cap or 'N/A'})."
    elif alpha:
        line5 = f"Relative to its designated benchmark, the fund reflects a Jensen's Alpha of {alpha}, highlighting its active portfolio selection capability."
    else:
        line5 = "Active benchmark alpha and dual-market capture ratios (upside/downside) will compute once mandatory 36-month daily return histories conclude."

    # Line 6: Agency Accolades & Expense Efficiency
    ms = f"{f.get('morningstar_rating')}★" if f.get("morningstar_rating") else "Unrated"
    if f.get("morningstar_medalist"):
        ms += f" ({f.get('morningstar_medalist')})"
    vr = f"{f.get('valueresearch_rating')}★" if f.get("valueresearch_rating") else "Unrated"
    if f.get("valueresearch_risk_grade"):
        vr += f" [{f.get('valueresearch_risk_grade')} Risk]"
    cr = f.get("crisil_rank") or "Unranked"
    of = f"{f.get('one_finance_score')}/100" if f.get("one_finance_score") else "N/A"
    ter = f"{f.get('direct_ter', 0):.2f}%" if f.get("direct_ter") is not None else "N/A"
    aum = f"₹{round(f.get('aum_cr', 0)):,} Cr" if f.get("aum_cr") else "N/A"

    line6 = f"Across independent rating agencies, it is assigned {ms} from Morningstar, {vr} from Value Research, {cr} from CRISIL, and a {of} score from 1 Finance, managing {aum} in AUM with a Direct TER of {ter}."

    return [line1, line2, line3, line4, line5, line6]


def generate_fund_summary_text(f: Dict[str, Any]) -> str:
    """Returns the 5-6 line summary as a newline-delimited text block."""
    return "\n".join(generate_fund_summary_lines(f))


def export_all_equity_data(db_path: str = DB_PATH):
    """
    Exports:
    1. Separate CSV files for each equity category in data/ (e.g. data/large_cap_summary.csv).
    2. A master CSV with all equity funds (data/all_equity_summary.csv).
    3. A single multi-sheet Excel file (data/Indian_Equity_Mutual_Funds_Master.xlsx)
       with dedicated tabs for each category, sorted from BEST to WORST.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    with get_connection(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query all records
        rows = cursor.execute("""
            SELECT 
                s.category,
                r.composite_rank,
                r.rating_tier,
                r.composite_score,
                s.scheme_code,
                s.scheme_name,
                s.amc,
                m.benchmark_name,
                s.plan,
                s.isin_growth,
                m.as_of_date,
                m.latest_nav,
                m.return_1m,
                m.return_3m,
                m.return_6m,
                m.return_1y,
                m.return_2y_cagr,
                m.return_3y_cagr,
                m.return_5y_cagr,
                m.return_inception_cagr,
                m.standard_deviation,
                m.beta,
                m.r_squared,
                m.alpha,
                m.sharpe_ratio,
                m.sortino_ratio,
                m.upside_capture,
                m.downside_capture,
                m.capture_ratio,
                m.max_drawdown_3y,
                m.direct_ter,
                m.regular_ter,
                r.morningstar_rating,
                r.morningstar_medalist,
                r.valueresearch_rating,
                r.valueresearch_risk_grade,
                r.valueresearch_avg_rating,
                r.crisil_rank,
                r.one_finance_score,
                r.one_finance_rank,
                r.advisorkhoj_volatility_rank,
                r.advisorkhoj_quartile,
                r.aum_cr
            FROM schemes s
            LEFT JOIN fund_metrics m ON s.scheme_code = m.scheme_code
            LEFT JOIN fund_ratings r ON s.scheme_code = r.scheme_code
            ORDER BY s.category ASC, r.composite_score DESC NULLS LAST, m.return_3y_cagr DESC NULLS LAST;
        """).fetchall()

        all_data = [dict(r) for r in rows]
        if not all_data:
            print("[Export] No data found in database to export.")
            return

        columns = list(all_data[0].keys())

        # 1. Master CSV
        master_csv_path = os.path.join(DATA_DIR, "all_equity_summary.csv")
        with open(master_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(all_data)

        # 2. Group by Category and export separate CSVs
        cat_map: Dict[str, List[Dict]] = {}
        for row in all_data:
            cat = row.get("category") or "Other"
            cat_map.setdefault(cat, []).append(row)

        PREFERRED_CAT_ORDER = [
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
        sorted_cats = [c for c in PREFERRED_CAT_ORDER if c in cat_map] + [c for c in cat_map if c not in PREFERRED_CAT_ORDER]

        excel_sheets: Dict[str, List[List[Any]]] = {}

        # Add Master Sheet to Excel first
        excel_sheets["All Equity Funds"] = [columns] + [[row[c] for c in columns] for row in all_data]

        for cat in sorted_cats:
            items = cat_map[cat]
            # Generate clean filename
            slug = re.sub(r"[^a-z0-9]+", "_", cat.lower()).strip("_")
            cat_csv_path = os.path.join(DATA_DIR, f"{slug}_summary.csv")

            with open(cat_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(items)

            # Add to Excel sheets
            excel_sheets[cat] = [columns] + [[row[c] for c in columns] for row in items]

        # 3. Create Multi-Sheet Excel Workbook
        write_xlsx(MASTER_EXCEL_PATH, excel_sheets)

        # 4. Generate web/data/funds.json for Web Application
        web_data_dir = os.path.join(os.path.dirname(DATA_DIR), "web", "data")
        os.makedirs(web_data_dir, exist_ok=True)
        web_json_path = os.path.join(web_data_dir, "funds.json")

        from analytics import CATEGORY_BENCHMARKS, DEFAULT_BENCHMARK
        cat_metadata = []
        total_aum = 0.0
        for c in PREFERRED_CAT_ORDER:
            c_funds = [f for f in all_data if f.get("category") == c]
            if not c_funds:
                continue
            c_aum = sum((f.get("aum_cr") or 0.0) for f in c_funds)
            total_aum += c_aum
            b_info = CATEGORY_BENCHMARKS.get(c, DEFAULT_BENCHMARK)
            cat_metadata.append({
                "name": c,
                "count": len(c_funds),
                "aum_cr": round(c_aum, 1),
                "benchmark": b_info["description"],
                "benchmark_proxy": b_info["name"]
            })

        # Attach 5-6 line dynamic AI summary to each mutual fund for detail modal
        try:
            from ai_summarizer import batch_generate_ai_summaries
            batch_generate_ai_summaries(all_data)
        except Exception:
            for f in all_data:
                s_lines = generate_fund_summary_lines(f)
                f["summary_lines"] = s_lines
                f["summary"] = "\n".join(s_lines)
                f["summary_source"] = "quantitative-fallback"

        web_payload = {
            "updated_at": datetime.date.today().isoformat(),
            "total_funds": len(all_data),
            "total_categories": len(cat_metadata),
            "total_aum_cr": round(total_aum, 1),
            "categories": cat_metadata,
            "funds": all_data
        }

        with open(web_json_path, "w", encoding="utf-8") as f:
            json.dump(web_payload, f, indent=2)

        # Copy Excel and CSV files to web/data/ for zero-config static hosting (GitHub Pages / Cloudflare)
        shutil.copy2(MASTER_EXCEL_PATH, os.path.join(web_data_dir, "Indian_Equity_Mutual_Funds_Master.xlsx"))
        shutil.copy2(master_csv_path, os.path.join(web_data_dir, "all_equity_summary.csv"))
        for cat in cat_map.keys():
            slug = re.sub(r"[^a-z0-9]+", "_", cat.lower()).strip("_")
            src_csv = os.path.join(DATA_DIR, f"{slug}_summary.csv")
            if os.path.exists(src_csv):
                shutil.copy2(src_csv, os.path.join(web_data_dir, f"{slug}_summary.csv"))

        print(f"[Export] Successfully generated:")
        print(f"  - Master Excel: {MASTER_EXCEL_PATH} ({len(excel_sheets)} tabs)")
        print(f"  - Master CSV  : {master_csv_path} ({len(all_data)} funds)")
        print(f"  - Web Dataset : {web_json_path} ({len(all_data)} funds, ₹{total_aum:,.0f} Cr AUM)")
        for cat in cat_map.keys():
            slug = re.sub(r"[^a-z0-9]+", "_", cat.lower()).strip("_")
            print(f"  - Category CSV: data/{slug}_summary.csv ({len(cat_map[cat])} funds)")
