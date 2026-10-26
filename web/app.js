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
  showChart: true,
  chartHorizon: "3y",
  chartViewMode: "3d", // "2d" or "3d"
  chartThirdDim: "sharpe_ratio", // metric key for 3rd dim / Z-axis
  chartHoveredFund: null,
  chartPoints: [],
  camera3D: {
    yaw: -0.65,
    pitch: 0.38,
    zoom: 1.0,
    isDragging: false,
    lastMouseX: 0,
    lastMouseY: 0,
  },
  activeInspectedFund: null,
};

// 3rd Dimension Metric Configurations
const THIRD_DIM_CONFIG = {
  sharpe_ratio: {
    key: "sharpe_ratio",
    label: "Sharpe Ratio",
    shortLabel: "Sharpe",
    format: (v) => (v !== null && v !== undefined ? Number(v).toFixed(2) : "N/A"),
    getVal: (f) => f.sharpe_ratio,
  },
  alpha: {
    key: "alpha",
    label: "Jensen's Alpha (%)",
    shortLabel: "Alpha",
    format: (v) => (v !== null && v !== undefined ? `${v > 0 ? "+" : ""}${Number(v).toFixed(2)}%` : "N/A"),
    getVal: (f) => f.alpha,
  },
  beta: {
    key: "beta",
    label: "Market Beta (β)",
    shortLabel: "Beta",
    format: (v) => (v !== null && v !== undefined ? Number(v).toFixed(2) : "N/A"),
    getVal: (f) => f.beta,
  },
  aum_cr: {
    key: "aum_cr",
    label: "Live AUM (₹ Cr)",
    shortLabel: "AUM",
    format: (v) => (v !== null && v !== undefined ? `₹${Math.round(Number(v)).toLocaleString()} Cr` : "N/A"),
    getVal: (f) => f.aum_cr,
  },
  sortino_ratio: {
    key: "sortino_ratio",
    label: "Sortino Ratio",
    shortLabel: "Sortino",
    format: (v) => (v !== null && v !== undefined ? Number(v).toFixed(2) : "N/A"),
    getVal: (f) => f.sortino_ratio,
  },
  capture_ratio: {
    key: "capture_ratio",
    label: "Overall Capture Ratio",
    shortLabel: "Capture",
    format: (v) => (v !== null && v !== undefined ? Number(v).toFixed(2) : "N/A"),
    getVal: (f) => f.capture_ratio,
  },
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
    if (state.showChart) drawRiskReturnChart();
  });

  clearBtn.addEventListener("click", () => {
    searchInput.value = "";
    state.searchTerm = "";
    clearBtn.style.display = "none";
    renderTable();
    if (state.showChart) drawRiskReturnChart();
  });

  // Tier Filter
  document.getElementById("filter-tier").addEventListener("change", (e) => {
    state.selectedTier = e.target.value;
    renderTable();
    if (state.showChart) drawRiskReturnChart();
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
    if (state.showChart) drawRiskReturnChart();
  });

  // Toggle Risk-Return Chart
  document.getElementById("btn-toggle-scatter").addEventListener("click", () => {
    state.showChart = !state.showChart;
    const chartSection = document.getElementById("chart-section");
    const toggleBtn = document.getElementById("btn-toggle-scatter");
    if (state.showChart) {
      chartSection.style.display = "block";
      toggleBtn.textContent = "✕ Hide Risk-Return Chart";
      drawRiskReturnChart();
    } else {
      chartSection.style.display = "none";
      toggleBtn.textContent = "📈 Toggle Risk-Return Chart";
      const tooltip = document.getElementById("chart-tooltip");
      if (tooltip) tooltip.style.display = "none";
    }
  });

  // Horizon Switcher buttons
  const btn3y = document.getElementById("btn-horizon-3y");
  const btn1y = document.getElementById("btn-horizon-1y");
  if (btn3y && btn1y) {
    btn3y.addEventListener("click", () => {
      if (state.chartHorizon === "3y") return;
      state.chartHorizon = "3y";
      btn3y.classList.add("active");
      btn1y.classList.remove("active");
      const labelEl = document.getElementById("chart-y-axis-label");
      if (labelEl) labelEl.textContent = "3Y CAGR (%)";
      if (state.showChart) drawRiskReturnChart();
    });
    btn1y.addEventListener("click", () => {
      if (state.chartHorizon === "1y") return;
      state.chartHorizon = "1y";
      btn1y.classList.add("active");
      btn3y.classList.remove("active");
      const labelEl = document.getElementById("chart-y-axis-label");
      if (labelEl) labelEl.textContent = "1Y Return (%)";
      if (state.showChart) drawRiskReturnChart();
    });
  }

  // View Mode Switcher (2D Bubble vs 3D Perspective)
  const btn2d = document.getElementById("btn-view-2d");
  const btn3d = document.getElementById("btn-view-3d");
  const resetCamBtn = document.getElementById("btn-reset-camera");
  const aumScaleLegend = document.getElementById("chart-aum-scale-legend");
  const hintOverlay = document.getElementById("chart-hint-overlay");
  const zSubText = document.getElementById("chart-z-axis-sub");

  if (btn2d && btn3d) {
    btn2d.addEventListener("click", () => {
      if (state.chartViewMode === "2d") return;
      state.chartViewMode = "2d";
      btn2d.classList.add("active");
      btn3d.classList.remove("active");
      if (resetCamBtn) resetCamBtn.style.display = "none";
      if (aumScaleLegend) aumScaleLegend.style.display = "flex";
      if (zSubText) zSubText.textContent = "Bubble Size: AUM";
      if (hintOverlay) {
        hintOverlay.innerHTML = `<span>💡 Hover bubble for Rank &amp; details &bull; Click to open full scheme analysis</span>`;
      }
      if (state.showChart) drawRiskReturnChart();
    });

    btn3d.addEventListener("click", () => {
      if (state.chartViewMode === "3d") return;
      state.chartViewMode = "3d";
      btn3d.classList.add("active");
      btn2d.classList.remove("active");
      if (resetCamBtn) resetCamBtn.style.display = "inline-flex";
      if (aumScaleLegend) aumScaleLegend.style.display = "none";
      const dimCfg = THIRD_DIM_CONFIG[state.chartThirdDim] || THIRD_DIM_CONFIG.sharpe_ratio;
      if (zSubText) zSubText.textContent = `Z-Axis: ${dimCfg.label} | Bubble Size: AUM`;
      if (hintOverlay) {
        hintOverlay.innerHTML = `<span>🖱️ Click &amp; drag to rotate 3D view &bull; Scroll to zoom &bull; Hover for 3D stats &bull; Click for scheme</span>`;
      }
      if (state.showChart) drawRiskReturnChart();
    });
  }

  // 3rd Dimension Selector Dropdown
  const thirdDimSelect = document.getElementById("select-third-dim");
  if (thirdDimSelect) {
    thirdDimSelect.addEventListener("change", (e) => {
      state.chartThirdDim = e.target.value;
      const dimCfg = THIRD_DIM_CONFIG[state.chartThirdDim] || THIRD_DIM_CONFIG.sharpe_ratio;
      if (state.chartViewMode === "3d" && zSubText) {
        zSubText.textContent = `Z-Axis: ${dimCfg.label} | Bubble Size: AUM`;
      }
      if (state.showChart) drawRiskReturnChart();
    });
  }

  // Reset 3D Camera button
  if (resetCamBtn) {
    resetCamBtn.addEventListener("click", () => {
      state.camera3D.yaw = -0.65;
      state.camera3D.pitch = 0.38;
      state.camera3D.zoom = 1.0;
      if (state.showChart) drawRiskReturnChart();
    });
  }

  // Setup interactive hover/click listeners on the chart
  setupChartInteractions();

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

  // Companion Scheme Inspector Dossier Button
  const inspectorDossierBtn = document.getElementById("inspector-btn-dossier");
  if (inspectorDossierBtn) {
    inspectorDossierBtn.addEventListener("click", () => {
      if (state.activeInspectedFund && state.activeInspectedFund.scheme_code) {
        openFundDrawer(state.activeInspectedFund.scheme_code);
      }
    });
  }
}

