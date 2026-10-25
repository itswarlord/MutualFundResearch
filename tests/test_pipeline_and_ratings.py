"""
test_pipeline_and_ratings.py - Comprehensive Unit & Integration Test Suite for:
1. Value Research PDF Scoreboard Parser & Extractor
2. Scheme Matching & AMC canonical resolution
3. Multi-Agency Composite Scoring & Volatility Rankings
4. SQLite Database integrity & schema columns
5. Multi-sheet Excel and CSV export integrity
6. Web dataset (funds.json) & HTTP Server endpoints
"""

import unittest
import os
import sys
import json
import sqlite3
import zipfile
import urllib.request
import urllib.error

# Add src/ and web/ to sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
WEB_DIR = os.path.join(REPO_ROOT, "web")
DATA_DIR = os.path.join(REPO_ROOT, "data")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

from ratings import (
    AMC_PATTERNS,
    extract_amc,
    clean_fund_tokens,
    get_or_load_vr_pdf_ratings,
    match_scheme_to_vr_pdf,
    compute_composite_rating,
    compute_advisorkhoj_category_volatility_rankings,
    get_or_load_crisil_rankings,
    match_scheme_to_crisil,
    fetch_crisil_rankings,
)
from storage import (
    get_connection,
    init_db,
    save_fund_ratings,
    DB_PATH,
    MASTER_EXCEL_PATH,
    generate_fund_summary_lines,
    generate_fund_summary_text,
)


class TestValueResearchPdfParser(unittest.TestCase):
    """Tests for Value Research PDF Scoreboard parser and matching logic."""

    @classmethod
    def setUpClass(cls):
        cls.pdf_funds = get_or_load_vr_pdf_ratings()

    def test_pdf_extraction_count(self):
        """Verifies that the parser extracted all funds from pages 87-111."""
        self.assertGreaterEqual(len(self.pdf_funds), 900, "Should extract at least 900 funds from Scoreboard")
        self.assertIn("name", self.pdf_funds[0])
        self.assertIn("category", self.pdf_funds[0])
        self.assertIn("rating", self.pdf_funds[0])

    def test_star_ratings_and_risk_grades(self):
        """Verifies valid distribution of stars and risk grades extracted from PDF."""
        ratings = [f.get("rating") for f in self.pdf_funds if f.get("rating") is not None]
        valid_ratings = set(ratings)
        # Ratings must be 0 (NR) or between 1 and 5
        self.assertTrue(valid_ratings.issubset({0, 1, 2, 3, 4, 5}))
        self.assertTrue(any(r == 5 for r in ratings), "Should contain 5-star funds")
        self.assertTrue(any(r == 1 for r in ratings), "Should contain 1-star funds")

        risk_grades = {f.get("risk_grade") for f in self.pdf_funds if f.get("risk_grade")}
        expected_grades = {"Low", "Below Average", "Average", "Above Average", "High"}
        self.assertTrue(risk_grades.issubset(expected_grades), f"Unexpected risk grades: {risk_grades}")

    def test_amc_extraction(self):
        """Verifies AMC canonical resolution across different naming conventions."""
        cases = [
            ("Aditya Birla Sun Life Large Cap Fund - Direct Plan", "absl"),
            ("ABSL Frontline Equity Fund", "absl"),
            ("ICICI Prudential Bluechip Fund", "icici pru"),
            ("ICICI Pru Midcap Fund", "icici pru"),
            ("HDFC Top 100 Fund", "hdfc"),
            ("Parag Parikh Flexi Cap Fund", "parag parikh"),
            ("Bandhan Large & Mid Cap Fund", "bandhan"),
            ("Nippon India Small Cap Fund", "nippon"),
            ("Canara Robeco Emerging Equities", "canara robeco"),
            ("Franklin India Flexi Cap Fund", "franklin"),
            ("Quant Multi Cap Fund", "quant"),
            ("Quantum Value Fund", "quantum"),
            ("WhiteOak Capital Mid Cap Fund", "whiteoak"),
        ]
        for name, expected in cases:
            self.assertEqual(extract_amc(name), expected, f"Failed for {name}")

    def test_clean_fund_tokens(self):
        """Verifies normalization handles suffixes, parentheses, and terms."""
        cleaned = clean_fund_tokens("HDFC Top 100 Fund - Direct Plan - Growth Option")
        self.assertNotIn("direct", cleaned)
        self.assertNotIn("growth", cleaned)
        self.assertNotIn("plan", cleaned)
        self.assertNotIn("fund", cleaned)
        self.assertIn("hdfc", cleaned)
        self.assertIn("top", cleaned)

    def test_scheme_matching_accuracy(self):
        """Verifies that schemes match their exact Value Research counterpart and avoid cross-AMC mismatch."""
        match1 = match_scheme_to_vr_pdf("Parag Parikh Flexi Cap Fund", "Flexi Cap", self.pdf_funds)
        self.assertIsNotNone(match1)
        self.assertEqual(match1.get("rating"), 5)
        self.assertEqual(match1.get("risk_grade"), "Low")

        match2 = match_scheme_to_vr_pdf("HDFC Mid Cap Fund", "Mid Cap", self.pdf_funds)
        self.assertIsNotNone(match2)
        self.assertEqual(match2.get("rating"), 5)

        # Ensure no cross-AMC match: unknown AMC should not match ABSL or HDFC
        unknown_match = match_scheme_to_vr_pdf("NonExistent AMC Super Fund", "Large Cap", self.pdf_funds)
        self.assertIsNone(unknown_match)


