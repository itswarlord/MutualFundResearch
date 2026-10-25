/**
 * Indian Equity Mutual Funds Research Platform
 * Interactive Client Application
 */

// Application State
const state = {
  rawFunds: [],
  categories: [],
  activeCategory: "Flexi Cap", // Default category
  searchTerm: "",
  selectedTier: "ALL",
  selectedSort: "composite_rank_asc",
  selectedFund: null,
  showChart: false,
};

// Category Description Mapping
const CATEGORY_DESCRIPTIONS = {
  "Large Cap": "Minimum 80% investment in top 100 stocks by full market capitalization. Mandated benchmark: NIFTY 100 TRI.",
  "Mid Cap": "Minimum 65% in 101st to 250th stocks by market capitalization. High growth with moderate volatility. Mandated benchmark: NIFTY Midcap 150 TRI.",
  "Small Cap": "Minimum 65% in stocks ranked 251st and beyond. High potential return with higher volatility. Mandated benchmark: NIFTY Smallcap 250 TRI.",
  "Flexi Cap": "Dynamic multi-cap strategy with minimum 65% in equity across Large, Mid, and Small cap stocks. Mandated benchmark: NIFTY 500 TRI.",
  "Multi Cap": "Minimum 25% mandatory allocation each in Large, Mid, and Small caps. Mandated benchmark: NIFTY 500 Multicap 50:25:25 TRI.",
  "Large & Mid Cap": "Minimum 35% in Large Cap and 35% in Mid Cap stocks (top 250 universe). Mandated benchmark: NIFTY LargeMidcap 250 TRI.",
  "ELSS": "Equity Linked Savings Schemes under Section 80C with 3-year statutory lock-in period. Mandated benchmark: NIFTY 500 TRI.",
  "Focused Fund": "High-conviction portfolio with maximum 30 stocks across market caps. Mandated benchmark: NIFTY 500 TRI.",
  "Value & Contra": "Value investing or contrarian strategy with minimum 65% in equity. Mandated benchmark: NIFTY 500 TRI.",
  "Dividend Yield": "Minimum 65% in dividend-yielding companies offering defensive cash-flow yields. Mandated benchmark: NIFTY 500 TRI.",
};

// Benchmark Proxy Details
const BENCHMARK_DETAILS = {
  "Large Cap": { name: "NIFTY 100 TRI", proxy: "Axis Nifty 100 Index Fund (Direct Growth - 147666)" },
  "Mid Cap": { name: "NIFTY Midcap 150 TRI", proxy: "Motilal Oswal Nifty Midcap 150 Index Fund (147622)" },
  "Small Cap": { name: "NIFTY Smallcap 250 TRI", proxy: "Motilal Oswal Nifty Smallcap 250 Index Fund (147623)" },
  "Flexi Cap": { name: "NIFTY 500 TRI", proxy: "Motilal Oswal Nifty 500 Index Fund (147625)" },
  "Multi Cap": { name: "NIFTY 500 Multicap 50:25:25 TRI", proxy: "Navi Nifty 500 Multicap Index Fund (152751)" },
  "Large & Mid Cap": { name: "NIFTY LargeMidcap 250 TRI", proxy: "Edelweiss NIFTY Large Midcap 250 Index Fund (149343)" },
  "ELSS": { name: "NIFTY 500 TRI", proxy: "Motilal Oswal Nifty 500 Index Fund (147625)" },
  "Focused Fund": { name: "NIFTY 500 TRI", proxy: "Motilal Oswal Nifty 500 Index Fund (147625)" },
  "Value & Contra": { name: "NIFTY 500 TRI", proxy: "Motilal Oswal Nifty 500 Index Fund (147625)" },
  "Dividend Yield": { name: "NIFTY 500 TRI", proxy: "Motilal Oswal Nifty 500 Index Fund (147625)" },
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await loadFundsData();
});