// Scheme Diagnostic Companion Inspector
function updateSchemeInspector(fund) {
  if (!fund) return;
  state.activeInspectedFund = fund;

  const titleEl = document.getElementById("inspector-scheme-name");
  const metaEl = document.getElementById("inspector-meta");
  const rankBadgeEl = document.getElementById("inspector-rank-badge");
  const alphaEl = document.getElementById("inspector-alpha");
  const betaEl = document.getElementById("inspector-beta");
  const sharpeEl = document.getElementById("inspector-sharpe");
  const sortinoEl = document.getElementById("inspector-sortino");
  const volEl = document.getElementById("inspector-volatility");
  const captureEl = document.getElementById("inspector-capture");
  const aumEl = document.getElementById("inspector-aum");
  const terEl = document.getElementById("inspector-ter");
  const msEl = document.getElementById("inspector-ms");
  const vrEl = document.getElementById("inspector-vr");
  const crisilEl = document.getElementById("inspector-crisil");

  if (titleEl) titleEl.textContent = fund.scheme_name || "Scheme Focus";
  if (metaEl) metaEl.textContent = `${fund.amc || "Direct Plan"} • Code: ${fund.scheme_code || "—"}`;

  if (rankBadgeEl) {
    rankBadgeEl.textContent = `#${fund.composite_rank || "—"} IN CATEGORY`;
    const tier = fund.rating_tier || "";
    if (tier.includes("BEST")) rankBadgeEl.className = "inspector-rank-pill best";
    else if (tier.includes("Tier 2")) rankBadgeEl.className = "inspector-rank-pill superior";
    else if (tier.includes("Tier 3")) rankBadgeEl.className = "inspector-rank-pill average";
    else rankBadgeEl.className = "inspector-rank-pill below";
  }

  if (alphaEl) {
    if (fund.alpha !== null && fund.alpha !== undefined) {
      alphaEl.textContent = (fund.alpha >= 0 ? "+" : "") + fund.alpha.toFixed(2) + "%";
      alphaEl.className = "im-val " + (fund.alpha >= 0 ? "val-pos" : "val-neg");
    } else {
      alphaEl.textContent = "N/A";
      alphaEl.className = "im-val";
    }
  }

  if (betaEl) betaEl.textContent = fund.beta !== null && fund.beta !== undefined ? fund.beta.toFixed(2) : "N/A";
  if (sharpeEl) sharpeEl.textContent = fund.sharpe_ratio !== null && fund.sharpe_ratio !== undefined ? fund.sharpe_ratio.toFixed(2) : "N/A";
  if (sortinoEl) sortinoEl.textContent = fund.sortino_ratio !== null && fund.sortino_ratio !== undefined ? fund.sortino_ratio.toFixed(2) : "N/A";
  if (volEl) volEl.textContent = fund.standard_deviation !== null && fund.standard_deviation !== undefined ? fund.standard_deviation.toFixed(2) + "%" : "N/A";
  if (captureEl) captureEl.textContent = fund.capture_ratio !== null && fund.capture_ratio !== undefined ? fund.capture_ratio.toFixed(2) : "N/A";
  if (aumEl) aumEl.textContent = fund.aum_cr ? "₹" + Math.round(fund.aum_cr).toLocaleString() + " Cr" : "N/A";
  if (terEl) terEl.textContent = fund.direct_ter !== null && fund.direct_ter !== undefined ? fund.direct_ter.toFixed(2) + "%" : "N/A";

  if (msEl) {
    if (fund.morningstar_rating) {
      msEl.textContent = "★".repeat(fund.morningstar_rating);
    } else {
      msEl.textContent = "—";
    }
  }
  if (vrEl) {
    if (fund.valueresearch_rating) {
      vrEl.textContent = `${fund.valueresearch_rating} Stars`;
    } else {
      vrEl.textContent = "Not Rated";
    }
  }
  if (crisilEl) {
    crisilEl.textContent = fund.crisil_rank ? fund.crisil_rank : "Unranked";
  }
}

window.previewFundInInspector = function(schemeCode) {
  const fund = state.rawFunds.find((f) => f.scheme_code === schemeCode);
  if (fund) {
    updateSchemeInspector(fund);
  }
};