class TestCrisilIntelligenceRatings(unittest.TestCase):
    """Tests for CRISIL Mutual Fund Rankings (CMFR) ingestion, live fetching, and matching."""

    @classmethod
    def setUpClass(cls):
        cls.crisil_funds = get_or_load_crisil_rankings()

    def test_crisil_rankings_loaded(self):
        """Verifies that CRISIL rankings dataset contains valid scheme entries."""
        self.assertGreaterEqual(len(self.crisil_funds), 250, "Should load at least 250 CRISIL ranked funds")
        first = self.crisil_funds[0]
        self.assertIn("crisilCprRanking", first)
        self.assertIn("categoryName", first)
        self.assertIn("displayName", first)

    def test_crisil_rank_values(self):
        """Verifies that rank values are between 1 and 5."""
        ranks = {f.get("crisilCprRanking") for f in self.crisil_funds if f.get("crisilCprRanking")}
        self.assertTrue(ranks.issubset({"1", "2", "3", "4", "5"}), f"Invalid CRISIL ranks: {ranks}")

    def test_crisil_scheme_matching(self):
        """Verifies matching accuracy for prominent equity funds with CRISIL rankings."""
        match_ppfc = match_scheme_to_crisil("Parag Parikh Flexi Cap Fund", "Flexi Cap", self.crisil_funds)
        self.assertIsNotNone(match_ppfc)
        self.assertIn("Rank", match_ppfc.get("crisil_rank", ""))

        match_sbi = match_scheme_to_crisil("SBI Focused Fund", "Focused Fund", self.crisil_funds)
        self.assertIsNotNone(match_sbi)
        self.assertEqual(match_sbi.get("crisil_rank"), "Rank 1")

        # Unknown AMC should not match
        no_match = match_scheme_to_crisil("NonExistent AMC Super Fund", "Large Cap", self.crisil_funds)
        self.assertIsNone(no_match)

    def test_crisil_coverage_in_summary_data(self):
        """Verifies that the majority of active schemes in summary datasets have CRISIL ranks populated."""
        import csv
        csv_path = os.path.join(DATA_DIR, "all_equity_summary.csv")
        self.assertTrue(os.path.exists(csv_path), "all_equity_summary.csv must exist")
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        total = len(rows)
        with_crisil = sum(1 for r in rows if r.get("crisil_rank") and r.get("crisil_rank").strip())
        coverage_pct = (with_crisil / total) * 100
        self.assertGreaterEqual(coverage_pct, 75.0, f"CRISIL coverage too low: {coverage_pct:.1f}%")