// Event Listeners
function setupEventListeners() {
  // Search Input
  const searchInput = document.getElementById("filter-search");
  const clearBtn = document.getElementById("btn-clear-search");
  searchInput.addEventListener("input", (e) => {
    state.searchTerm = e.target.value.trim().toLowerCase();
    clearBtn.style.display = state.searchTerm ? "block" : "none";
    renderTable();
  });

  clearBtn.addEventListener("click", () => {
    searchInput.value = "";
    state.searchTerm = "";
    clearBtn.style.display = "none";
    renderTable();
  });

  // Tier Filter
  document.getElementById("filter-tier").addEventListener("change", (e) => {
    state.selectedTier = e.target.value;
    renderTable();
  });

  // Sort Filter
  document.getElementById("filter-sort").addEventListener("change", (e) => {
    state.selectedSort = e.target.value;
    renderTable();
  });

  // Reset Button
  document.getElementById("btn-reset-filters").addEventListener("click", () => {
    searchInput.value = "";
    state.searchTerm = "";
    document.getElementById("filter-tier").value = "ALL";
    state.selectedTier = "ALL";
    document.getElementById("filter-sort").value = "composite_rank_asc";
    state.selectedSort = "composite_rank_asc";
    renderTable();
  });

  // Toggle Risk-Return Chart
  document.getElementById("btn-toggle-scatter").addEventListener("click", () => {
    state.showChart = !state.showChart;
    const chartSection = document.getElementById("chart-section");
    const toggleBtn = document.getElementById("btn-toggle-scatter");
    if (state.showChart) {
      chartSection.style.display = "block";
      toggleBtn.textContent = "✕ Hide Chart";
      drawRiskReturnChart();
    } else {
      chartSection.style.display = "none";
      toggleBtn.textContent = "📈 Toggle Risk-Return Chart";
    }
  });

  // Day / Night Theme Mode Setup
  initTheme();

  // Alternate Category Selection Dropdown
  const catDropdown = document.getElementById("category-dropdown-select");
  if (catDropdown) {
    catDropdown.addEventListener("change", (e) => {
      selectCategory(e.target.value);
    });
  }

  // Methodology Modal Setup
  setupModal("btn-methodology", "modal-methodology", "modal-methodology-close", "modal-methodology-ack");

  // Drawer Close
  document.getElementById("drawer-close-btn").addEventListener("click", closeDrawer);
  document.getElementById("fund-drawer-overlay").addEventListener("click", closeDrawer);

  // Esc key closes modals/drawer
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeDrawer();
      document.querySelectorAll(".modal-backdrop.active").forEach((m) => m.classList.remove("active"));
    }
  });

  // Window resize redraws canvas
  window.addEventListener("resize", () => {
    if (state.showChart) drawRiskReturnChart();
  });
}

function setupModal(openBtnId, modalId, closeBtnId, ackBtnId) {
  const openBtn = document.getElementById(openBtnId);
  const modal = document.getElementById(modalId);
  const closeBtn = document.getElementById(closeBtnId);
  const ackBtn = document.getElementById(ackBtnId);

  if (openBtn && modal) {
    openBtn.addEventListener("click", () => modal.classList.add("active"));
  }
  if (closeBtn) {
    closeBtn.addEventListener("click", () => modal.classList.remove("active"));
  }
  if (ackBtn) {
    ackBtn.addEventListener("click", () => modal.classList.remove("active"));
  }
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
  }
}

// Day / Night Mode Switcher
function initTheme() {
  const themeBtn = document.getElementById("theme-toggle-btn");
  const themeLabel = document.getElementById("theme-label");
  if (!themeBtn) return;

  function updateThemeUI(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("mf_theme", theme);
    if (themeLabel) {
      themeLabel.textContent = theme === "light" ? "Dark Mode" : "Light Mode";
    }
    themeBtn.setAttribute("title", theme === "light" ? "Switch to Dark Mode (Night)" : "Switch to Light Mode (Day)");
    if (state.showChart) {
      drawRiskReturnChart();
    }
  }

  const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
  updateThemeUI(currentTheme);

  themeBtn.addEventListener("click", () => {
    const active = document.documentElement.getAttribute("data-theme") || "dark";
    const next = active === "light" ? "dark" : "light";
    updateThemeUI(next);
  });
}

// Load Funds Data from JSON
async function loadFundsData() {
  try {
    const res = await fetch("data/funds.json");
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();

    state.rawFunds = data.funds || [];
    state.categories = data.categories || [];

    // Update KPI Header stats
    document.getElementById("stat-funds-count").textContent = data.total_funds || state.rawFunds.length;
    document.getElementById("stat-categories-count").textContent = state.categories.length;
    if (data.total_aum_cr) {
      const lakhCr = (data.total_aum_cr / 100000).toFixed(1);
      document.getElementById("stat-total-aum").textContent = `₹${lakhCr} Lakh Cr`;
    }

    renderCategoryTabs();
    updateCategoryBanner();
    renderTable();
  } catch (err) {
    console.error("Failed to load funds.json:", err);
    document.getElementById("table-body").innerHTML = `
      <tr><td colspan="9" style="text-align:center; padding: 40px; color: #f87171;">
        Failed to load fund datasets. Ensure the local server is running on port 8000.
      </td></tr>`;
  }
}