const CAT_CODES = {
  "Flexi Cap": "01 / FLX",
  "Large Cap": "02 / LRG",
  "Mid Cap": "03 / MID",
  "Small Cap": "04 / SML",
  "Large & Mid Cap": "05 / L&M",
  "Multi Cap": "06 / MLT",
  "ELSS (Tax Saving)": "07 / ELS",
  "Focused Fund": "08 / FCS",
  "Value & Contra": "09 / VAL",
  "Dividend Yield": "10 / DIV",
};

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
    const filtered = getFilteredFunds();
    if (filtered.length > 0) {
      updateSchemeInspector(filtered[0]);
    }
    if (state.showChart) {
      drawRiskReturnChart();
    }
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
  state.categories.forEach((cat, idx) => {
    const code = CAT_CODES[cat.name] || `${String(idx + 1).padStart(2, "0")}`;
    const btn = document.createElement("button");
    btn.className = `cat-tab-btn ${state.activeCategory === cat.name ? "active" : ""}`;
    btn.innerHTML = `<span style="font-family: var(--font-mono); font-size: 10px; color: var(--accent-brass);">${code}</span> ${cat.name} <span class="cat-tab-count">${cat.count}</span>`;
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
  const filtered = getFilteredFunds();
  if (filtered.length > 0) {
    updateSchemeInspector(filtered[0]);
  }
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

      // Direct TER
      const dirTer = fund.direct_ter !== null ? `${fund.direct_ter.toFixed(2)}%` : "N/A";

      return `
        <tr data-scheme-code="${fund.scheme_code}" onclick="openFundDrawer(${fund.scheme_code})" onmouseenter="previewFundInInspector(${fund.scheme_code})">
          <td class="col-rank">
            <span class="rank-badge ${medalClass}">${rank}</span>
          </td>
          <td class="col-scheme">
            <div class="scheme-name">${escapeHtml(fund.scheme_name)}</div>
            <div class="scheme-meta">
              <span class="tag-amc">${escapeHtml(fund.amc)}</span>
              ${fund.isin_growth ? `<span class="tag-isin" title="ISIN">${fund.isin_growth}</span>` : ""}
              ${fund.benchmark_name ? `<span class="tag-isin" style="color: var(--accent-brass);" title="Category Benchmark">${escapeHtml(fund.benchmark_name)}</span>` : ""}
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
              <div class="ret-primary">${ret3y} <span style="font-size:10px; color: var(--text-dim);">(3Y)</span></div>
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
              <span class="capture-primary ${fund.capture_ratio >= 1.0 ? "val-pos" : ""}">${capRatio}</span>
              <span class="capture-sub">Up/Dn: ${upDown}</span>
            </div>
          </td>
          <td class="col-ter">
            <div class="ter-direct">${dirTer}</div>
          </td>
          <td class="col-action" onclick="event.stopPropagation();">
            <button class="btn-row-details" onclick="openFundDrawer(${fund.scheme_code})">Inspect</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

// Get 5-6 Line Mutual Fund Summary
function getFundSummaryLines(fund) {
  if (Array.isArray(fund.summary_lines) && fund.summary_lines.length >= 5) {
    return fund.summary_lines;
  }
  if (fund.summary) {
    return fund.summary.split("\n").filter((l) => l.trim().length > 0);
  }
  const name = fund.scheme_name || "This fund";
  const cat = fund.category || "Equity";
  const bench = fund.benchmark_name || "NIFTY 500 TRI";
  const rank = fund.composite_rank ? `#${fund.composite_rank}` : "-";
  const score = fund.composite_score ? `${fund.composite_score.toFixed(1)}/100` : "N/A";
  const tier = fund.rating_tier || "Unrated";
  const ret3y = fund.return_3y_cagr !== null ? `${fund.return_3y_cagr.toFixed(2)}% CAGR` : "maturing";
  const ret1y = fund.return_1y !== null ? `${fund.return_1y.toFixed(2)}%` : "N/A";
  const vol = fund.standard_deviation !== null ? `${fund.standard_deviation.toFixed(2)}%` : "N/A";
  const beta = fund.beta !== null ? fund.beta.toFixed(2) : "N/A";
  const alpha = fund.alpha !== null ? `${fund.alpha >= 0 ? "+" : ""}${fund.alpha.toFixed(2)}%` : "N/A";
  const ter = fund.direct_ter !== null ? `${fund.direct_ter.toFixed(2)}%` : "N/A";
  const aum = fund.aum_cr ? `₹${Math.round(fund.aum_cr).toLocaleString()} Cr` : "N/A";

  return [
    `${name} is an open-ended ${cat} mutual fund offered by ${fund.amc || "AMC"}, benchmarked against ${bench}.`,
    `Under our multi-agency quantitative framework, the fund ranks ${rank} in the ${cat} peer group with a score of ${score} (${tier}).`,
    `In historical compounding, the fund recorded a 3-year return of ${ret3y} and 1-year return of ${ret1y}.`,
    `From a risk perspective, it displays an annualized volatility of ${vol} and market Beta of ${beta}.`,
    `Relative to ${bench}, the fund delivers a Jensen's Alpha of ${alpha} with capture ratio ${fund.capture_ratio || "N/A"}.`,
    `Assigned independent agency coverage, managing ${aum} in AUM with a Direct TER of ${ter}.`
  ];
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

  // Fund Executive Summary (5-6 Lines)
  const summaryLines = getFundSummaryLines(fund);
  const summaryHtml = summaryLines
    .map(
      (line, idx) => `
      <div class="summary-line-item">
        <span class="summary-line-num">${idx + 1}</span>
        <div class="summary-line-text">${escapeHtml(line)}</div>
      </div>
    `
    )
    .join("");

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

  const isAi = fund.summary_source && fund.summary_source.includes("gemini");
  const badgeText = isAi ? "✨ Gemini 2.0 Flash AI" : "Quantitative Analysis";

  content.innerHTML = `
    <!-- Fund Executive Summary Card (5-6 Lines) -->
    <div class="drawer-card fund-summary-card" id="drawer-summary-card">
      <div class="drawer-card-title">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span>Fund Executive Summary</span>
          <span class="summary-badge ${isAi ? "ai-badge" : ""}" id="drawer-summary-badge">${badgeText}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <button class="btn-generate-ai" id="btn-ai-regenerate" onclick="generateLiveGeminiSummary(${fund.scheme_code})" title="Generate dynamic live AI insights using Google Gemini">
            ⚡ Run Gemini AI
          </button>
          <button class="btn-key-settings" onclick="changeGeminiApiKey(event)" title="Configure or update saved Gemini API Key">
            ⚙️
          </button>
        </div>
      </div>
      <div class="fund-summary-body" id="drawer-summary-body">
        ${summaryHtml}
      </div>
    </div>

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

    <!-- Direct Plan Expense Ratio (TER) -->
    <div class="drawer-card">
      <div class="drawer-card-title">Direct Plan Expense Ratio (TER)</div>
      <div class="drawer-stats-row">
        <div class="d-stat-box">
          <div class="d-stat-label">Direct TER</div>
          <div class="d-stat-val" style="color: var(--accent-emerald);">${fund.direct_ter !== null ? fund.direct_ter.toFixed(2) + "%" : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Fund Scale (AUM)</div>
          <div class="d-stat-val">${fund.aum_cr ? "₹" + Math.round(fund.aum_cr).toLocaleString() + " Cr" : "N/A"}</div>
        </div>
        <div class="d-stat-box">
          <div class="d-stat-label">Plan Option</div>
          <div class="d-stat-val" style="color: #38bdf8; font-size: 13px; font-weight: 600;">Direct - Growth</div>
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

// Dynamic AUM Bubble Radius: Higher AUM is dramatically bigger, lower is smaller
function calculateBubbleRadius(aum, minAum, maxAum) {
  const safeAum = Math.max(aum || minAum, 20);
  const sqrtMin = Math.sqrt(Math.max(minAum, 20));
  const sqrtMax = Math.sqrt(Math.max(maxAum, 1000));
  const sqrtVal = Math.sqrt(safeAum);
  const fraction = Math.max(0, Math.min(1, (sqrtVal - sqrtMin) / (sqrtMax - sqrtMin || 1)));

  // Bubble size extremes: 4.5px for small boutique funds up to 28px for mega funds
  const minR = 4.5;
  const maxR = 28;
  return minR + fraction * (maxR - minR);
}

// Interactive Canvas-based Risk-Return Scatter Plot (2D & 3D)
let isChartInteractionsSetup = false;

function setupChartInteractions() {
  if (isChartInteractionsSetup) return;
  const canvas = document.getElementById("riskReturnCanvas");
  const tooltip = document.getElementById("chart-tooltip");
  const wrapper = document.getElementById("chart-canvas-wrapper");
  if (!canvas || !tooltip || !wrapper) return;

  isChartInteractionsSetup = true;

  function findPointAt(mouseX, mouseY) {
    if (!state.chartPoints || state.chartPoints.length === 0) return null;
    let closest = null;
    let minDistance = Infinity;

    for (const pt of state.chartPoints) {
      const px = state.chartViewMode === "3d" ? pt.screenX : pt.x;
      const py = state.chartViewMode === "3d" ? pt.screenY : pt.y;
      const pr = state.chartViewMode === "3d" ? pt.projectedR : pt.r;

      const dist = Math.hypot(px - mouseX, py - mouseY);
      const hitRadius = Math.max(pr + 8, 14);

      if (dist <= hitRadius) {
        if (state.chartViewMode === "3d") {
          // In 3D, pick nearest depth (foreground)
          if (!closest || pt.depth < closest.depth || (Math.abs(pt.depth - closest.depth) < 0.25 && dist < minDistance)) {
            minDistance = dist;
            closest = pt;
          }
        } else {
          if (dist < minDistance) {
            minDistance = dist;
            closest = pt;
          }
        }
      }
    }
    return closest;
  }

  // Mouse Down for 3D Drag Orbit
  canvas.addEventListener("mousedown", (e) => {
    if (state.chartViewMode === "3d") {
      state.camera3D.isDragging = true;
      state.camera3D.lastMouseX = e.clientX;
      state.camera3D.lastMouseY = e.clientY;
      canvas.style.cursor = "grabbing";
    }
  });

  window.addEventListener("mouseup", () => {
    if (state.camera3D.isDragging) {
      state.camera3D.isDragging = false;
      canvas.style.cursor = state.chartHoveredFund ? "pointer" : "default";
    }
  });

  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Handle 3D Drag Rotation
    if (state.chartViewMode === "3d" && state.camera3D.isDragging) {
      const dx = e.clientX - state.camera3D.lastMouseX;
      const dy = e.clientY - state.camera3D.lastMouseY;
      state.camera3D.yaw += dx * 0.008;
      state.camera3D.pitch = Math.max(-1.15, Math.min(1.15, state.camera3D.pitch + dy * 0.008));
      state.camera3D.lastMouseX = e.clientX;
      state.camera3D.lastMouseY = e.clientY;
      drawRiskReturnChart();
      tooltip.style.display = "none";
      return;
    }

    const hit = findPointAt(mouseX, mouseY);

    if (hit) {
      canvas.style.cursor = state.camera3D.isDragging ? "grabbing" : "pointer";
      if (!state.chartHoveredFund || state.chartHoveredFund.fund.scheme_code !== hit.fund.scheme_code) {
        state.chartHoveredFund = hit;
        drawRiskReturnChart();
      }
      updateChartTooltip(hit);
    } else {
      canvas.style.cursor = state.camera3D.isDragging ? "grabbing" : "default";
      if (state.chartHoveredFund !== null) {
        state.chartHoveredFund = null;
        drawRiskReturnChart();
        tooltip.style.display = "none";
      }
    }
  });

  canvas.addEventListener("mouseleave", () => {
    if (state.chartHoveredFund !== null) {
      state.chartHoveredFund = null;
      canvas.style.cursor = "default";
      drawRiskReturnChart();
      tooltip.style.display = "none";
    }
  });

  // Wheel Zoom in 3D
  canvas.addEventListener("wheel", (e) => {
    if (state.chartViewMode === "3d") {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      state.camera3D.zoom = Math.max(0.65, Math.min(2.4, state.camera3D.zoom * factor));
      drawRiskReturnChart();
    }
  }, { passive: false });

  // Bubble Click -> Open Detail Drawer
  canvas.addEventListener("click", (e) => {
    if (state.camera3D.isDragging) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const hit = findPointAt(mouseX, mouseY);
    if (hit && hit.fund && hit.fund.scheme_code) {
      openFundDrawer(hit.fund.scheme_code);
    }
  });
}

function updateChartTooltip(pt) {
  const tooltip = document.getElementById("chart-tooltip");
  const wrapper = document.getElementById("chart-canvas-wrapper");
  if (!tooltip || !wrapper || !pt || !pt.fund) return;

  const fund = pt.fund;
  updateSchemeInspector(fund);

  const horizon = state.chartHorizon || "3y";
  const horizonLabel = horizon === "1y" ? "1-Year Return" : "3-Year CAGR";
  const retVal = horizon === "1y" ? fund.return_1y : fund.return_3y_cagr;
  const isPos = retVal !== null && retVal >= 0;

  const dimCfg = THIRD_DIM_CONFIG[state.chartThirdDim] || THIRD_DIM_CONFIG.sharpe_ratio;
  const zFormatted = dimCfg.format(dimCfg.getVal(fund));

  const tier = fund.rating_tier || "Unrated";
  let tierClass = "below";
  let rankBadgeClass = "tier-bel";
  if (tier.includes("BEST")) {
    tierClass = "best";
    rankBadgeClass = "tier-best";
  } else if (tier.includes("Tier 2")) {
    tierClass = "superior";
    rankBadgeClass = "tier-sup";
  } else if (tier.includes("Tier 3")) {
    tierClass = "average";
    rankBadgeClass = "tier-avg";
  }

  tooltip.innerHTML = `
    <div class="chart-tooltip-header">
      <div class="chart-tooltip-rank-badge ${rankBadgeClass}">#${fund.composite_rank || "—"}</div>
      <div class="chart-tooltip-titles">
        <div class="chart-tooltip-name">${escapeHtml(fund.scheme_name)}</div>
        <div class="chart-tooltip-meta">${escapeHtml(fund.amc || "")} • Code: ${fund.scheme_code}</div>
      </div>
    </div>
    <div class="chart-tooltip-badge-row">
      <span class="chart-tooltip-tier-pill ${tierClass}">${escapeHtml(tier)}</span>
      <span class="chart-tooltip-score">Category Rank <strong>#${fund.composite_rank || "—"}</strong> (${fund.composite_score ? fund.composite_score.toFixed(1) : "N/A"}/100)</span>
    </div>
    <div class="chart-tooltip-metrics-grid">
      <div class="tooltip-metric-box">
        <span class="metric-box-label">${horizonLabel}</span>
        <span class="metric-box-val ${isPos ? "val-pos" : "val-neg"}">${formatPercent(retVal)}</span>
      </div>
      <div class="tooltip-metric-box">
        <span class="metric-box-label">Volatility (&sigma;)</span>
        <span class="metric-box-val">${fund.standard_deviation !== null ? fund.standard_deviation.toFixed(2) + "%" : "N/A"}</span>
      </div>
      <div class="tooltip-metric-box">
        <span class="metric-box-label">Z-Dim (${dimCfg.shortLabel})</span>
        <span class="metric-box-val" style="color: var(--accent-brass);">${zFormatted}</span>
      </div>
      <div class="tooltip-metric-box">
        <span class="metric-box-label">Live AUM (Size)</span>
        <span class="metric-box-val">₹${fund.aum_cr ? Math.round(fund.aum_cr).toLocaleString() : "N/A"} Cr</span>
      </div>
    </div>
    <div class="chart-tooltip-footer">
      <span>👆 Click bubble to open full scheme analysis</span>
    </div>
  `;

  tooltip.style.display = "block";

  const wrapperRect = wrapper.getBoundingClientRect();
  const ttWidth = tooltip.offsetWidth || 310;
  const ttHeight = tooltip.offsetHeight || 160;

  const posX = state.chartViewMode === "3d" ? pt.screenX : pt.x;
  const posY = state.chartViewMode === "3d" ? pt.screenY : pt.y;
  const posR = state.chartViewMode === "3d" ? pt.projectedR : pt.r;

  let left = posX + posR + 14;
  if (left + ttWidth > wrapperRect.width - 12) {
    left = posX - posR - ttWidth - 14;
  }
  if (left < 10) left = 10;

  let top = posY - ttHeight / 2;
  if (top + ttHeight > wrapperRect.height - 10) {
    top = wrapperRect.height - ttHeight - 10;
  }
  if (top < 10) top = 10;

  tooltip.style.left = `${Math.round(left)}px`;
  tooltip.style.top = `${Math.round(top)}px`;
}

function drawRiskReturnChart() {
  const canvas = document.getElementById("riskReturnCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  setupChartInteractions();

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;

  ctx.clearRect(0, 0, width, height);

  const horizon = state.chartHorizon || "3y";

  // Filter category funds with valid metrics
  const categoryFunds = state.rawFunds.filter((f) => {
    if (f.category !== state.activeCategory) return false;
    if (f.standard_deviation === null || f.standard_deviation === undefined) return false;
    const ret = horizon === "1y" ? f.return_1y : f.return_3y_cagr;
    return ret !== null && ret !== undefined;
  });

  const countBadge = document.getElementById("chart-plotted-count");
  if (countBadge) {
    countBadge.textContent = `${categoryFunds.length} schemes plotted`;
  }

  if (categoryFunds.length === 0) {
    state.chartPoints = [];
    ctx.fillStyle = "#94a3b8";
    ctx.font = "14px 'Plus Jakarta Sans', sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`No ${horizon.toUpperCase()} performance data available for this category`, width / 2, height / 2);
    return;
  }

  const isLight = document.documentElement.getAttribute("data-theme") === "light";

  if (state.chartViewMode === "3d") {
    draw3DChart(canvas, ctx, categoryFunds, horizon, width, height, isLight);
  } else {
    draw2DChart(canvas, ctx, categoryFunds, horizon, width, height, isLight);
  }
}

// 2D Bubble Scatter Plot with Enhanced AUM Extremes
function draw2DChart(canvas, ctx, categoryFunds, horizon, width, height, isLight) {
  let minVol = Infinity, maxVol = -Infinity;
  let minRet = Infinity, maxRet = -Infinity;
  let minAum = Infinity, maxAum = -Infinity;

  categoryFunds.forEach((f) => {
    const vol = f.standard_deviation;
    const ret = horizon === "1y" ? f.return_1y : f.return_3y_cagr;
    const aum = f.aum_cr || 100;
    if (vol < minVol) minVol = vol;
    if (vol > maxVol) maxVol = vol;
    if (ret < minRet) minRet = ret;
    if (ret > maxRet) maxRet = ret;
    if (aum < minAum) minAum = aum;
    if (aum > maxAum) maxAum = aum;
  });

  minVol = Math.max(0, Math.floor(minVol - 1));
  maxVol = Math.ceil(maxVol + 2);
  minRet = Math.floor(minRet - 2);
  maxRet = Math.ceil(maxRet + 2);

  if (maxVol <= minVol) maxVol = minVol + 5;
  if (maxRet <= minRet) maxRet = minRet + 5;

  const padding = { top: 35, right: 40, bottom: 50, left: 65 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  // Calculate Median Volatility & Return for quadrant lines
  const volValues = categoryFunds.map((f) => f.standard_deviation).sort((a, b) => a - b);
  const retValues = categoryFunds
    .map((f) => (horizon === "1y" ? f.return_1y : f.return_3y_cagr))
    .sort((a, b) => a - b);
  const medVol = volValues[Math.floor(volValues.length / 2)];
  const medRet = retValues[Math.floor(retValues.length / 2)];

  const medX = padding.left + ((medVol - minVol) / (maxVol - minVol)) * plotW;
  const medY = padding.top + plotH - ((medRet - minRet) / (maxRet - minRet)) * plotH;

  // Subtle Quadrant Shading & Divider Lines
  ctx.save();
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.12)" : "rgba(255, 255, 255, 0.10)";
  ctx.lineWidth = 1;

  if (medX >= padding.left && medX <= width - padding.right) {
    ctx.beginPath();
    ctx.moveTo(medX, padding.top);
    ctx.lineTo(medX, height - padding.bottom);
    ctx.stroke();
  }

  if (medY >= padding.top && medY <= height - padding.bottom) {
    ctx.beginPath();
    ctx.moveTo(padding.left, medY);
    ctx.lineTo(width - padding.right, medY);
    ctx.stroke();
  }
  ctx.restore();

  // Quadrant Annotation
  ctx.fillStyle = isLight ? "rgba(16, 185, 129, 0.55)" : "rgba(52, 211, 153, 0.4)";
  ctx.font = "600 11px 'Plus Jakarta Sans', sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("✨ Optimal Zone (High Return, Lower Volatility)", padding.left + 12, padding.top + 18);

  // Grid lines
  ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.07)" : "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  ctx.fillStyle = isLight ? "#64748b" : "#64748b";
  ctx.font = "11px 'JetBrains Mono', monospace";
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
    ctx.fillText(`${val > 0 ? "+" : ""}${val.toFixed(1)}%`, padding.left - 10, y + 4);
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
  ctx.font = "600 12px 'Plus Jakarta Sans', sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("Annualized Volatility / Standard Deviation (σ) → Higher Risk", padding.left + plotW / 2, height - 12);

  ctx.save();
  ctx.translate(18, padding.top + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  const yAxisTitle = horizon === "1y" ? "1-Year Return (%) → Higher Reward" : "3-Year CAGR Return (%) → Higher Reward";
  ctx.fillText(yAxisTitle, 0, 0);
  ctx.restore();

  // Compute point positions with dynamic AUM radius scaling
  const newPoints = [];
  categoryFunds.forEach((f) => {
    const vol = f.standard_deviation;
    const ret = horizon === "1y" ? f.return_1y : f.return_3y_cagr;
    const x = padding.left + ((vol - minVol) / (maxVol - minVol)) * plotW;
    const y = padding.top + plotH - ((ret - minRet) / (maxRet - minRet)) * plotH;

    // Enhanced AUM scaling: 4.5px to 28px
    const r = calculateBubbleRadius(f.aum_cr, minAum, maxAum);

    let color = "#64748b";
    const tier = f.rating_tier || "";
    if (tier.includes("BEST")) color = "#22c55e";
    else if (tier.includes("Tier 2")) color = "#c59b27";
    else if (tier.includes("Tier 3")) color = "#94a3b8";

    newPoints.push({
      fund: f,
      x,
      y,
      r,
      color,
      vol,
      ret,
      tier,
      rank: f.composite_rank,
    });
  });

  state.chartPoints = newPoints;

  // Check hover
  let hoveredPt = null;
  if (state.chartHoveredFund) {
    hoveredPt = state.chartPoints.find((p) => p.fund.scheme_code === state.chartHoveredFund.fund.scheme_code);
    if (!hoveredPt) {
      state.chartHoveredFund = null;
      const tooltip = document.getElementById("chart-tooltip");
      if (tooltip) tooltip.style.display = "none";
    }
  }

  const hasSearch = !!state.searchTerm;

  // CRITICAL: Sort by radius descending so larger bubbles are drawn in background, smaller bubbles on top!
  const sortedToDraw = [...state.chartPoints].sort((a, b) => b.r - a.r);

  // Draw Bubbles (Non-hovered first)
  sortedToDraw.forEach((p) => {
    if (hoveredPt && p.fund.scheme_code === hoveredPt.fund.scheme_code) return;

    let isMatch = true;
    if (hasSearch) {
      const name = (p.fund.scheme_name || "").toLowerCase();
      const amc = (p.fund.amc || "").toLowerCase();
      isMatch = name.includes(state.searchTerm) || amc.includes(state.searchTerm);
    }

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);

    let alpha = 0.68;
    if (hoveredPt) {
      alpha = 0.22;
    } else if (hasSearch) {
      alpha = isMatch ? 0.92 : 0.12;
    }

    ctx.fillStyle = p.color;
    ctx.globalAlpha = alpha;
    ctx.fill();

    ctx.lineWidth = isMatch && hasSearch ? 2.5 : (p.r > 15 ? 2.0 : 1.2);
    ctx.strokeStyle = isMatch && hasSearch ? "#38bdf8" : "#ffffff";
    ctx.globalAlpha = hoveredPt ? 0.35 : (hasSearch ? (isMatch ? 1.0 : 0.2) : 0.88);
    ctx.stroke();
    ctx.globalAlpha = 1.0;

    // Rank label in bubble if bubble is large enough (>= 9px)
    if ((!hoveredPt || isMatch) && p.rank && p.rank <= 3 && p.r >= 9) {
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 10px 'Plus Jakarta Sans', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`#${p.rank}`, p.x, p.y + 3.5);
    }
  });

  // Highlight Hovered Fund in 2D
  if (hoveredPt) {
    ctx.save();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = hoveredPt.color;
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.85;

    ctx.beginPath();
    ctx.moveTo(hoveredPt.x, hoveredPt.y);
    ctx.lineTo(hoveredPt.x, height - padding.bottom);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(hoveredPt.x, hoveredPt.y);
    ctx.lineTo(padding.left, hoveredPt.y);
    ctx.stroke();
    ctx.restore();

    // Axis coordinate callout badges
    const xBadgeText = `${hoveredPt.vol.toFixed(2)}% σ`;
    ctx.font = "bold 10.5px 'JetBrains Mono', monospace";
    const xBadgeW = ctx.measureText(xBadgeText).width + 12;
    ctx.fillStyle = isLight ? "#0f172a" : "#1e293b";
    ctx.beginPath();
    ctx.roundRect(hoveredPt.x - xBadgeW / 2, height - padding.bottom + 4, xBadgeW, 18, 4);
    ctx.fill();
    ctx.strokeStyle = hoveredPt.color;
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.fillText(xBadgeText, hoveredPt.x, height - padding.bottom + 17);

    const yBadgeText = `${hoveredPt.ret > 0 ? "+" : ""}${hoveredPt.ret.toFixed(2)}%`;
    const yBadgeW = ctx.measureText(yBadgeText).width + 12;
    ctx.fillStyle = isLight ? "#0f172a" : "#1e293b";
    ctx.beginPath();
    ctx.roundRect(padding.left - yBadgeW - 6, hoveredPt.y - 9, yBadgeW, 18, 4);
    ctx.fill();
    ctx.strokeStyle = hoveredPt.color;
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.fillText(yBadgeText, padding.left - yBadgeW / 2 - 6, hoveredPt.y + 4);

    // Outer Halo
    ctx.save();
    ctx.beginPath();
    ctx.arc(hoveredPt.x, hoveredPt.y, hoveredPt.r + 8, 0, Math.PI * 2);
    ctx.fillStyle = hoveredPt.color;
    ctx.globalAlpha = 0.25;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(hoveredPt.x, hoveredPt.y, hoveredPt.r + 4, 0, Math.PI * 2);
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2.5;
    ctx.globalAlpha = 0.95;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(hoveredPt.x, hoveredPt.y, hoveredPt.r + 1, 0, Math.PI * 2);
    ctx.fillStyle = hoveredPt.color;
    ctx.globalAlpha = 1.0;
    ctx.fill();
    ctx.restore();

    if (hoveredPt.r >= 8) {
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 11px 'Plus Jakarta Sans', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`#${hoveredPt.rank || ""}`, hoveredPt.x, hoveredPt.y + 4);
    }
  }
}