class TestCompositeScoring(unittest.TestCase):
    """Tests for multi-agency composite scoring and tier calculations."""

    def test_composite_score_calculation(self):
        """Verifies weighted composite score formula."""
        # Fund with 5-star MS, 5-star VR, Rank 1 CRISIL, 80 1F, Q1 Volatility
        payload = {
            "morningstar_rating": 5,
            "morningstar_medalist": "Gold",
            "valueresearch_rating": 5,
            "crisil_rank": "Rank 1",
            "one_finance_score": 80,
            "advisorkhoj_quartile": "Q1 (Lowest Volatility)",
        }
        score, tier = compute_composite_rating(payload)
        self.assertGreaterEqual(score, 90.0)
        self.assertEqual(tier, "BEST (Tier 1 - Elite)")

    def test_composite_score_tier_thresholds(self):
        """Verifies correct tier classification."""
        self.assertEqual(compute_composite_rating({"valueresearch_rating": 5, "morningstar_rating": 5})[1], "BEST (Tier 1 - Elite)")
        self.assertEqual(compute_composite_rating({"valueresearch_rating": 1, "morningstar_rating": 1})[1], "WORST (Tier 5 - Lagging/Unproven)")

    def test_advisorkhoj_volatility_rankings(self):
        """Verifies quartile assignment based on volatility ranking."""
        sample_tuples = {
            "Flexi Cap": [(101, 10.0), (102, 12.0), (103, 14.0), (104, 18.0)]
        }
        ranks = compute_advisorkhoj_category_volatility_rankings(sample_tuples)
        self.assertEqual(ranks[101][0], 1)
        self.assertIn("Q1", ranks[101][1])
        self.assertEqual(ranks[104][0], 4)
        self.assertIn("Q4", ranks[104][1])


class TestDatabaseIntegrity(unittest.TestCase):
    """Tests SQLite database structure, schema migration, and ratings records."""

    @classmethod
    def setUpClass(cls):
        init_db(DB_PATH)

    def test_tables_and_columns_exist(self):
        """Verifies that all required tables and new VR columns exist in SQLite."""
        conn = get_connection(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {r[0] for r in cursor.fetchall()}
            self.assertTrue({"schemes", "nav_history", "fund_metrics", "fund_ratings"}.issubset(tables))

            # Check fund_ratings columns
            cursor.execute("PRAGMA table_info(fund_ratings);")
            cols = {c[1] for c in cursor.fetchall()}
            self.assertIn("valueresearch_rating", cols)
            self.assertIn("valueresearch_risk_grade", cols)
            self.assertIn("valueresearch_avg_rating", cols)
        finally:
            conn.close()

    def test_ratings_populated_in_db(self):
        """Verifies that ratings are properly populated across the schemes."""
        conn = get_connection(DB_PATH)
        try:
            cursor = conn.cursor()
            total = cursor.execute("SELECT count(*) FROM fund_ratings").fetchone()[0]
            if total > 0:
                self.assertGreaterEqual(total, 300, "Should have over 300 ratings rows in DB")
                vr_rated = cursor.execute("SELECT count(*) FROM fund_ratings WHERE valueresearch_rating IS NOT NULL").fetchone()[0]
                self.assertGreaterEqual(vr_rated, 240, "Should have at least 240 schemes with VR ratings")
                rg_rated = cursor.execute("SELECT count(*) FROM fund_ratings WHERE valueresearch_risk_grade IS NOT NULL").fetchone()[0]
                self.assertGreaterEqual(rg_rated, 240, "Should have at least 240 schemes with VR risk grades")
            else:
                # In a fresh CI checkout where DB was newly initialized, verify ratings saving & column reads
                cursor.execute("INSERT OR IGNORE INTO schemes (scheme_code, scheme_name, amc, category) VALUES (999999, 'Test Flexi Cap Fund', 'Test AMC', 'Flexi Cap')")
                conn.commit()

                test_ratings = {
                    "composite_score": 85.5,
                    "composite_rank": 1,
                    "rating_tier": "Tier 1: Top 10% (Elite)",
                    "morningstar_rating": 4,
                    "morningstar_medalist": "Gold",
                    "valueresearch_rating": 4,
                    "valueresearch_risk_grade": "Below Average",
                    "valueresearch_avg_rating": 4.2,
                    "crisil_rank": 5,
                    "one_finance_score": 8.5,
                    "one_finance_rank": 2,
                    "advisorkhoj_volatility_rank": 5,
                    "advisorkhoj_quartile": "Q1 (Lowest Volatility)",
                    "aum_cr": 12500.0,
                }
                save_fund_ratings(999999, "Flexi Cap", test_ratings, DB_PATH)
                row = cursor.execute("SELECT valueresearch_rating, valueresearch_risk_grade, valueresearch_avg_rating, composite_score FROM fund_ratings WHERE scheme_code = 999999").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 4)
                self.assertEqual(row[1], "Below Average")
                self.assertAlmostEqual(row[2], 4.2)
                self.assertAlmostEqual(row[3], 85.5)
        finally:
            conn.close()


