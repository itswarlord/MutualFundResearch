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

### 1. Flexi Cap Funds (Top 5)
| Rank | Scheme Name | Tier & Score | 3Y CAGR | Std Dev | Sharpe | Beta | Alpha | Capture Ratio | Live AUM (₹ Cr) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | **Parag Parikh Flexi Cap Fund** | **BEST (97.5/100)** | 12.29% | **9.90%** | 0.53 | **0.61** | **+4.26%** | **1.44** | **₹145,070 Cr** |
| **02** | **HDFC Flexi Cap Fund** | **BEST (96.0/100)** | 14.39% | 12.12% | **0.61** | 0.80 | **+5.96%** | **1.32** | **₹108,547 Cr** |
| **03** | **Bank of India Flexi Cap Fund** | **Tier 2 (74.2/100)** | **17.39%** | 17.68% | 0.59 | 1.13 | **+8.10%** | **1.35** | ₹3,098 Cr |
| **04** | **Kotak Flexi Cap Fund** | **Tier 2 (73.9/100)** | 10.32% | 14.60% | 0.23 | 0.99 | +1.26% | 1.06 | ₹53,087 Cr |
| **05** | **Edelweiss Flexi Cap Fund** | **Tier 2 (73.9/100)** | 13.16% | 14.72% | 0.42 | 1.01 | **+4.16%** | **1.18** | ₹3,509 Cr |

### 2. Large Cap Funds (Top 5)
| Rank | Scheme Name | Tier & Score | 3Y CAGR | Std Dev | Sharpe | Beta | Alpha | Capture Ratio | Live AUM (₹ Cr) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | **UTI Large Cap Fund** | **Tier 3 (52.2/100)** | 6.82% | 12.61% | -0.01 | 0.84 | -1.85% | 0.91 | ₹9,673 Cr |
| **02** | **ICICI Prudential Large Cap (Bluechip)** | **Tier 3 (51.9/100)** | 9.57% | 12.73% | 0.20 | 0.86 | +0.89% | 1.03 | **₹76,352 Cr** |
| **03** | **SBI Large Cap Fund** | **Tier 3 (51.9/100)** | 8.02% | 12.63% | 0.08 | 0.85 | -0.66% | 0.97 | **₹52,373 Cr** |
| **04** | **Sundaram Large Cap Fund** | **Tier 3 (50.7/100)** | 7.10% | 12.89% | 0.01 | 0.86 | -1.62% | 0.92 | ₹2,866 Cr |
| **05** | **DSP Large Cap Fund** | **Tier 3 (50.1/100)** | 10.04% | 12.36% | 0.25 | 0.81 | +1.42% | 1.08 | ₹6,642 Cr |

### 3. Small Cap Funds (Top 5)
| Rank | Scheme Name | Tier & Score | 3Y CAGR | Std Dev | Sharpe | Beta | Alpha | Capture Ratio | Live AUM (₹ Cr) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | **SBI Small Cap Fund** | **Tier 3 (51.0/100)** | 9.46% | 14.25% | 0.17 | 0.84 | +0.83% | 1.02 | ₹41,059 Cr |
| **02** | **Axis Small Cap Fund** | **Tier 3 (51.0/100)** | 12.90% | 15.05% | 0.39 | 0.93 | **+4.08%** | **1.15** | ₹30,678 Cr |
| **03** | **Kotak Small Cap Fund** | **Tier 3 (51.0/100)** | 10.20% | 15.49% | 0.21 | 0.93 | +1.23% | 1.06 | ₹19,141 Cr |
| **04** | **ICICI Prudential Small Cap Fund** | **Tier 4 (49.5/100)** | 9.24% | 14.41% | 0.16 | 0.89 | +0.55% | 1.01 | ₹9,791 Cr |
| **05** | **PGIM India Small Cap Fund** | **Tier 4 (46.2/100)** | 13.58% | 15.68% | 0.42 | 0.91 | **+4.74%** | **1.19** | ₹1,739 Cr |

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
This command concurrently ingests all 320+ schemes, computes rolling returns and risk/CAPM metrics against each category's designated SEBI benchmark, ingests ratings, and updates all category CSVs and the single master Excel file.

### 2. Run for a Specific Category
```bash
python3 src/main.py --sync --category "Small Cap"
```

### 3. Display Leaderboard in Terminal
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