// 3D Perspective Orbit Scatter Plot
function draw3DChart(canvas, ctx, categoryFunds, horizon, width, height, isLight) {
  const dimCfg = THIRD_DIM_CONFIG[state.chartThirdDim] || THIRD_DIM_CONFIG.sharpe_ratio;

  let minVol = Infinity, maxVol = -Infinity;
  let minRet = Infinity, maxRet = -Infinity;
  let minZ = Infinity, maxZ = -Infinity;
  let minAum = Infinity, maxAum = -Infinity;

  categoryFunds.forEach((f) => {
    const vol = f.standard_deviation;
    const ret = horizon === "1y" ? f.return_1y : f.return_3y_cagr;
    const zVal = dimCfg.getVal(f);
    const aum = f.aum_cr || 100;

    if (vol < minVol) minVol = vol;
    if (vol > maxVol) maxVol = vol;
    if (ret < minRet) minRet = ret;
    if (ret > maxRet) maxRet = ret;
    if (zVal !== null && zVal !== undefined) {
      const numZ = Number(zVal);
      if (numZ < minZ) minZ = numZ;
      if (numZ > maxZ) maxZ = numZ;
    }
    if (aum < minAum) minAum = aum;
    if (aum > maxAum) maxAum = aum;
  });

  if (minZ === Infinity || maxZ === -Infinity) { minZ = 0; maxZ = 1; }
  if (minVol === maxVol) maxVol = minVol + 5;
  if (minRet === maxRet) maxRet = minRet + 5;
  if (minZ === maxZ) maxZ = minZ + 1;

  minVol = Math.max(0, minVol - 1);
  maxVol += 1.5;
  minRet -= 1.5;
  maxRet += 1.5;
  minZ -= (maxZ - minZ) * 0.08;
  maxZ += (maxZ - minZ) * 0.08;

  // 3D Projection function
  function project(x, y, z) {
    const cosY = Math.cos(state.camera3D.yaw);
    const sinY = Math.sin(state.camera3D.yaw);
    const cosP = Math.cos(state.camera3D.pitch);
    const sinP = Math.sin(state.camera3D.pitch);

    const x1 = x * cosY + z * sinY;
    const z1 = -x * sinY + z * cosY;

    const y2 = y * cosP - z1 * sinP;
    const z2 = y * sinP + z1 * cosP;

    const fov = 3.6 / state.camera3D.zoom;
    const camZ = z2 + fov;
    const perspective = fov / Math.max(camZ, 0.2);

    const scale = Math.min(width, height) * 0.38;
    const screenX = width / 2 + x1 * scale * perspective;
    const screenY = height / 2 - y2 * scale * perspective;

    return { screenX, screenY, depth: camZ, perspective };
  }

  // Draw 3D Floor Grid at Y = -1
  ctx.save();
  ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.12)" : "rgba(255, 255, 255, 0.12)";
  ctx.lineWidth = 1;
  const gridSteps = 4;

  for (let i = 0; i <= gridSteps; i++) {
    const t = -1 + (2 / gridSteps) * i;
    const pA = project(t, -1, -1);
    const pB = project(t, -1, 1);
    ctx.beginPath();
    ctx.moveTo(pA.screenX, pA.screenY);
    ctx.lineTo(pB.screenX, pB.screenY);
    ctx.stroke();

    const pC = project(-1, -1, t);
    const pD = project(1, -1, t);
    ctx.beginPath();
    ctx.moveTo(pC.screenX, pC.screenY);
    ctx.lineTo(pD.screenX, pD.screenY);
    ctx.stroke();
  }

  // 3D Axes
  ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.3)" : "rgba(255, 255, 255, 0.3)";
  ctx.lineWidth = 1.5;

  const axX0 = project(-1, -1, -1);
  const axX1 = project(1, -1, -1);
  ctx.beginPath();
  ctx.moveTo(axX0.screenX, axX0.screenY);
  ctx.lineTo(axX1.screenX, axX1.screenY);
  ctx.stroke();

  const axY0 = project(-1, -1, -1);
  const axY1 = project(-1, 1, -1);
  ctx.beginPath();
  ctx.moveTo(axY0.screenX, axY0.screenY);
  ctx.lineTo(axY1.screenX, axY1.screenY);
  ctx.stroke();

  const axZ0 = project(-1, -1, -1);
  const axZ1 = project(-1, -1, 1);
  ctx.beginPath();
  ctx.moveTo(axZ0.screenX, axZ0.screenY);
  ctx.lineTo(axZ1.screenX, axZ1.screenY);
  ctx.stroke();

  // 3D Axis Labels
  ctx.font = "bold 11px 'Plus Jakarta Sans', sans-serif";
  ctx.fillStyle = isLight ? "#1e293b" : "#94a3b8";

  const lblX = project(1.15, -1, -1);
  ctx.textAlign = "left";
  ctx.fillText("Volatility (σ) →", lblX.screenX, lblX.screenY);

  const lblY = project(-1, 1.15, -1);
  ctx.textAlign = "center";
  ctx.fillText(horizon === "1y" ? "1Y Return (%) ↑" : "3Y CAGR (%) ↑", lblY.screenX, lblY.screenY - 4);

  const lblZ = project(-1, -1, 1.18);
  ctx.textAlign = "right";
  ctx.fillText(`3rd Dim: ${dimCfg.shortLabel} ↗`, lblZ.screenX, lblZ.screenY);
  ctx.restore();

  // Project all funds into 3D
  const points3D = [];
  categoryFunds.forEach((f) => {
    const vol = f.standard_deviation;
    const ret = horizon === "1y" ? f.return_1y : f.return_3y_cagr;
    let zVal = dimCfg.getVal(f);
    if (zVal === null || zVal === undefined) zVal = (minZ + maxZ) / 2;

    const normX = ((vol - minVol) / (maxVol - minVol)) * 2 - 1;
    const normY = ((ret - minRet) / (maxRet - minRet)) * 2 - 1;
    const normZ = ((zVal - minZ) / (maxZ - minZ)) * 2 - 1;

    const baseR = calculateBubbleRadius(f.aum_cr, minAum, maxAum);
    const proj = project(normX, normY, normZ);
    const floorProj = project(normX, -1, normZ);

    let color = "#64748b";
    const tier = f.rating_tier || "";
    if (tier.includes("BEST")) color = "#22c55e";
    else if (tier.includes("Tier 2")) color = "#c59b27";
    else if (tier.includes("Tier 3")) color = "#94a3b8";

    points3D.push({
      fund: f,
      normX,
      normY,
      normZ,
      vol,
      ret,
      zVal,
      screenX: proj.screenX,
      screenY: proj.screenY,
      depth: proj.depth,
      projectedR: Math.max(3.5, baseR * proj.perspective),
      baseR,
      floorX: floorProj.screenX,
      floorY: floorProj.screenY,
      color,
      tier,
      rank: f.composite_rank,
    });
  });

  state.chartPoints = points3D;

  let hoveredPt = null;
  if (state.chartHoveredFund) {
    hoveredPt = state.chartPoints.find((p) => p.fund.scheme_code === state.chartHoveredFund.fund.scheme_code);
    if (!hoveredPt) {
      state.chartHoveredFund = null;
      const tooltip = document.getElementById("chart-tooltip");
      if (tooltip) tooltip.style.display = "none";
    }
  }

  // Painter's Algorithm: render from farthest to nearest
  const renderList = [...points3D].sort((a, b) => b.depth - a.depth);
  const hasSearch = !!state.searchTerm;

  renderList.forEach((p) => {
    const isHovered = hoveredPt && p.fund.scheme_code === hoveredPt.fund.scheme_code;

    let isMatch = true;
    if (hasSearch) {
      const name = (p.fund.scheme_name || "").toLowerCase();
      const amc = (p.fund.amc || "").toLowerCase();
      isMatch = name.includes(state.searchTerm) || amc.includes(state.searchTerm);
    }

    // Drop line to floor
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(p.screenX, p.screenY);
    ctx.lineTo(p.floorX, p.floorY);
    ctx.strokeStyle = isHovered ? p.color : (isLight ? "rgba(15, 23, 42, 0.15)" : "rgba(255, 255, 255, 0.15)");
    ctx.setLineDash(isHovered ? [2, 2] : [1, 3]);
    ctx.lineWidth = isHovered ? 1.5 : 1;
    ctx.stroke();

    // Floor shadow disc
    ctx.beginPath();
    ctx.ellipse(p.floorX, p.floorY, p.projectedR * 0.7, p.projectedR * 0.35, 0, 0, Math.PI * 2);
    ctx.fillStyle = isLight ? "rgba(0, 0, 0, 0.08)" : "rgba(0, 0, 0, 0.35)";
    ctx.fill();
    ctx.restore();

    // 3D Sphere / Orb with radial specular highlight
    ctx.save();
    ctx.beginPath();
    const drawR = isHovered ? p.projectedR + 3 : p.projectedR;
    ctx.arc(p.screenX, p.screenY, drawR, 0, Math.PI * 2);

    const grad = ctx.createRadialGradient(
      p.screenX - drawR * 0.35,
      p.screenY - drawR * 0.35,
      drawR * 0.1,
      p.screenX,
      p.screenY,
      drawR
    );
    grad.addColorStop(0, "#ffffff");
    grad.addColorStop(0.3, p.color);
    grad.addColorStop(1, isLight ? "#0f172a" : "#020617");

    let alpha = 0.85;
    if (hoveredPt && !isHovered) alpha = 0.22;
    else if (hasSearch && !isMatch) alpha = 0.12;

    ctx.globalAlpha = alpha;
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.lineWidth = isHovered ? 2.5 : 1.2;
    ctx.strokeStyle = isHovered ? "#ffffff" : (isMatch && hasSearch ? "#38bdf8" : "rgba(255, 255, 255, 0.7)");
    ctx.stroke();
    ctx.restore();

    if ((!hoveredPt || isHovered || isMatch) && p.rank && p.rank <= 3 && p.projectedR >= 8) {
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 10px 'Plus Jakarta Sans', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`#${p.rank}`, p.screenX, p.screenY + 3.5);
    }
  });

  // 3D Hover highlight
  if (hoveredPt) {
    ctx.save();
    ctx.beginPath();
    ctx.arc(hoveredPt.screenX, hoveredPt.screenY, hoveredPt.projectedR + 8, 0, Math.PI * 2);
    ctx.fillStyle = hoveredPt.color;
    ctx.globalAlpha = 0.3;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(hoveredPt.screenX, hoveredPt.screenY, hoveredPt.projectedR + 4, 0, Math.PI * 2);
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();
  }
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
  if (!score) return "var(--border-hairline)";
  if (score >= 75) return "var(--accent-emerald)";
  if (score >= 60) return "var(--accent-brass)";
  if (score >= 45) return "#94a3b8";
  return "var(--accent-crimson)";
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