// Render Category Navigation Tabs & Alternate Dropdown
function renderCategoryTabs() {
  const container = document.getElementById("category-tabs-container");
  container.innerHTML = "";

  // Synchronize Alternate Category Dropdown
  const dropdown = document.getElementById("category-dropdown-select");
  if (dropdown) {
    dropdown.innerHTML = "";

    state.categories.forEach((cat) => {
      const opt = document.createElement("option");
      opt.value = cat.name;
      opt.textContent = `${cat.name} (${cat.count} schemes)`;
      dropdown.appendChild(opt);
    });
    dropdown.value = state.activeCategory;
  }

  // Individual Category Tabs
  state.categories.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = `cat-tab-btn ${state.activeCategory === cat.name ? "active" : ""}`;
    btn.innerHTML = `${cat.name} <span class="cat-tab-count">${cat.count}</span>`;
    btn.addEventListener("click", () => selectCategory(cat.name));
    container.appendChild(btn);
  });
}

// Category Switcher
function selectCategory(categoryName) {
  state.activeCategory = categoryName;

  // Sync Alternate Dropdown if needed
  const dropdown = document.getElementById("category-dropdown-select");
  if (dropdown && dropdown.value !== categoryName) {
    dropdown.value = categoryName;
  }

  renderCategoryTabs();

  // Smoothly center the active pill tab in horizontal scroll
  const activeTab = document.querySelector(".cat-tab-btn.active");
  if (activeTab) {
    activeTab.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  }

  updateCategoryBanner();
  renderTable();
  if (state.showChart) drawRiskReturnChart();
}

// Update Active Category Header & Benchmark Chip
function updateCategoryBanner() {
  const bInfo = BENCHMARK_DETAILS[state.activeCategory] || { name: "NIFTY 500 TRI", proxy: "Nifty 500" };
  const desc = CATEGORY_DESCRIPTIONS[state.activeCategory] || "Diversified Indian equity mutual funds.";

  document.getElementById("benchmark-display-name").textContent = bInfo.name;
  document.getElementById("cat-banner-title").textContent = `${state.activeCategory} Mutual Funds`;
  document.getElementById("cat-banner-desc").textContent = desc;
  document.getElementById("cat-benchmark-val").textContent = bInfo.name;
  document.getElementById("cat-benchmark-proxy").textContent = bInfo.proxy;

  // Update Category CSV Download link
  const dlBtn = document.getElementById("btn-download-cat-csv");
  const slug = state.activeCategory.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  dlBtn.href = `data/${slug}_summary.csv`;
  dlBtn.download = `${slug}_summary.csv`;
  dlBtn.textContent = `📥 Download ${state.activeCategory} CSV`;
}

// Filter and Sort Funds
function getFilteredFunds() {
  return state.rawFunds
    .filter((f) => {
      // Category Filter
      if (f.category !== state.activeCategory) {
        return false;
      }
      // Search Filter
      if (state.searchTerm) {
        const name = (f.scheme_name || "").toLowerCase();
        const amc = (f.amc || "").toLowerCase();
        const isin = (f.isin_growth || "").toLowerCase();
        if (!name.includes(state.searchTerm) && !amc.includes(state.searchTerm) && !isin.includes(state.searchTerm)) {
          return false;
        }
      }
      // Tier Filter
      if (state.selectedTier !== "ALL") {
        const tier = f.rating_tier || "";
        if (!tier.includes(state.selectedTier)) {
          return false;
        }
      }
      return true;
    })
    .sort((a, b) => {
      switch (state.selectedSort) {
        case "composite_rank_asc":
          return (a.composite_rank || 999) - (b.composite_rank || 999);
        case "return_3y_desc":
          return (b.return_3y_cagr || -999) - (a.return_3y_cagr || -999);
        case "return_1y_desc":
          return (b.return_1y || -999) - (a.return_1y || -999);
        case "alpha_desc":
          return (b.alpha || -999) - (a.alpha || -999);
        case "sharpe_desc":
          return (b.sharpe_ratio || -999) - (a.sharpe_ratio || -999);
        case "volatility_asc":
          return (a.standard_deviation || 999) - (b.standard_deviation || 999);
        case "aum_desc":
          return (b.aum_cr || 0) - (a.aum_cr || 0);
        case "ter_asc":
          return (a.direct_ter || 999) - (b.direct_ter || 999);
        default:
          return 0;
      }
    });
}

