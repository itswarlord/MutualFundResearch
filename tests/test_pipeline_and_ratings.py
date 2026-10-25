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
)
from storage import get_connection, DB_PATH, MASTER_EXCEL_PATH


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
            self.assertGreaterEqual(total, 300, "Should have over 300 ratings rows in DB")

            vr_rated = cursor.execute("SELECT count(*) FROM fund_ratings WHERE valueresearch_rating IS NOT NULL").fetchone()[0]
            self.assertGreaterEqual(vr_rated, 240, "Should have at least 240 schemes with VR ratings")

            rg_rated = cursor.execute("SELECT count(*) FROM fund_ratings WHERE valueresearch_risk_grade IS NOT NULL").fetchone()[0]
            self.assertGreaterEqual(rg_rated, 240, "Should have at least 240 schemes with VR risk grades")
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


if __name__ == "__main__":
    unittest.main()