// Normalize user model name or slug into API-compatible slug
function normalizeGeminiModel(input) {
  if (!input || typeof input !== "string") return "gemini-3.1-pro";
  const trimmed = input.trim();
  const lower = trimmed.toLowerCase();
  if (lower.includes("nano") && lower.includes("banana")) {
    return "nano-banana-2-lite";
  }
  return lower.replace(/[\(\)]/g, "").trim().replace(/\s+/g, "-");
}

// Ordered fallback models in requested priority sequence
const FALLBACK_CANDIDATE_MODELS = [
  "gemini-3.1-pro",
  "gemini-3.1-flash-lite",
  "gemini-3.5-flash-lite",
  "gemini-3.8-flash-lite-tts",
  "nano-banana-2-lite",
  "gemini-3.1-flash-lite-image",
  "gemini-3.5-flash",
  "gemini-3.6-flash",
  "gemini-3.7-flash",
  "gemini-3.8-flash",
  "gemini-3.1-flash",
  "gemini-3-pro",
  "gemini-3-flash",
  "gemini-2.5-pro",
  "gemini-2.5-flash",
  "gemini-2.0-flash",
  "gemini-1.5-flash"
];

// Get user-configured or default Gemini model
function getSavedGeminiModel() {
  const custom = localStorage.getItem("mf_gemini_model");
  if (custom && custom.trim()) {
    return normalizeGeminiModel(custom);
  }
  return "gemini-3.1-pro";
}