// Render Data Table
function renderTable() {
  const tbody = document.getElementById("table-body");
  const emptyState = document.getElementById("table-empty-state");
  const filtered = getFilteredFunds();

  document.getElementById("filtered-count").textContent = filtered.length;

  if (filtered.length === 0) {
    tbody.innerHTML = "";
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";

  tbody.innerHTML = filtered
    .map((fund, idx) => {
      // Rank Badge
      const rank = fund.composite_rank || idx + 1;
      let medalClass = "";
      if (rank === 1) medalClass = "gold";
      else if (rank === 2) medalClass = "silver";
      else if (rank === 3) medalClass = "bronze";

      // Score Tier
      const score = fund.composite_score ? fund.composite_score.toFixed(1) : "N/A";
      const tierText = (fund.rating_tier || "Unrated").split(" ")[0].replace("(", "");
      let tierClass = "tier-below";
      if (tierText.includes("BEST")) tierClass = "tier-best";
      else if (tierText.includes("Tier 2")) tierClass = "tier-superior";
      else if (tierText.includes("Tier 3")) tierClass = "tier-average";
      else if (tierText.includes("WORST")) tierClass = "tier-worst";

      // Agency Chips
      const msStar = fund.morningstar_rating ? `${fund.morningstar_rating}★` : "-";
      const msMed = fund.morningstar_medalist ? ` (${fund.morningstar_medalist[0]})` : "";
      const vrStar = fund.valueresearch_rating ? `${fund.valueresearch_rating}★` : "-";
      const vrRisk = fund.valueresearch_risk_grade ? ` (${fund.valueresearch_risk_grade} Risk)` : "";
      const vrAvg = fund.valueresearch_avg_rating ? ` • 3Y Avg: ${fund.valueresearch_avg_rating}★` : "";
      const vrTooltip = fund.valueresearch_rating
        ? `Value Research Scoreboard: ${fund.valueresearch_rating} Stars${vrRisk}${vrAvg}`
        : "Value Research: Not Rated (NR) / Insufficient Track Record";

      const crRank = fund.crisil_rank ? fund.crisil_rank.replace("Rank ", "R") : "-";
      const ofScore = fund.one_finance_score && fund.one_finance_score > 0 ? fund.one_finance_score : "-";
      const advQ = fund.advisorkhoj_quartile ? fund.advisorkhoj_quartile.split(" ")[0] : "-";

      // Returns
      const ret1y = formatPercent(fund.return_1y);
      const ret3y = formatPercent(fund.return_3y_cagr);
      const ret5y = formatPercent(fund.return_5y_cagr);

      // Risk
      const beta = fund.beta !== null && fund.beta !== undefined ? fund.beta.toFixed(2) : "N/A";
      const alphaVal = fund.alpha !== null && fund.alpha !== undefined ? fund.alpha : null;
      const alphaPill =
        alphaVal !== null
          ? `<span class="alpha-pill ${alphaVal >= 0 ? "positive" : "negative"}">${alphaVal >= 0 ? "+" : ""}${alphaVal.toFixed(2)}%</span>`
          : "N/A";
      const sharpe = fund.sharpe_ratio !== null && fund.sharpe_ratio !== undefined ? fund.sharpe_ratio.toFixed(2) : "N/A";

      // Capture
      const capRatio = fund.capture_ratio !== null && fund.capture_ratio !== undefined ? fund.capture_ratio.toFixed(2) : "N/A";
      const upDown = `${fund.upside_capture ? Math.round(fund.upside_capture) : "-"} / ${fund.downside_capture ? Math.round(fund.downside_capture) : "-"}`;

      // TER
      const dirTer = fund.direct_ter !== null ? `${fund.direct_ter.toFixed(2)}%` : "N/A";
      const regTer = fund.regular_ter !== null ? `${fund.regular_ter.toFixed(2)}%` : "";

      return `
        <tr data-scheme-code="${fund.scheme_code}" onclick="openFundDrawer(${fund.scheme_code})">
          <td class="col-rank">
            <span class="rank-badge ${medalClass}">${rank}</span>
          </td>
          <td class="col-scheme">
            <div class="scheme-name">${escapeHtml(fund.scheme_name)}</div>
            <div class="scheme-meta">
              <span class="tag-amc">${escapeHtml(fund.amc)}</span>
              ${fund.isin_growth ? `<span class="tag-isin" title="ISIN">${fund.isin_growth}</span>` : ""}
              ${fund.benchmark_name ? `<span class="tag-isin" style="color:#38bdf8;" title="Category Benchmark">${escapeHtml(fund.benchmark_name)}</span>` : ""}
            </div>
          </td>
          <td class="col-score">
            <div class="score-badge-wrap">
              <div class="score-row">
                <span class="score-number">${score}</span>
                <span class="score-tier-tag ${tierClass}">${tierText}</span>
              </div>
              <div class="score-bar-bg">
                <div class="score-bar-fill" style="width: ${fund.composite_score || 0}%; background: ${getScoreBarColor(fund.composite_score)};"></div>
              </div>
            </div>
          </td>
          <td class="col-ratings">
            <div class="agency-ratings-grid">
              <span class="agency-chip ms" title="Morningstar Rating">MS: ${msStar}${msMed}</span>
              <span class="agency-chip vr" title="${escapeHtml(vrTooltip)}">VR: ${vrStar}</span>
              <span class="agency-chip cr" title="CRISIL CMFR Rank">CR: ${crRank}</span>
              <span class="agency-chip of" title="1 Finance Score (out of 100)">1F: ${ofScore}</span>
              <span class="agency-chip adv" title="Advisorkhoj Volatility Quartile">ADV: ${advQ}</span>
            </div>
          </td>
          <td class="col-returns">
            <div class="returns-cluster">
              <div class="ret-primary">${ret3y} <span style="font-size:10px; color:#64748b;">(3Y)</span></div>
              <div class="ret-secondary">1Y: ${ret1y} • 5Y: ${ret5y}</div>
            </div>
          </td>
          <td class="col-risk">
            <div class="risk-cluster">
              <div class="risk-row">
                <span class="risk-tag">&beta;: ${beta}</span>
                <span class="risk-tag">Sh: ${sharpe}</span>
              </div>
              <div>Alpha: ${alphaPill}</div>
            </div>
          </td>
          <td class="col-capture">
            <div class="capture-box">
              <span class="capture-ratio-val ${fund.capture_ratio >= 1.0 ? "val-positive" : ""}">${capRatio}</span>
              <span class="capture-split">Up/Dn: ${upDown}</span>
            </div>
          </td>
          <td class="col-ter">
            <div class="ter-direct">${dirTer}</div>
            ${regTer ? `<div class="ter-regular">${regTer}</div>` : ""}
          </td>
          <td class="col-action" onclick="event.stopPropagation();">
            <button class="btn-details" onclick="openFundDrawer(${fund.scheme_code})">Inspect</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

// Open Fund Detail Slide-over Drawer
function openFundDrawer(schemeCode) {
  const fund = state.rawFunds.find((f) => f.scheme_code === schemeCode);
  if (!fund) return;
  state.selectedFund = fund;

  document.getElementById("drawer-category").textContent = `${fund.category} Fund`;
  document.getElementById("drawer-scheme-name").textContent = fund.scheme_name;
  document.getElementById("drawer-meta-line").textContent = `${fund.amc} • Code: ${fund.scheme_code} • ${fund.isin_growth || ""}`;

  const content = document.getElementById("drawer-content");

  // Multi-Agency Breakdown Card
  const msStar = fund.morningstar_rating ? `${fund.morningstar_rating}★` : "Unrated";
  const msMed = fund.morningstar_medalist || "None";
  const vrStar = fund.valueresearch_rating ? `${fund.valueresearch_rating}★` : "Unrated";
  const crRank = fund.crisil_rank || "Unranked";
  const ofScore = fund.one_finance_score ? `${fund.one_finance_score}/100` : "N/A";
  const advQ = fund.advisorkhoj_quartile || "N/A";

  // Returns Progress bars
  const intervals = [
    { label: "1 Month", val: fund.return_1m },
    { label: "3 Months", val: fund.return_3m },
    { label: "6 Months", val: fund.return_6m },
    { label: "1 Year", val: fund.return_1y },
    { label: "2Y CAGR", val: fund.return_2y_cagr },
    { label: "3Y CAGR", val: fund.return_3y_cagr },
    { label: "5Y CAGR", val: fund.return_5y_cagr },
    { label: "Inception", val: fund.return_inception_cagr },
  ];

  const returnsHtml = intervals
    .map((item) => {
      const v = item.val;
      const formatted = formatPercent(v);
      const isPos = v !== null && v >= 0;
      const width = v !== null ? Math.min(Math.max(Math.abs(v) * 2.5, 2), 100) : 0;
      const barColor = isPos ? "var(--accent-emerald)" : "var(--accent-crimson)";
      return `
        <div class="progress-item">
          <span class="progress-period">${item.label}</span>
          <div class="progress-track">
            <div class="progress-bar-fill" style="width: ${width}%; background: ${barColor};"></div>
          </div>
          <span class="progress-val ${isPos ? "val-positive" : "val-negative"}">${formatted}</span>
        </div>
      `;
    })
    .join("");

  content.innerHTML = `
    <!-- Key Statistics Grid -->
    <div class="drawer-card">
      <div class="drawer-card-title">Portfolio & NAV Overview</div>
      <div class="drawer-stats-row">
        <div class="d-stat-box">
          <div class="d-stat-label">Latest NAV</div>
          <div class="d-stat-val">₹${fund.latest_nav ? fund.latest_nav.toFixed(2) : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Live AUM</div>
          <div class="d-stat-val">₹${fund.aum_cr ? fund.aum_cr.toLocaleString() : "N/A"} Cr</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Composite Rank</div>
          <div class="d-stat-val" style="color: #38bdf8;">#${fund.composite_rank || "-"}</div>
        </div>
      </div>
    </div>

    <!-- SEBI Category Benchmark Evaluation -->
    <div class="drawer-card" style="border-left: 3px solid #38bdf8;">
      <div class="drawer-card-title">SEBI Designated Benchmark</div>
      <p style="font-size: 13px; color: #e2e8f0; margin-bottom: 6px;">
        Evaluated against <strong>${escapeHtml(fund.benchmark_name || "NIFTY 500 TRI")}</strong>
      </p>
      <p style="font-size: 11px; color: var(--text-dim); line-height: 1.4;">
        All sensitivity metrics below (Beta, Jensen's Alpha, R-Squared, and Capture Ratios) are strictly measured against this category's benchmark index.
      </p>
    </div>

    <!-- CAPM Risk Sensitivity Breakdown -->
    <div class="drawer-card">
      <div class="drawer-card-title">CAPM & Risk Analytics (3-Year Horizon)</div>
      <div class="drawer-stats-row" style="margin-bottom: 12px;">
        <div class="d-stat-box">
          <div class="d-stat-label">Beta (&beta;)</div>
          <div class="d-stat-val">${fund.beta !== null ? fund.beta.toFixed(2) : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Jensen's Alpha (&alpha;)</div>
          <div class="d-stat-val ${fund.alpha >= 0 ? "val-positive" : "val-negative"}">
            ${fund.alpha !== null ? (fund.alpha >= 0 ? "+" : "") + fund.alpha.toFixed(2) + "%" : "N/A"}
          </div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">R-Squared (R&sup2;)</div>
          <div class="d-stat-val">${fund.r_squared !== null ? fund.r_squared.toFixed(2) : "N/A"}</div>
        </div>
      </div>
      <div class="drawer-stats-row">
        <div class="d-stat-box">
          <div class="d-stat-label">Sharpe Ratio</div>
          <div class="d-stat-val">${fund.sharpe_ratio !== null ? fund.sharpe_ratio.toFixed(2) : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Sortino Ratio</div>
          <div class="d-stat-val">${fund.sortino_ratio !== null ? fund.sortino_ratio.toFixed(2) : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Max Drawdown</div>
          <div class="d-stat-val val-negative">${fund.max_drawdown_3y !== null ? "-" + fund.max_drawdown_3y.toFixed(2) + "%" : "N/A"}</div>
        </div>
      </div>
    </div>

    <!-- Morningstar Capture Ratios -->
    <div class="drawer-card">
      <div class="drawer-card-title">
        <span>Capture Ratios (Upside vs Downside)</span>
        <span style="font-size:11px; font-weight:600; color:${fund.capture_ratio >= 1.0 ? "var(--accent-emerald)" : "var(--accent-crimson)"}">
          ${fund.capture_ratio >= 1.0 ? "✓ Asymmetrical Outperformer" : "Underperforming"}
        </span>
      </div>
      <div class="drawer-stats-row">
        <div class="d-stat-box">
          <div class="d-stat-label">Upside Capture</div>
          <div class="d-stat-val val-positive">${fund.upside_capture ? fund.upside_capture.toFixed(1) + "%" : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Downside Capture</div>
          <div class="d-stat-val val-negative">${fund.downside_capture ? fund.downside_capture.toFixed(1) + "%" : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Overall Ratio</div>
          <div class="d-stat-val">${fund.capture_ratio ? fund.capture_ratio.toFixed(2) : "N/A"}</div>
        </div>
      </div>
    </div>

    <!-- Returns Progression -->
    <div class="drawer-card">
      <div class="drawer-card-title">Historical Returns Progression</div>
      <div class="progress-list">${returnsHtml}</div>
    </div>

    <!-- Agency Ratings Grid -->
    <div class="drawer-card">
      <div class="drawer-card-title">Multi-Agency Ratings Matrix</div>
      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
        <div class="d-stat-box" style="text-align: left;">
          <div class="d-stat-label">Morningstar Star & Medal</div>
          <div class="d-stat-val" style="color: #f59e0b;">${msStar} (${msMed})</div>
        </div>
        <div class="d-stat-box" style="text-align: left;">
          <div class="d-stat-label">Value Research Rating</div>
          <div class="d-stat-val" style="color: #38bdf8;">${vrStar}</div>
          ${fund.valueresearch_risk_grade ? `<div style="font-size: 11px; color: #94a3b8; margin-top: 3px;">Risk: <strong style="color: #e2e8f0;">${fund.valueresearch_risk_grade}</strong></div>` : ""}
          ${fund.valueresearch_avg_rating ? `<div style="font-size: 11px; color: #94a3b8;">3Y Avg: <strong style="color: #f59e0b;">${fund.valueresearch_avg_rating}★</strong></div>` : ""}
        </div>
        <div class="d-stat-box" style="text-align: left;">
          <div class="d-stat-label">CRISIL CMFR Rank</div>
          <div class="d-stat-val" style="color: #a78bfa;">${crRank}</div>
        </div>
        <div class="d-stat-box" style="text-align: left;">
          <div class="d-stat-label">1 Finance Score</div>
          <div class="d-stat-val" style="color: #34d399;">${ofScore}</div>
        </div>
      </div>
    </div>

    <!-- TER Fee Comparison -->
    <div class="drawer-card">
      <div class="drawer-card-title">Expense Ratio Savings (Direct vs Regular)</div>
      <div class="drawer-stats-row">
        <div class="d-stat-box">
          <div class="d-stat-label">Direct TER</div>
          <div class="d-stat-val" style="color: var(--accent-emerald);">${fund.direct_ter !== null ? fund.direct_ter.toFixed(2) + "%" : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Regular TER</div>
          <div class="d-stat-val" style="color: var(--text-dim); text-decoration: line-through;">
            ${fund.regular_ter !== null ? fund.regular_ter.toFixed(2) + "%" : "N/A"}
          </div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Annual Savings</div>
          <div class="d-stat-val" style="color: #38bdf8;">
            ${fund.direct_ter && fund.regular_ter ? (fund.regular_ter - fund.direct_ter).toFixed(2) + "%" : "N/A"}
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById("fund-drawer").classList.add("active");
  document.getElementById("fund-drawer-overlay").classList.add("active");
}

function closeDrawer() {
  document.getElementById("fund-drawer").classList.remove("active");
  document.getElementById("fund-drawer-overlay").classList.remove("active");
  state.selectedFund = null;
}

// Canvas-based Risk-Return Scatter Plot
function drawRiskReturnChart() {
  const canvas = document.getElementById("riskReturnCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Handle Retina HiDPI displays
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;

  ctx.clearRect(0, 0, width, height);

  // Filter funds with valid 3Y CAGR and Volatility
  const categoryFunds = state.rawFunds.filter((f) => {
    if (f.category !== state.activeCategory) return false;
    return f.standard_deviation !== null && f.return_3y_cagr !== null;
  });

  if (categoryFunds.length === 0) {
    ctx.fillStyle = "#94a3b8";
    ctx.font = "14px Plus Jakarta Sans";
    ctx.textAlign = "center";
    ctx.fillText("No 3-year performance data available for this category", width / 2, height / 2);
    return;
  }

  // Find min/max ranges
  let minVol = Infinity, maxVol = -Infinity;
  let minRet = Infinity, maxRet = -Infinity;

  categoryFunds.forEach((f) => {
    if (f.standard_deviation < minVol) minVol = f.standard_deviation;
    if (f.standard_deviation > maxVol) maxVol = f.standard_deviation;
    if (f.return_3y_cagr < minRet) minRet = f.return_3y_cagr;
    if (f.return_3y_cagr > maxRet) maxRet = f.return_3y_cagr;
  });

  // Pad margins
  minVol = Math.max(0, Math.floor(minVol - 1));
  maxVol = Math.ceil(maxVol + 2);
  minRet = Math.floor(minRet - 2);
  maxRet = Math.ceil(maxRet + 2);

  const padding = { top: 30, right: 40, bottom: 45, left: 60 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  // Theme-aware colors
  const isLight = document.documentElement.getAttribute("data-theme") === "light";

  // Draw Grid lines
  ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.08)" : "rgba(255, 255, 255, 0.06)";
  ctx.lineWidth = 1;
  ctx.fillStyle = isLight ? "#475569" : "#64748b";
  ctx.font = "11px JetBrains Mono";
  ctx.textAlign = "right";

  // Y-axis grid
  const ySteps = 5;
  for (let i = 0; i <= ySteps; i++) {
    const val = minRet + ((maxRet - minRet) / ySteps) * i;
    const y = padding.top + plotH - (i / ySteps) * plotH;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(`${val.toFixed(1)}%`, padding.left - 10, y + 4);
  }

  // X-axis grid
  ctx.textAlign = "center";
  const xSteps = 6;
  for (let i = 0; i <= xSteps; i++) {
    const val = minVol + ((maxVol - minVol) / xSteps) * i;
    const x = padding.left + (i / xSteps) * plotW;
    ctx.beginPath();
    ctx.moveTo(x, padding.top);
    ctx.lineTo(x, height - padding.bottom);
    ctx.stroke();
    ctx.fillText(`${val.toFixed(0)}%`, x, height - padding.bottom + 18);
  }

  // Axis Labels
  ctx.fillStyle = isLight ? "#1e293b" : "#94a3b8";
  ctx.font = "12px Plus Jakarta Sans";
  ctx.textAlign = "center";
  ctx.fillText("Annualized Volatility / Standard Deviation (σ)", padding.left + plotW / 2, height - 10);

  ctx.save();
  ctx.translate(16, padding.top + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("3-Year CAGR Return (%)", 0, 0);
  ctx.restore();

  // Draw Fund Bubbles
  categoryFunds.forEach((f) => {
    const x = padding.left + ((f.standard_deviation - minVol) / (maxVol - minVol)) * plotW;
    const y = padding.top + plotH - ((f.return_3y_cagr - minRet) / (maxRet - minRet)) * plotH;

    // Radius scaled by AUM
    const aum = f.aum_cr || 1000;
    const r = Math.min(Math.max(Math.sqrt(aum) / 25, 5), 18);

    // Color by Tier
    let color = "#64748b";
    const tier = f.rating_tier || "";
    if (tier.includes("BEST")) color = "#10b981";
    else if (tier.includes("Tier 2")) color = "#3b82f6";
    else if (tier.includes("Tier 3")) color = "#f59e0b";

    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.65;
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = "#ffffff";
    ctx.globalAlpha = 0.9;
    ctx.stroke();
    ctx.globalAlpha = 1.0;

    // Label for top 3
    if (f.composite_rank && f.composite_rank <= 3) {
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 10px Plus Jakarta Sans";
      ctx.textAlign = "center";
      ctx.fillText(`#${f.composite_rank}`, x, y + 3);
    }
  });
}

// Utility Helpers
function formatPercent(val) {
  if (val === null || val === undefined) return "N/A";
  const num = typeof val === "number" ? val : parseFloat(val);
  if (isNaN(num)) return "N/A";
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(2)}%`;
}

function getScoreBarColor(score) {
  if (!score) return "#64748b";
  if (score >= 75) return "linear-gradient(90deg, #10b981, #34d399)";
  if (score >= 65) return "linear-gradient(90deg, #2563eb, #60a5fa)";
  if (score >= 50) return "linear-gradient(90deg, #d97706, #fbbf24)";
  return "linear-gradient(90deg, #dc2626, #f87171)";
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