class TestExportsAndDatasets(unittest.TestCase):
    """Tests integrity of generated CSVs, Excel workbook, and JSON web dataset."""

    def test_master_csv_exists_and_has_vr_columns(self):
        """Verifies data/all_equity_summary.csv contains required Value Research columns."""
        csv_path = os.path.join(DATA_DIR, "all_equity_summary.csv")
        self.assertTrue(os.path.exists(csv_path), "all_equity_summary.csv must exist")

        with open(csv_path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split(",")
            self.assertIn("valueresearch_rating", header)
            self.assertIn("valueresearch_risk_grade", header)
            self.assertIn("valueresearch_avg_rating", header)

    def test_category_csv_files(self):
        """Verifies each equity category has an individual summary CSV."""
        expected_categories = [
            "large_cap", "mid_cap", "small_cap", "flexi_cap", "multi_cap",
            "large_mid_cap", "elss", "focused_fund", "value_contra", "dividend_yield"
        ]
        for cat in expected_categories:
            p = os.path.join(DATA_DIR, f"{cat}_summary.csv")
            self.assertTrue(os.path.exists(p), f"Missing category CSV: {p}")
            self.assertGreater(os.path.getsize(p), 1000, f"Category CSV {p} is suspiciously small")

    def test_excel_workbook_validity(self):
        """Verifies that the multi-sheet Excel workbook is valid and contains all 11 tabs."""
        self.assertTrue(os.path.exists(MASTER_EXCEL_PATH), "Master Excel workbook must exist")
        self.assertTrue(zipfile.is_zipfile(MASTER_EXCEL_PATH), "Excel file must be a valid OpenXML zip archive")

        with zipfile.ZipFile(MASTER_EXCEL_PATH, "r") as zf:
            workbook_xml = zf.read("xl/workbook.xml").decode("utf-8")
            expected_sheets = [
                "All Equity Funds", "Large Cap", "Mid Cap", "Small Cap",
                "Flexi Cap", "Multi Cap", "Large & Mid Cap", "ELSS",
                "Focused Fund", "Value & Contra", "Dividend Yield"
            ]
            import xml.sax.saxutils
            for s in expected_sheets:
                esc_s = xml.sax.saxutils.escape(s)
                self.assertIn(esc_s, workbook_xml, f"Sheet '{s}' missing from Excel workbook")

    def test_web_dataset_json(self):
        """Verifies web/data/funds.json has valid structure, category metadata, and funds."""
        json_path = os.path.join(WEB_DIR, "data", "funds.json")
        self.assertTrue(os.path.exists(json_path), "web/data/funds.json must exist")

        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.assertIn("updated_at", payload)
        self.assertIn("categories", payload)
        self.assertIn("funds", payload)
        self.assertEqual(len(payload["categories"]), 10)
        self.assertGreaterEqual(len(payload["funds"]), 300)

        # Check VR fields in funds array
        funds_with_vr = [f for f in payload["funds"] if f.get("valueresearch_rating")]
        self.assertGreaterEqual(len(funds_with_vr), 240)


class TestWebServerEndpoints(unittest.TestCase):
    """Tests that web/server.py correctly serves assets and handles download endpoints."""

    @classmethod
    def setUpClass(cls):
        import socketserver
        import threading
        from server import MutualFundAppHandler

        # Bind to port 0 for an ephemeral available port
        cls.httpd = socketserver.TCPServer(("127.0.0.1", 0), MutualFundAppHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_index_page_served(self):
        """Verifies root URL returns index.html with 200 OK."""
        url = f"http://127.0.0.1:{self.port}/"
        with urllib.request.urlopen(url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")
            self.assertIn("Indian Equity Mutual Funds Intelligence", html)

    def test_funds_json_served(self):
        """Verifies /data/funds.json is accessible and valid."""
        url = f"http://127.0.0.1:{self.port}/data/funds.json"
        with urllib.request.urlopen(url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("funds", data)
            self.assertGreaterEqual(len(data["funds"]), 300)

    def test_excel_download_endpoint(self):
        """Verifies /download/excel returns Master XLSX with proper content type."""
        url = f"http://127.0.0.1:{self.port}/download/excel"
        with urllib.request.urlopen(url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            content_type = resp.headers.get("Content-Type", "")
            self.assertIn("openxmlformats", content_type)
            content = resp.read()
            self.assertGreater(len(content), 10000)

    def test_csv_download_endpoints(self):
        """Verifies /download/csv/master and category endpoints."""
        url_master = f"http://127.0.0.1:{self.port}/download/csv/master"
        with urllib.request.urlopen(url_master, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/csv", resp.headers.get("Content-Type", ""))

        url_flexi = f"http://127.0.0.1:{self.port}/download/csv/flexi_cap"
        with urllib.request.urlopen(url_flexi, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/csv", resp.headers.get("Content-Type", ""))


class TestWebAppUIChanges(unittest.TestCase):
    """Tests the UI changes requested: theme toggle, category dropdown, sticky header, removed items."""

    def setUp(self):
        with open(os.path.join(WEB_DIR, "index.html"), "r", encoding="utf-8") as f:
            self.html = f.read()
        with open(os.path.join(WEB_DIR, "style.css"), "r", encoding="utf-8") as f:
            self.css = f.read()
        with open(os.path.join(WEB_DIR, "app.js"), "r", encoding="utf-8") as f:
            self.js = f.read()

    def test_online_hosting_guide_removed(self):
        """Verifies that online hosting guide modal and button have been removed."""
        self.assertNotIn("btn-hosting-eval", self.html, "Online hosting button should be removed")
        self.assertNotIn("modal-hosting", self.html, "Online hosting modal should be removed")
        self.assertNotIn("modal-hosting-ack", self.js, "Modal hosting JS listener should be removed")

    def test_download_master_excel_button_removed(self):
        """Verifies that download master excel button is removed from navbar and footer."""
        self.assertNotIn("btn-download-master-excel", self.html, "Master excel navbar button should be removed")
        self.assertNotIn('download="Indian_Equity_Mutual_Funds_Master.xlsx"', self.html, "Master excel links should be removed from UI")

    def test_day_night_mode_switch_present(self):
        """Verifies day/night switch button and logic exist."""
        self.assertIn("theme-toggle-btn", self.html, "Theme toggle button must be present in HTML")
        self.assertIn("initTheme", self.js, "Theme initialization function must be present in JS")
        self.assertIn('[data-theme="light"]', self.css, "Light mode CSS rules must be present in style.css")

    def test_alternate_category_selection_dropdown(self):
        """Verifies alternate category dropdown selector exists and is wired in JS."""
        self.assertIn("category-dropdown-select", self.html, "Alternate category dropdown must exist in HTML")
        self.assertIn("category-dropdown-select", self.js, "Category dropdown must be wired in app.js")

    def test_sticky_table_header_css(self):
        """Verifies table header is sticky while scrolling down in table-responsive container."""
        self.assertIn(".table-responsive", self.css)
        self.assertIn("max-height:", self.css)
        self.assertIn(".data-table thead", self.css)
        self.assertIn("position: sticky", self.css)

    def test_all_equity_funds_option_removed(self):
        """Verifies 'All Equity Funds' option is removed both from dropdown and category selector tabs."""
        self.assertNotIn('<option value="All Equity Funds">', self.html, "'All Equity Funds' option must be removed from dropdown HTML")
        self.assertNotIn('allOpt.value = "All Equity Funds"', self.js, "'All Equity Funds' must not be added to dropdown in app.js")
        self.assertNotIn('selectCategory("All Equity Funds")', self.js, "'All Equity Funds' must not be added as a category tab in app.js")


class TestFundExecutiveSummaries(unittest.TestCase):
    """Verifies that 5-6 line quantitative executive summaries are correctly generated
    and populated for all funds across all 10 equity categories."""

    def setUp(self):
        self.funds_json_path = os.path.join(WEB_DIR, "data", "funds.json")
        with open(self.funds_json_path, "r", encoding="utf-8") as f:
            self.funds_data = json.load(f)

    def test_summary_generation_function_complete_profile(self):
        """Verifies 5-6 line summary generation with complete metrics."""
        fund = {
            "scheme_name": "Parag Parikh Flexi Cap Fund",
            "amc": "PPFAS Mutual Fund",
            "category": "Flexi Cap",
            "benchmark_name": "NIFTY 500 TRI",
            "composite_rank": 1,
            "composite_score": 92.4,
            "rating_tier": "BEST (Tier 1 - Elite)",
            "return_1y": 28.5,
            "return_3y_cagr": 21.4,
            "return_5y_cagr": 23.1,
            "return_inception_cagr": 19.8,
            "standard_deviation": 11.2,
            "beta": 0.74,
            "sharpe_ratio": 1.25,
            "sortino_ratio": 1.88,
            "alpha": 6.85,
            "upside_capture": 94.2,
            "downside_capture": 68.5,
            "capture_ratio": 1.38,
            "morningstar_rating": 5,
            "morningstar_medalist": "Gold",
            "valueresearch_rating": 5,
            "valueresearch_risk_grade": "Low",
            "crisil_rank": "Rank 1",
            "one_finance_score": 88,
            "direct_ter": 0.62,
            "regular_ter": 1.45,
            "aum_cr": 72450.0,
        }
        lines = generate_fund_summary_lines(fund)
        self.assertEqual(len(lines), 6, "Must generate exactly 6 summary lines")

        # Line 1: Mandate & Investment Strategy
        self.assertIn("Parag Parikh Flexi Cap Fund", lines[0])
        self.assertIn("PPFAS Mutual Fund", lines[0])
        self.assertIn("NIFTY 500 TRI", lines[0])

        # Line 2: Composite Ranking & Quality Tier
        self.assertIn("#1", lines[1])
        self.assertIn("92.4/100", lines[1])
        self.assertIn("BEST (Tier 1 - Elite)", lines[1])

        # Line 3: Compounding Track Record & Returns
        self.assertIn("21.40% CAGR", lines[2])
        self.assertIn("28.50%", lines[2])

        # Line 4: Risk, Volatility & Risk-Adjusted Returns
        self.assertIn("11.20%", lines[3])
        self.assertIn("0.74", lines[3])
        self.assertIn("1.25", lines[3])

        # Line 5: Alpha Generation & Market Capture Ratios
        self.assertIn("+6.85%", lines[4])
        self.assertIn("1.38", lines[4])

        # Line 6: Agency Accolades & Direct TER
        self.assertIn("Direct TER of 0.62%", lines[5])
        self.assertIn("72,450 Cr", lines[5])

        # User requirement check: No regular TER or savings in summary
        summary_text = "\n".join(lines)
        self.assertNotIn("regular_ter", summary_text.lower())
        self.assertNotIn("regular ter", summary_text.lower())
        self.assertNotIn("annual savings", summary_text.lower())
        self.assertNotIn("savings about expenses", summary_text.lower())

    def test_summary_text_generator(self):
        """Verifies generate_fund_summary_text returns newline-joined 6 lines."""
        fund = {
            "scheme_name": "Test Bluechip Fund",
            "amc": "Test AMC",
            "category": "Large Cap",
            "benchmark_name": "NIFTY 100 TRI",
            "composite_rank": 5,
            "composite_score": 75.0,
            "rating_tier": "Tier 2 - Superior",
            "direct_ter": 0.85,
            "aum_cr": 15000.0,
        }
        text = generate_fund_summary_text(fund)
        lines = text.split("\n")
        self.assertEqual(len(lines), 6)
        self.assertTrue(all(len(l.strip()) > 10 for l in lines))

    def test_all_funds_in_funds_json_have_valid_summaries(self):
        """Verifies every fund in web/data/funds.json has 5-6 lines of valid summary."""
        funds = self.funds_data["funds"]
        self.assertGreaterEqual(len(funds), 300)

        for fund in funds:
            name = fund.get("scheme_name", "Unknown")
            summary_lines = fund.get("summary_lines")
            self.assertIsNotNone(summary_lines, f"Missing summary_lines for {name}")
            self.assertIsInstance(summary_lines, list, f"summary_lines should be a list for {name}")
            self.assertIn(len(summary_lines), [5, 6], f"Summary lines should be 5-6 for {name}")

            # Each line must be substantial
            for idx, line in enumerate(summary_lines):
                self.assertGreater(len(line.strip()), 20, f"Line {idx+1} too short for {name}")

            # Combined summary
            summary = fund.get("summary")
            self.assertIsNotNone(summary, f"Missing summary for {name}")
            self.assertEqual(summary, "\n".join(summary_lines))

            # Must NOT contain regular expenses or expense savings
            self.assertNotIn("regular ter", summary.lower())
            self.assertNotIn("annual savings", summary.lower())
            self.assertNotIn("fee savings", summary.lower())

    def test_all_10_categories_have_complete_summaries(self):
        """Verifies all 10 SEBI categories are represented and 100% summarized."""
        funds = self.funds_data["funds"]
        categories = set(f["category"] for f in funds)
        expected_categories = {
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
        }
        self.assertEqual(categories, expected_categories)

        for cat in expected_categories:
            cat_funds = [f for f in funds if f["category"] == cat]
            self.assertGreaterEqual(len(cat_funds), 10, f"Category {cat} should have at least 10 funds")
            for f in cat_funds:
                self.assertEqual(len(f.get("summary_lines", [])), 6)


class TestWebUICleanupAndTER(unittest.TestCase):
    """Verifies that all CSV links and regular expenses/savings are removed from the website,
    and only Direct TER is displayed along with the fund executive summary."""

    def setUp(self):
        with open(os.path.join(WEB_DIR, "index.html"), "r", encoding="utf-8") as f:
            self.html = f.read()
        with open(os.path.join(WEB_DIR, "app.js"), "r", encoding="utf-8") as f:
            self.js = f.read()
        with open(os.path.join(WEB_DIR, "style.css"), "r", encoding="utf-8") as f:
            self.css = f.read()

    def test_no_csv_links_in_index_html(self):
        """Verifies no CSV download buttons or links remain in index.html."""
        self.assertNotIn("btn-download-cat-csv", self.html)
        self.assertNotIn(".csv", self.html)
        self.assertNotIn("download=", self.html)
        self.assertNotIn("download master csv", self.html.lower())

    def test_no_csv_download_in_app_js(self):
        """Verifies app.js does not reference CSV download buttons or CSV files."""
        self.assertNotIn("btn-download-cat-csv", self.js)
        self.assertNotIn("_summary.csv", self.js)

    def test_table_header_shows_direct_ter(self):
        """Verifies table header shows 'Direct TER' and sort option references Direct TER."""
        self.assertIn('<th class="col-ter">Direct TER</th>', self.html)
        self.assertIn("Direct TER (Lowest first)", self.html)

    def test_table_row_renders_only_direct_ter(self):
        """Verifies table rows in app.js do not render regular TER."""
        self.assertNotIn('<div class="ter-regular">', self.js)
        self.assertIn('<div class="ter-direct">${dirTer}</div>', self.js)

    def test_fund_drawer_shows_summary_and_direct_ter_only(self):
        """Verifies fund drawer displays the 5-6 line summary and only Direct TER (no savings)."""
        # Summary Card in drawer
        self.assertIn("getFundSummaryLines", self.js)
        self.assertIn("fund-summary-card", self.js)
        self.assertIn("Fund Executive Summary", self.js)
        self.assertIn("summary-line-item", self.js)
        self.assertIn("summary-line-num", self.js)
        self.assertIn("summary-line-text", self.js)

        # No regular TER or savings in drawer
        self.assertNotIn("Expense Ratio Savings", self.js)
        self.assertNotIn("Regular TER", self.js)
        self.assertNotIn("Annual Savings", self.js)
        self.assertIn("Direct Plan Expense Ratio (TER)", self.js)

    def test_fund_summary_styles_in_css(self):
        """Verifies CSS contains styling for the executive summary card and items."""
        self.assertIn(".fund-summary-card", self.css)
        self.assertIn(".summary-badge", self.css)
        self.assertIn(".fund-summary-body", self.css)
        self.assertIn(".summary-line-item", self.css)
        self.assertIn(".summary-line-num", self.css)
        self.assertIn(".summary-line-text", self.css)
        self.assertIn('[data-theme="light"] .fund-summary-card', self.css)
        self.assertIn('[data-theme="light"] .summary-line-item', self.css)


class TestCategoryBenchmarkAlignment(unittest.TestCase):
    """Verifies that all 10 equity categories have designated SEBI Tier 1 benchmarks
    consistently across backend and frontend configurations."""

    def setUp(self):
        with open(os.path.join(WEB_DIR, "app.js"), "r", encoding="utf-8") as f:
            self.js = f.read()

    def test_benchmark_details_cover_all_categories(self):
        """Verifies BENCHMARK_DETAILS dictionary in app.js maps all 10 categories."""
        categories = [
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
        for cat in categories:
            self.assertIn(f'"{cat}":', self.js)
            self.assertIn("TRI", self.js)


if __name__ == "__main__":
    unittest.main()