// Configure or update saved Gemini API Key & Model
function changeGeminiApiKey(event) {
  if (event) event.stopPropagation();
  const currentKey = localStorage.getItem("mf_gemini_api_key") || "";
  const currentModel = getSavedGeminiModel();

  const newKey = prompt(
    "Enter your Google Gemini API Key\n(Get a free key at https://aistudio.google.com/):",
    currentKey
  );
  if (newKey !== null) {
    if (newKey.trim()) {
      localStorage.setItem("mf_gemini_api_key", newKey.trim());
      const newModel = prompt(
        "Enter your Gemini Model Name (e.g. gemini-3.1-pro, gemini-3.1-flash-lite, gemini-3.5-flash, gemini-3.8-flash):",
        currentModel
      );
      if (newModel && newModel.trim()) {
        const cleaned = normalizeGeminiModel(newModel);
        localStorage.setItem("mf_gemini_model", cleaned);
      }
      sessionStorage.removeItem("mf_resolved_gemini_model");
      alert("✅ Saved! Model set to " + getSavedGeminiModel() + ". You can now click '⚡ Run Gemini AI'.");
    } else {
      localStorage.removeItem("mf_gemini_api_key");
      sessionStorage.removeItem("mf_resolved_gemini_model");
      alert("API Key removed from browser storage.");
    }
  }
}

