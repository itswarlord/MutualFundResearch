"""
analytics.py - Calculates returns, risk-adjusted performance ratios, and CAPM benchmark metrics.

Metrics implemented:
- 1M, 3M, 6M, 1Y Absolute Returns (%)
- 2Y, 3Y, 5Y CAGR (Compound Annual Growth Rate) (%)
- Standard Deviation (3-Year Annualized Volatility) (%)
- Sharpe Ratio (3-Year, default Rf = 7.0% - India 10Y Benchmark G-Sec Yield)
- Sortino Ratio (3-Year, Downside Volatility penalization)
- Maximum Drawdown (3-Year Peak-to-Trough Decline) (%)
- Beta (Covariance with Benchmark / Variance of Benchmark)
- R-Squared (Percentage of fund variance explained by Benchmark)
- Alpha (Jensen's Alpha annualized excess return via CAPM)
- Upside Capture Ratio (%)
- Downside Capture Ratio (%)
- Overall Capture Ratio (Upside Capture / Downside Capture)
"""

import datetime
import math
from typing import Dict, List, Optional, Tuple

RISK_FREE_RATE_DEFAULT = 7.0  # 7.0% per annum (approx Indian 10-Yr Benchmark G-Sec Yield)
BENCHMARK_SCHEME_CODE = 147625  # Motilal Oswal Nifty 500 Index Fund (Direct Growth)

# SEBI Mandated Tier 1 Category Benchmarks and their corresponding high-liquidity Index Fund proxies on AMFI/MFAPI
CATEGORY_BENCHMARKS = {
    "Large Cap": {
        "name": "NIFTY 100",
        "description": "NIFTY 100 TRI",
        "scheme_code": 147666,  # Axis Nifty 100 Index Fund - Direct Plan - Growth Option
        "fallback_code": 147625,
    },
    "Mid Cap": {
        "name": "NIFTY Midcap 150",
        "description": "NIFTY Midcap 150 TRI",
        "scheme_code": 147622,  # Motilal Oswal Nifty Midcap 150 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Small Cap": {
        "name": "NIFTY Smallcap 250",
        "description": "NIFTY Smallcap 250 TRI",
        "scheme_code": 147623,  # Motilal Oswal Nifty Smallcap 250 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Flexi Cap": {
        "name": "NIFTY 500",
        "description": "NIFTY 500 TRI",
        "scheme_code": 147625,  # Motilal Oswal Nifty 500 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Multi Cap": {
        "name": "NIFTY 500 Multicap 50:25:25",
        "description": "NIFTY 500 Multicap 50:25:25 TRI",
        "scheme_code": 152751,  # Navi Nifty 500 Multicap 50:25:25 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Large & Mid Cap": {
        "name": "NIFTY LargeMidcap 250",
        "description": "NIFTY LargeMidcap 250 TRI",
        "scheme_code": 149343,  # Edelweiss NIFTY Large Midcap 250 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "ELSS": {
        "name": "NIFTY 500",
        "description": "NIFTY 500 TRI",
        "scheme_code": 147625,  # Motilal Oswal Nifty 500 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Focused Fund": {
        "name": "NIFTY 500",
        "description": "NIFTY 500 TRI",
        "scheme_code": 147625,  # Motilal Oswal Nifty 500 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Value & Contra": {
        "name": "NIFTY 500",
        "description": "NIFTY 500 TRI",
        "scheme_code": 147625,  # Motilal Oswal Nifty 500 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Dividend Yield": {
        "name": "NIFTY 500",
        "description": "NIFTY 500 TRI",
        "scheme_code": 147625,  # Motilal Oswal Nifty 500 Index Fund - Direct Plan - Growth
        "fallback_code": 147625,
    },
    "Sectoral & Thematic": {
        "name": "NIFTY 500",
        "description": "NIFTY 500 TRI",
        "scheme_code": 147625,
        "fallback_code": 147625,
    },
}

