# Indian Equity Mutual Funds Research Repository 🇮🇳

An automated, data pipeline and quantitative research repository tracking all SEBI-registered **Equity Mutual Funds** in India across **all major equity categories**.

This project automatically fetches official daily NAVs from AMFI, Total Expense Ratios (TER), historical NAV time-series from MFAPI, computes rolling returns (1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y CAGR), calculates risk and CAPM benchmark metrics (**Standard Deviation, Sharpe Ratio, Sortino Ratio, Beta, R-Squared, Jensen's Alpha, Upside Capture Ratio, Downside Capture Ratio, Overall Capture Ratio** against the Nifty 500 benchmark), ingests **multi-agency ratings (Morningstar, Value Research, CRISIL, 1 Finance, Advisorkhoj)**, and ranks schemes from **"BEST" (top) to "WORST" (bottom)**.

---

## 📁 Generated Datasets & Files

All data files are stored in the [data/](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data) directory:

### 1. Master Multi-Sheet Excel Workbook
* **[Indian_Equity_Mutual_Funds_Master.xlsx](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/Indian_Equity_Mutual_Funds_Master.xlsx)**: A single comprehensive OpenXML Excel workbook containing 11 sheets/tabs:
  1. `All Equity Funds` (Master Sheet of all categories)
  2. `Large Cap`
  3. `Mid Cap`
  4. `Small Cap`
  5. `Flexi Cap`
  6. `Multi Cap`
  7. `Large & Mid Cap`
  8. `ELSS` (Tax Saver)
  9. `Focused Fund`
  10. `Value & Contra`
  11. `Dividend Yield`

### 2. Category-Specific CSV Sheets
Each category is also exported as an individual, clean CSV file, sorted with **"BEST" (Rank 1)** at the top:
* **[all_equity_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/all_equity_summary.csv)** (Complete Master CSV)
* **[large_cap_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/large_cap_summary.csv)** (34 Large Cap Funds)
* **[mid_cap_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/mid_cap_summary.csv)** (33 Mid Cap Funds)
* **[small_cap_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/small_cap_summary.csv)** (36 Small Cap Funds)
* **[flexi_cap_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/flexi_cap_summary.csv)** (46 Flexi Cap Funds)
* **[multi_cap_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/multi_cap_summary.csv)** (32 Multi Cap Funds)
* **[large_mid_cap_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/large_mid_cap_summary.csv)** (36 Large & Mid Cap Funds)
* **[elss_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/elss_summary.csv)** (38 ELSS Tax Saver Funds)
* **[focused_fund_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/focused_fund_summary.csv)** (28 Focused Funds)
* **[value_contra_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/value_contra_summary.csv)** (28 Value & Contra Funds)
* **[dividend_yield_summary.csv](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/dividend_yield_summary.csv)** (12 Dividend Yield Funds)

### 3. Relational Database
* **[mutual_funds.db](file:///home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/data/mutual_funds.db)**: SQLite database containing indexed scheme metadata, processed metrics, ratings, and daily historical NAV series.

---

## 🏆 Category Leaderboard Snapshots (BEST to WORST)
*Synthesized using multi-agency ratings including official **Value Research Scoreboard (Pages 85–111 in reference PDF)**, **CRISIL Mutual Fund Rankings (CMFR)** live from CRISIL Research Intelligence (`intelligence.crisil.com`), Morningstar, 1 Finance, and Advisorkhoj.*

### 1. Flexi Cap Funds (Top 5)
| Rank | Scheme Name | Tier & Score | 3Y CAGR | Std Dev | Sharpe | Beta | Alpha | Capture Ratio | VR Rating | Live AUM (₹ Cr) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | **Parag Parikh Flexi Cap Fund** | **BEST (97.5/100)** | 12.29% | **9.90%** | 0.53 | **0.61** | **+4.26%** | **1.44** | **5★ (Low Risk)** | **₹145,070 Cr** |
| **02** | **HDFC Flexi Cap Fund** | **BEST (96.0/100)** | 14.39% | 12.12% | **0.61** | 0.80 | **+5.96%** | **1.32** | **5★ (Low Risk)** | **₹108,547 Cr** |
| **03** | **WhiteOak Capital Flexi Cap Fund** | **BEST (75.7/100)** | 13.14% | 13.83% | 0.44 | 0.94 | **+4.26%** | **1.18** | **4★ (-Avg Risk)** | ₹9,325 Cr |
| **04** | **Mahindra Manulife Flexi Cap Fund**| **BEST (75.1/100)** | 8.43% | 13.69% | 0.10 | 0.93 | -0.45% | 0.97 | **4★ (-Avg Risk)** | ₹1,510 Cr |
| **05** | **Invesco India Flexi Cap Fund** | **Tier 2 (74.9/100)** | **15.41%** | 15.69% | 0.54 | 1.03 | **+6.39%** | **1.27** | **5★ (Avg Risk)** | ₹5,437 Cr |

### 2. Large Cap Funds (Top 5)
| Rank | Scheme Name | Tier & Score | 3Y CAGR | Std Dev | Sharpe | Beta | Alpha | Capture Ratio | VR Rating | Live AUM (₹ Cr) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | **ICICI Prudential Large Cap (Bluechip)** | **BEST (94.2/100)** | 9.57% | 12.73% | 0.20 | 0.91 | **+1.86%** | **1.03** | **5★ (Low Risk)** | **₹76,352 Cr** |
| **02** | **DSP Large Cap Fund** | **BEST (92.9/100)** | 10.04% | 12.36% | 0.25 | 0.86 | **+2.34%** | **1.08** | **5★ (Low Risk)** | ₹6,642 Cr |
| **03** | **Nippon India Large Cap Fund** | **BEST (83.9/100)** | 10.08% | 13.29% | 0.23 | 0.97 | **+2.28%** | **1.07** | **5★ (Low Risk)** | **₹51,296 Cr** |
| **04** | **SBI Large Cap Fund** | **BEST (82.8/100)** | 8.02% | 12.63% | 0.08 | 0.90 | +0.31% | 0.97 | **4★ (-Avg Risk)** | **₹52,373 Cr** |
| **05** | **HDFC Large Cap Fund** | **BEST (82.2/100)** | 7.54% | 12.44% | 0.04 | 0.97 | -0.21% | 0.96 | **5★ (Low Risk)** | **₹37,294 Cr** |

### 3. Mid Cap Funds (Top 5)
| Rank | Scheme Name | Tier & Score | 3Y CAGR | Std Dev | Sharpe | Beta | Alpha | Capture Ratio | VR Rating | Live AUM (₹ Cr) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | **HDFC Mid Cap Fund** | **BEST (93.1/100)** | 15.27% | 13.56% | 0.61 | 0.84 | **+3.50%** | **1.11** | **5★ (Low Risk)** | **₹101,856 Cr** |
| **02** | **WhiteOak Capital Mid Cap Fund** | **BEST (85.6/100)** | **19.17%** | 14.54% | 0.84 | 0.90 | **+7.13%** | **1.24** | **5★ (Low Risk)** | ₹7,540 Cr |
| **03** | **Nippon India Growth Mid Cap Fund**| **BEST (82.0/100)** | 15.64% | 14.63% | 0.59 | 0.95 | **+3.17%** | **1.10** | **5★ (-Avg Risk)** | **₹50,176 Cr** |
| **04** | **Edelweiss Mid Cap Fund** | **BEST (82.0/100)** | 18.18% | 14.77% | 0.76 | 0.95 | **+5.82%** | **1.21** | **5★ (-Avg Risk)** | ₹19,230 Cr |
| **05** | **Baroda BNP Paribas Mid Cap Fund** | **BEST (80.6/100)** | 14.22% | 13.92% | 0.52 | 0.86 | **+2.25%** | **1.05** | **4★ (Low Risk)** | ₹2,503 Cr |

### 4. Small Cap Funds (Top 5)
| Rank | Scheme Name | Tier & Score | 3Y CAGR | Std Dev | Sharpe | Beta | Alpha | Capture Ratio | VR Rating | Live AUM (₹ Cr) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | **BANDHAN Small Cap Fund** | **BEST (83.9/100)** | **22.10%** | 17.43% | 0.87 | 0.89 | **+11.41%**| **1.39** | **5★ (Avg Risk)** | **₹35,856 Cr** |
| **02** | **Invesco India Small Cap Fund** | **BEST (82.4/100)** | 19.45% | 17.99% | 0.69 | 0.90 | **+8.72%** | **1.27** | **5★ (-Avg Risk)** | ₹16,131 Cr |
| **03** | **Axis Small Cap Fund** | **BEST (82.1/100)** | 12.90% | 15.05% | 0.39 | 0.76 | **+2.72%** | **1.03** | **4★ (Low Risk)** | **₹30,678 Cr** |
| **04** | **Nippon India Small Cap Fund** | **BEST (77.2/100)** | 12.62% | 16.60% | 0.34 | 0.85 | **+2.06%** | **1.02** | **4★ (-Avg Risk)** | **₹80,906 Cr** |
| **05** | **Edelweiss Small Cap Fund** | **BEST (76.8/100)** | 12.77% | 16.38% | 0.35 | 0.82 | **+2.27%** | **1.03** | **4★ (Low Risk)** | ₹7,000 Cr |

---

## 🎯 Category-Specific Benchmarks (SEBI Mandated Tier 1)

In compliance with SEBI's circular on *Benchmarking of Scheme's Performance* (SEBI/HO/IMD/DF3/CIR/P/2021/652), every mutual fund category is benchmarked against its designated Tier 1 index rather than a generic index:

| Mutual Fund Category | SEBI Mandated Benchmark | Proxy Index Fund on AMFI / MFAPI | Scheme Code | History Window |
| :--- | :--- | :--- | :---: | :---: |
| **Large Cap** | **NIFTY 100 TRI** | Axis Nifty 100 Index Fund (Direct Growth) | `147666` | 1,736 daily NAVs (2019-2026) |
| **Mid Cap** | **NIFTY Midcap 150 TRI** | Motilal Oswal Nifty Midcap 150 Index Fund (Direct Growth) | `147622` | 1,755 daily NAVs (2019-2026) |
| **Small Cap** | **NIFTY Smallcap 250 TRI** | Motilal Oswal Nifty Smallcap 250 Index Fund (Direct Growth) | `147623` | 1,755 daily NAVs (2019-2026) |
| **Flexi Cap** | **NIFTY 500 TRI** | Motilal Oswal Nifty 500 Index Fund (Direct Growth) | `147625` | 1,755 daily NAVs (2019-2026) |
| **Multi Cap** | **NIFTY 500 Multicap 50:25:25 TRI** | Navi Nifty 500 Multicap 50:25:25 Index Fund (Direct Growth) | `152751` | 550 daily NAVs (fallback: Nifty 500) |
| **Large & Mid Cap** | **NIFTY LargeMidcap 250 TRI** | Edelweiss NIFTY Large Midcap 250 Index Fund (Direct Growth) | `149343` | 1,206 daily NAVs (2021-2026) |
| **ELSS (Tax Saver)** | **NIFTY 500 TRI** | Motilal Oswal Nifty 500 Index Fund (Direct Growth) | `147625` | 1,755 daily NAVs (2019-2026) |
| **Focused Fund** | **NIFTY 500 TRI** | Motilal Oswal Nifty 500 Index Fund (Direct Growth) | `147625` | 1,755 daily NAVs (2019-2026) |
| **Value & Contra** | **NIFTY 500 TRI** | Motilal Oswal Nifty 500 Index Fund (Direct Growth) | `147625` | 1,755 daily NAVs (2019-2026) |
| **Dividend Yield** | **NIFTY 500 TRI** | Motilal Oswal Nifty 500 Index Fund (Direct Growth) | `147625` | 1,755 daily NAVs (2019-2026) |

---

## 📐 Quantitative Formulas & CAPM Analytics

All CAPM sensitivity metrics and capture ratios are evaluated **against each category's specific benchmark** ($R_b$):

1. **Beta ($\beta$)**: Sensitivity of fund daily returns relative to its category benchmark:
   $$\beta = \frac{\text{Covariance}(R_f, R_b)}{\text{Variance}(R_b)}$$
2. **R-Squared ($R^2$)**: Percentage of fund variance explained by the category benchmark:
   $$R^2 = \text{Correlation}(R_f, R_b)^2$$
3. **Jensen's Alpha ($\alpha$)**: Annualized excess return generated over CAPM expectations ($R_f = 7.0\%$):
   $$\alpha = \text{CAGR}_f - [R_f + \beta \times (\text{CAGR}_b - R_f)]$$
4. **Capture Ratios (Monthly Morningstar Method)**:
   - **Upside Capture Ratio (%)**: Annualized return of the fund during months when the category benchmark is positive, divided by benchmark return $\times 100$.
   - **Downside Capture Ratio (%)**: Annualized return of the fund during months when the category benchmark is negative, divided by benchmark return $\times 100$.
   - **Capture Ratio**: Upside Capture / Downside Capture. (> 1.0 indicates favorable upside/downside asymmetry).
5. **Standard Deviation ($\sigma$)**: 3-Year Annualized daily volatility ($\sigma_{\text{daily}} \times \sqrt{252} \times 100$).
6. **Sharpe Ratio**: $(\text{CAGR}_{3Y} - R_f) / \sigma$.
7. **Sortino Ratio**: $(\text{CAGR}_{3Y} - R_f) / \sigma_{\text{downside}}$.

---

## 🚀 How to Run the Pipeline

### 1. Run Complete Sync Across All Equity Categories
```bash
python3 src/main.py --sync
```
This command concurrently ingests all 320+ schemes, computes rolling returns and risk/CAPM metrics against each category's designated SEBI benchmark, ingests Value Research PDF scoreboard ratings and multi-agency scores, and updates all category CSVs and the master Excel file.

### 2. Incorporate / Refresh Ratings from PDF (Zero Network Calls, Fast)
```bash
python3 src/main.py --update-ratings
```
Parses the official Value Research *Mutual Fund Insight* Scoreboard from `reference/` (Page 85 onwards), matches funds to the database with AMC-strict verification, re-computes composite scores, and regenerates all CSV, Excel, and Web files.

### 3. Run for a Specific Category
```bash
python3 src/main.py --sync --category "Small Cap"
```

### 4. Display Leaderboard in Terminal
```bash
python3 src/main.py --report --category "Mid Cap"
```

### 4. Run Local Web Research Platform
```bash
python3 web/server.py
```
Open **`http://localhost:8000`** in any web browser.

---

## ⏰ Automated Daily Updates

AMFI publishes daily closing NAVs on Indian market trading days between **21:00 and 23:00 IST**. You can automate daily updates using either of the following methods:

### Method A: GitHub Actions (Recommended — Cloud Automation, 100% Free)
A ready-to-use GitHub Actions workflow is located at [`.github/workflows/daily_update.yml`](file://.github/workflows/daily_update.yml):
* **Trigger Schedule**: Runs automatically every weekday (Monday through Friday) at **18:00 UTC (23:30 IST)**.
* **Workflow Tasks**:
  1. Checks out the repository.
  2. Runs `python3 src/main.py --sync` to ingest new AMFI NAVs and calculate rolling metrics against SEBI benchmarks.
  3. Updates all CSV files, the Master Excel workbook, and `web/data/funds.json`.
  4. Commits and pushes the updated data back to the repository.
  5. Automatically redeploys the web dashboard if GitHub Pages or Cloudflare Pages is connected.

### Method B: Linux Cron Job (Local Machine / VPS)
To run the sync automatically every night on your local machine or server:
1. Open your crontab editor:
   ```bash
   crontab -e
   ```
2. Add the following cron entry (runs weekdays at 23:30 IST / 18:00 UTC):
   ```cron
   30 23 * * 1-5 /home/gotham/.gemini/antigravity-ide/scratch/MututalFundResearch/scripts/daily_update.sh
   ```
   *(Or if your system timezone is UTC, use `0 18 * * 1-5`).*