// Dynamically resolve the best active Gemini model supported by the user's API key
async function resolveGeminiModel(apiKey) {
  const cachedModel = sessionStorage.getItem("mf_resolved_gemini_model");
  if (cachedModel) return cachedModel;

  const userModel = getSavedGeminiModel();
  const candidateModels = [
    userModel,
    ...FALLBACK_CANDIDATE_MODELS,
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro"
  ].filter((m, i, arr) => m && arr.indexOf(m) === i);

  try {
    const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
    if (resp.ok) {
      const data = await resp.json();
      const availableModels = data.models || [];

      // Check if user's configured model or any candidate is available
      for (const cand of candidateModels) {
        const candNorm = cand.toLowerCase().replace(/[\s\(\)\-_]/g, "");
        const matched = availableModels.find((m) => {
          const apiName = (m.name || "").replace("models/", "");
          const apiNorm = apiName.toLowerCase().replace(/[\s\(\)\-_]/g, "");
          const dispNorm = (m.displayName || "").toLowerCase().replace(/[\s\(\)\-_]/g, "");
          const methods = m.supportedGenerationMethods || [];
          const canGenerate = methods.length === 0 || methods.includes("generateContent");
          return (
            canGenerate &&
            (apiName === cand ||
             apiNorm === candNorm ||
             dispNorm === candNorm ||
             apiNorm.includes(candNorm) ||
             dispNorm.includes(candNorm))
          );
        });

        if (matched) {
          const actualName = (matched.name || "").replace("models/", "");
          sessionStorage.setItem("mf_resolved_gemini_model", actualName);
          return actualName;
        }
      }

      // Check for any 3.x, 2.x, or flash model
      const anyModern = availableModels.find((m) => {
        const name = (m.name || "").toLowerCase();
        return name.includes("gemini-3") || name.includes("gemini-2") || name.includes("flash");
      });
      if (anyModern) {
        const actualName = (anyModern.name || "").replace("models/", "");
        sessionStorage.setItem("mf_resolved_gemini_model", actualName);
        return actualName;
      }

      if (availableModels.length > 0) {
        const actualName = (availableModels[0].name || "").replace("models/", "");
        sessionStorage.setItem("mf_resolved_gemini_model", actualName);
        return actualName;
      }
    }
  } catch (e) {
    console.warn("Unable to query ListModels, falling back to candidates", e);
  }

  return userModel;
}