DEFAULT_BENCHMARK = {
    "name": "NIFTY 500",
    "description": "NIFTY 500 TRI",
    "scheme_code": 147625,
    "fallback_code": 147625,
}


def get_category_benchmark_info(category: Optional[str]) -> Dict:
    """Returns the benchmark name, scheme code, and fallback for a given mutual fund category."""
    if not category:
        return DEFAULT_BENCHMARK
    return CATEGORY_BENCHMARKS.get(category, DEFAULT_BENCHMARK)


def get_all_benchmark_scheme_codes(categories: Optional[List[str]] = None) -> List[int]:
    """Returns all unique scheme codes needed to fetch benchmark histories."""
    codes = set()
    target_cats = categories if categories else list(CATEGORY_BENCHMARKS.keys())
    for cat in target_cats:
        info = get_category_benchmark_info(cat)
        codes.add(info["scheme_code"])
        if info.get("fallback_code"):
            codes.add(info["fallback_code"])
    return sorted(list(codes))


def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parses date string in 'DD-MM-YYYY' or 'YYYY-MM-DD' format."""
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def calculate_metrics(
    nav_history: List[Dict],
    risk_free_rate: float = RISK_FREE_RATE_DEFAULT
) -> Dict[str, Optional[float]]:
    """
    Computes standard performance and risk metrics from raw historical NAV series.
    """
    if not nav_history:
        return {}

    # Sort chronological (oldest to newest)
    clean_history: List[Tuple[datetime.date, float]] = []
    for item in nav_history:
        d = parse_date(item.get("date", ""))
        try:
            nav = float(item.get("nav", 0.0))
            if d and nav > 0:
                clean_history.append((d, nav))
        except (ValueError, TypeError):
            continue

    clean_history.sort(key=lambda x: x[0])
    if not clean_history:
        return {}

    latest_date, latest_nav = clean_history[-1]
    inception_date, inception_nav = clean_history[0]

    def find_nav_prior_to(target_dt: datetime.date) -> Tuple[Optional[float], Optional[datetime.date]]:
        for d, nav in reversed(clean_history):
            if d <= target_dt:
                return nav, d
        return None, None

    metrics: Dict[str, Optional[float]] = {
        "latest_nav": round(latest_nav, 4),
        "as_of_date": latest_date.isoformat(),
        "inception_date": inception_date.isoformat(),
    }

    # Inception CAGR
    total_days = (latest_date - inception_date).days
    if total_days >= 365:
        years = total_days / 365.25
        metrics["return_inception_cagr"] = round(((latest_nav / inception_nav) ** (1.0 / years) - 1.0) * 100, 2)
    else:
        metrics["return_inception_cagr"] = None

    # Intervals: (key, days, is_cagr)
    return_intervals = [
        ("return_1m", 30, False),
        ("return_3m", 91, False),
        ("return_6m", 182, False),
        ("return_1y", 365, False),
        ("return_2y_cagr", 730, True),
        ("return_3y_cagr", 1095, True),
        ("return_5y_cagr", 1825, True),
    ]

    for key, days, is_cagr in return_intervals:
        target = latest_date - datetime.timedelta(days=days)
        past_nav, actual_dt = find_nav_prior_to(target)

        if past_nav and actual_dt and (latest_date - actual_dt).days >= int(days * 0.85):
            actual_days = (latest_date - actual_dt).days
            if is_cagr and actual_days >= 365:
                years = actual_days / 365.25
                cagr = ((latest_nav / past_nav) ** (1.0 / years) - 1.0) * 100.0
                metrics[key] = round(cagr, 2)
            else:
                abs_ret = ((latest_nav - past_nav) / past_nav) * 100.0
                metrics[key] = round(abs_ret, 2)
        else:
            metrics[key] = None

    # Risk Metrics calculated over trailing 3 Years (~750 trading days)
    three_yr_cutoff = latest_date - datetime.timedelta(days=1095)
    three_yr_data = [nav for d, nav in clean_history if d >= three_yr_cutoff]

    if len(three_yr_data) >= 250:
        daily_returns = [
            (three_yr_data[i] - three_yr_data[i - 1]) / three_yr_data[i - 1]
            for i in range(1, len(three_yr_data))
        ]

        # 1. Standard Deviation (Annualized Volatility)
        mean_ret = sum(daily_returns) / len(daily_returns)
        var = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_std = math.sqrt(var)
        ann_volatility = daily_std * math.sqrt(252) * 100.0
        metrics["volatility_3y"] = round(ann_volatility, 2)
        metrics["standard_deviation"] = round(ann_volatility, 2)

        # 2. Sharpe Ratio = (3Y CAGR - Risk Free Rate) / Annualized Volatility
        ret_3y = metrics.get("return_3y_cagr")
        if ret_3y is not None and ann_volatility > 0:
            metrics["sharpe_3y"] = round((ret_3y - risk_free_rate) / ann_volatility, 2)
        else:
            metrics["sharpe_3y"] = None

        # 3. Sortino Ratio = (3Y CAGR - Risk Free Rate) / Downside Deviation
        downside_returns = [r for r in daily_returns if r < 0]
        if downside_returns:
            downside_var = sum(r ** 2 for r in downside_returns) / len(daily_returns)
            downside_dev = math.sqrt(downside_var) * math.sqrt(252) * 100.0
            if downside_dev > 0 and ret_3y is not None:
                metrics["sortino_3y"] = round((ret_3y - risk_free_rate) / downside_dev, 2)
            else:
                metrics["sortino_3y"] = None
        else:
            metrics["sortino_3y"] = None

        # 4. Maximum Drawdown
        peak = three_yr_data[0]
        max_dd = 0.0
        for val in three_yr_data:
            if val > peak:
                peak = val
            dd = (peak - val) / peak
            if dd > max_dd:
                max_dd = dd
        metrics["max_drawdown_3y"] = round(max_dd * 100.0, 2)
    else:
        metrics["volatility_3y"] = None
        metrics["standard_deviation"] = None
        metrics["sharpe_3y"] = None
        metrics["sortino_3y"] = None
        metrics["max_drawdown_3y"] = None

    return metrics


def calculate_benchmark_metrics(
    fund_history: List[Dict],
    bench_history: List[Dict],
    risk_free_rate: float = RISK_FREE_RATE_DEFAULT
) -> Dict[str, Optional[float]]:
    """
    Computes Beta, Alpha, R-Squared, Upside Capture Ratio, and Downside Capture Ratio
    relative to the Nifty 500 Benchmark over a 3-year analysis window.
    """
    results: Dict[str, Optional[float]] = {
        "beta": None,
        "r_squared": None,
        "alpha": None,
        "upside_capture": None,
        "downside_capture": None,
        "capture_ratio": None,
    }

    if not fund_history or not bench_history:
        return results

    # Convert to date -> nav maps
    f_map = {}
    for item in fund_history:
        d = parse_date(item.get("date", ""))
        try:
            n = float(item.get("nav", 0.0))
            if d and n > 0:
                f_map[d] = n
        except (ValueError, TypeError):
            continue

    b_map = {}
    for item in bench_history:
        d = parse_date(item.get("date", ""))
        try:
            n = float(item.get("nav", 0.0))
            if d and n > 0:
                b_map[d] = n
        except (ValueError, TypeError):
            continue

    # Common dates
    common_dates = sorted(list(set(f_map.keys()) & set(b_map.keys())))
    if not common_dates:
        return results

    latest_date = common_dates[-1]
    three_yr_ago = latest_date - datetime.timedelta(days=1095)
    analysis_dates = [d for d in common_dates if d >= three_yr_ago]

    # Need at least ~250 trading days for statistical validity
    if len(analysis_dates) < 250:
        return results

    # 1. Daily Returns Series
    f_navs = [f_map[d] for d in analysis_dates]
    b_navs = [b_map[d] for d in analysis_dates]

    f_rets = [(f_navs[i] - f_navs[i - 1]) / f_navs[i - 1] for i in range(1, len(analysis_dates))]
    b_rets = [(b_navs[i] - b_navs[i - 1]) / b_navs[i - 1] for i in range(1, len(analysis_dates))]

    N = len(f_rets)
    f_mean = sum(f_rets) / N
    b_mean = sum(b_rets) / N

    cov = sum((f_rets[i] - f_mean) * (b_rets[i] - b_mean) for i in range(N)) / (N - 1)
    var_b = sum((b_rets[i] - b_mean) ** 2 for i in range(N)) / (N - 1)
    var_f = sum((f_rets[i] - f_mean) ** 2 for i in range(N)) / (N - 1)

    # Beta
    beta = cov / var_b if var_b > 0 else 1.0
    results["beta"] = round(beta, 2)

    # R-Squared
    if var_f > 0 and var_b > 0:
        corr = cov / (math.sqrt(var_f) * math.sqrt(var_b))
        r2 = corr ** 2
        results["r_squared"] = round(r2, 4)
    else:
        results["r_squared"] = None

    # Jensen's Alpha: Fund CAGR - [Rf + Beta * (Benchmark CAGR - Rf)]
    actual_years = (analysis_dates[-1] - analysis_dates[0]).days / 365.25
    if actual_years >= 1.0:
        cagr_f = ((f_navs[-1] / f_navs[0]) ** (1.0 / actual_years) - 1.0) * 100.0
        cagr_b = ((b_navs[-1] / b_navs[0]) ** (1.0 / actual_years) - 1.0) * 100.0
        alpha = cagr_f - (risk_free_rate + beta * (cagr_b - risk_free_rate))
        results["alpha"] = round(alpha, 2)

    # 2. Capture Ratios (Monthly Morningstar Method)
    monthly_f = {}
    monthly_b = {}
    for d in analysis_dates:
        key = (d.year, d.month)
        monthly_f[key] = f_map[d]
        monthly_b[key] = b_map[d]

    sorted_months = sorted(list(monthly_f.keys()))
    if len(sorted_months) >= 12:
        f_m_rets = [
            (monthly_f[sorted_months[i]] - monthly_f[sorted_months[i - 1]]) / monthly_f[sorted_months[i - 1]]
            for i in range(1, len(sorted_months))
        ]
        b_m_rets = [
            (monthly_b[sorted_months[i]] - monthly_b[sorted_months[i - 1]]) / monthly_b[sorted_months[i - 1]]
            for i in range(1, len(sorted_months))
        ]

        up_f, up_b = 1.0, 1.0
        down_f, down_b = 1.0, 1.0
        up_count, down_count = 0, 0

        for rf, rb in zip(f_m_rets, b_m_rets):
            if rb > 0:
                up_f *= (1.0 + rf)
                up_b *= (1.0 + rb)
                up_count += 1
            elif rb < 0:
                down_f *= (1.0 + rf)
                down_b *= (1.0 + rb)
                down_count += 1

        up_ret_f_ann = (up_f ** (12.0 / up_count)) - 1.0 if up_count > 0 else 0
        up_ret_b_ann = (up_b ** (12.0 / up_count)) - 1.0 if up_count > 0 else 0
        down_ret_f_ann = (down_f ** (12.0 / down_count)) - 1.0 if down_count > 0 else 0
        down_ret_b_ann = (down_b ** (12.0 / down_count)) - 1.0 if down_count > 0 else 0

        up_capture = (up_ret_f_ann / up_ret_b_ann) * 100.0 if up_ret_b_ann != 0 else 0.0
        down_capture = (down_ret_f_ann / down_ret_b_ann) * 100.0 if down_ret_b_ann != 0 else 0.0
        ratio = up_capture / down_capture if down_capture > 0 else 0.0

        results["upside_capture"] = round(up_capture, 2)
        results["downside_capture"] = round(down_capture, 2)
        results["capture_ratio"] = round(ratio, 2)

    return results