// Live Dynamic AI Summary Generator via Google Gemini API
async function generateLiveGeminiSummary(schemeCode) {
  const fund = state.rawFunds.find((f) => f.scheme_code === schemeCode);
  if (!fund) return;

  let apiKey = localStorage.getItem("mf_gemini_api_key");
  if (!apiKey) {
    apiKey = prompt("Enter your Google Gemini API Key:\n(Get a free key at: https://aistudio.google.com/)");
    if (!apiKey || !apiKey.trim()) return;
    apiKey = apiKey.trim();
    localStorage.setItem("mf_gemini_api_key", apiKey);

    const modelChoice = prompt(
      "Enter your Gemini Model Name (Default: gemini-3.1-pro):\n(Fallbacks: gemini-3.1-flash-lite, gemini-3.5-flash, gemini-3.8-flash...)",
      "gemini-3.1-pro"
    );
    if (modelChoice && modelChoice.trim()) {
      localStorage.setItem("mf_gemini_model", normalizeGeminiModel(modelChoice));
    }
  }

  const badgeEl = document.getElementById("drawer-summary-badge");
  const bodyEl = document.getElementById("drawer-summary-body");
  const btnEl = document.getElementById("btn-ai-regenerate");
  const activeModel = getSavedGeminiModel();

  if (btnEl) btnEl.disabled = true;
  if (badgeEl) {
    badgeEl.textContent = "✨ Generating...";
    badgeEl.classList.add("ai-badge");
  }
  if (bodyEl) {
    bodyEl.innerHTML = `
      <div style="padding: 20px; text-align: center; color: #38bdf8; font-size: 13px;">
        <span style="display:inline-block; animation: pulse 1s infinite;">✨</span> Calling Google Gemini (${escapeHtml(activeModel)}) for live quantitative insights...
      </div>
    `;
  }

  try {
    const promptText = `You are a Senior Quantitative Mutual Fund Research Analyst specializing in Indian equity mutual funds (SEBI framework).
Analyze the provided fund metrics and produce EXACTLY 5 or 6 concise, data-driven, institutional research summary lines.
Ground every line in the metrics provided. Do not mention regular plan expense ratios, commissions, or distributor fees.
Output format: Strict JSON with key "summary_lines" containing an array of 5 or 6 strings.

Fund Metrics:
${JSON.stringify({
  scheme_name: fund.scheme_name,
  amc: fund.amc,
  category: fund.category,
  benchmark: fund.benchmark_name,
  rank: fund.composite_rank,
  score: fund.composite_score,
  tier: fund.rating_tier,
  return_3y: fund.return_3y_cagr,
  return_1y: fund.return_1y,
  volatility: fund.standard_deviation,
  beta: fund.beta,
  alpha: fund.alpha,
  sharpe: fund.sharpe_ratio,
  sortino: fund.sortino_ratio,
  upside_capture: fund.upside_capture,
  downside_capture: fund.downside_capture,
  ratings: {
    ms: fund.morningstar_rating,
    vr: fund.valueresearch_rating,
    crisil: fund.crisil_rank,
    of: fund.one_finance_score
  },
  direct_ter: fund.direct_ter,
  aum_cr: fund.aum_cr
}, null, 2)}`;

    // Resolve model or try candidates sequentially to prevent 404
    const resolvedModel = await resolveGeminiModel(apiKey);
    const candidateModels = [
      activeModel,
      resolvedModel,
      ...FALLBACK_CANDIDATE_MODELS
    ].filter((m, i, arr) => m && arr.indexOf(m) === i);

    let successData = null;
    let usedModel = activeModel;
    let lastError = null;

    for (const model of candidateModels) {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
      try {
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ parts: [{ text: promptText }] }],
            generationConfig: {
              temperature: 0.2,
              responseMimeType: "application/json"
            }
          })
        });

        if (resp.ok) {
          successData = await resp.json();
          usedModel = model;
          sessionStorage.setItem("mf_resolved_gemini_model", model);
          break;
        }

        const errBody = await resp.json().catch(() => null);
        const errMsg = errBody?.error?.message || `HTTP ${resp.status}`;

        if (resp.status === 404) {
          // Model not found for this key/region, try next candidate
          lastError = `Model ${model} not found (${errMsg})`;
          continue;
        } else if (resp.status === 400 || resp.status === 403) {
          localStorage.removeItem("mf_gemini_api_key");
          sessionStorage.removeItem("mf_resolved_gemini_model");
          throw new Error(`Authentication/Permission Failed: ${errMsg}\nPlease verify your key at https://aistudio.google.com/`);
        } else {
          lastError = errMsg;
        }
      } catch (reqErr) {
        if (reqErr.message && reqErr.message.includes("Authentication/Permission Failed")) {
          throw reqErr;
        }
        lastError = reqErr.message;
      }
    }

    if (!successData) {
      throw new Error(
        lastError || "Could not connect to an active Gemini model. Please check that Generative Language API is enabled for your key at https://aistudio.google.com/"
      );
    }

    const candidateText = successData.candidates?.[0]?.content?.parts?.[0]?.text;
    const parsed = JSON.parse(candidateText);
    const lines = parsed.summary_lines;

    if (Array.isArray(lines) && lines.length >= 5) {
      fund.summary_lines = lines;
      fund.summary = lines.join("\n");
      fund.summary_source = usedModel;

      const modelDisplayName = usedModel.replace("gemini-", "").replace("-latest", "");
      if (badgeEl) {
        badgeEl.textContent = `✨ Gemini ${modelDisplayName} AI`;
        badgeEl.classList.add("ai-badge");
      }
      if (bodyEl) {
        bodyEl.innerHTML = lines
          .map(
            (l, i) => `
          <div class="summary-line-item">
            <span class="summary-line-num">${i + 1}</span>
            <div class="summary-line-text">${escapeHtml(l)}</div>
          </div>
        `
          )
          .join("");
      }
    } else {
      throw new Error("Unexpected format returned from Gemini model.");
    }
  } catch (err) {
    alert("Gemini AI Notice: " + err.message);
    const defaultLines = getFundSummaryLines(fund);
    if (bodyEl) {
      bodyEl.innerHTML = defaultLines
        .map(
          (l, i) => `
        <div class="summary-line-item">
          <span class="summary-line-num">${i + 1}</span>
          <div class="summary-line-text">${escapeHtml(l)}</div>
        </div>
      `
        )
        .join("");
    }
    if (badgeEl) {
      badgeEl.textContent = `${defaultLines.length} Core Insights`;
      badgeEl.classList.remove("ai-badge");
    }
  } finally {
    if (btnEl) btnEl.disabled = false;
  }
}


