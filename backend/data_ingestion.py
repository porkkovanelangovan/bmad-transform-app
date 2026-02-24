"""
Data Ingestion Module — Finnhub & Alpha Vantage API Client
Fetches company profiles, financials, peers, and key ratios from free APIs.
"""

import logging
import os

import httpx

logger = logging.getLogger("data_ingestion")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

FINNHUB_BASE = "https://finnhub.io/api/v1"
ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"


async def search_ticker(company_name: str) -> str | None:
    """Search for a stock ticker symbol by company name using Finnhub.
    Tries multiple query variations if the initial search fails."""
    if not FINNHUB_API_KEY:
        return None

    # Build search variations: original, with common suffixes, without common prefixes
    queries = [company_name]
    name_lower = company_name.lower().strip()

    # Try ticker-like abbreviations — ordered by likelihood of being a real ticker
    words = company_name.strip().split()
    ticker_queries = []
    if len(words) >= 2:
        # Best: first word + initials of rest: "US Bank" -> "USB", "JP Morgan" -> "JPM"
        first_plus_initials = (words[0] + "".join(w[0] for w in words[1:] if w)).upper()
        if 2 <= len(first_plus_initials) <= 5:
            ticker_queries.append(first_plus_initials)
    # Single word or compact form: "IBM" stays "IBM"
    no_spaces = company_name.replace(" ", "").replace(".", "").upper()
    if 2 <= len(no_spaces) <= 5 and no_spaces not in ticker_queries:
        ticker_queries.append(no_spaces)
    # Search ticker candidates first, then fall back to full name
    queries = ticker_queries + queries

    # Try adding corporate suffixes
    for suffix in ["Corp", "Inc", "Corporation", "Bancorp", "Company"]:
        if suffix.lower() not in name_lower:
            queries.append(f"{company_name} {suffix}")
    # Try removing common short prefixes like "US" -> "U.S."
    if name_lower.startswith("us "):
        queries.append("U.S. " + company_name[3:])
        queries.append("U.S. " + company_name[3:] + "corp")

    async with httpx.AsyncClient(timeout=30) as client:
        for query in queries:
            resp = await client.get(
                f"{FINNHUB_BASE}/search",
                params={"q": query, "token": FINNHUB_API_KEY},
            )
            data = resp.json()
            results = data.get("result", [])
            if not results:
                continue
            # Filter to common US stock exchanges to avoid foreign tickers
            us_results = [r for r in results if not r.get("symbol", "").count(".")]
            candidates = us_results if us_results else results
            # Prefer exact description match
            for r in candidates:
                if r.get("description", "").lower() == query.lower():
                    return r["symbol"]
            # Prefer partial match containing the original name
            for r in candidates:
                if company_name.lower() in r.get("description", "").lower():
                    return r["symbol"]
            return candidates[0]["symbol"]
    return None


async def fetch_company_profile(ticker: str) -> dict | None:
    """Fetch company profile from Finnhub /stock/profile2."""
    if not FINNHUB_API_KEY:
        return None
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{FINNHUB_BASE}/stock/profile2",
            params={"symbol": ticker, "token": FINNHUB_API_KEY},
        )
        data = resp.json()
        if not data or not data.get("name"):
            return None
        return {
            "name": data.get("name"),
            "ticker": data.get("ticker", ticker),
            "industry": data.get("finnhubIndustry", ""),
            "country": data.get("country", ""),
            "currency": data.get("currency", ""),
            "market_cap": data.get("marketCapitalization"),
            "logo": data.get("logo", ""),
            "weburl": data.get("weburl", ""),
            "ipo": data.get("ipo", ""),
            "exchange": data.get("exchange", ""),
        }


async def fetch_peers(ticker: str) -> list[str]:
    """Fetch peer/competitor tickers from Finnhub /stock/peers."""
    if not FINNHUB_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{FINNHUB_BASE}/stock/peers",
                params={"symbol": ticker, "token": FINNHUB_API_KEY},
            )
            peers = resp.json()
            if isinstance(peers, list):
                # Remove self from peers
                return [p for p in peers if p != ticker][:8]
            return []
    except Exception:
        return []


async def fetch_finnhub_metrics(ticker: str) -> dict | None:
    """Fetch comprehensive financial metrics from Finnhub /stock/metric endpoint.
    Returns a flat dict of the most useful metrics, or None on failure."""
    if not FINNHUB_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{FINNHUB_BASE}/stock/metric",
                params={"symbol": ticker, "metric": "all", "token": FINNHUB_API_KEY},
            )
            data = resp.json()
            metric = data.get("metric", {})
            series = data.get("series", {})
            if not metric:
                logger.warning("Finnhub metrics returned empty for %s", ticker)
                return None

            result = {
                # Revenue & growth
                "revenuePerShareTTM": _parse_float(metric.get("revenuePerShareTTM")),
                "revenuePerShareAnnual": _parse_float(metric.get("revenuePerShareAnnual")),
                "revenueGrowthTTMYoy": _parse_float(metric.get("revenueGrowthTTMYoy")),
                "revenueGrowth5Y": _parse_float(metric.get("revenueGrowth5Y")),
                # Margins
                "netProfitMarginTTM": _parse_float(metric.get("netProfitMarginTTM")),
                "netProfitMarginAnnual": _parse_float(metric.get("netProfitMarginAnnual")),
                "netProfitMargin5Y": _parse_float(metric.get("netProfitMargin5Y")),
                "operatingMarginTTM": _parse_float(metric.get("operatingMarginTTM")),
                "operatingMarginAnnual": _parse_float(metric.get("operatingMarginAnnual")),
                "grossMarginTTM": _parse_float(metric.get("grossMarginTTM")),
                "grossMarginAnnual": _parse_float(metric.get("grossMarginAnnual")),
                # Returns
                "roeTTM": _parse_float(metric.get("roeTTM")),
                "roeRfy": _parse_float(metric.get("roeRfy")),
                "roaTTM": _parse_float(metric.get("roaTTM")),
                "roaRfy": _parse_float(metric.get("roaRfy")),
                "roicTTM": _parse_float(metric.get("roicTTM")),
                # Valuation
                "peAnnual": _parse_float(metric.get("peAnnual")),
                "peTTM": _parse_float(metric.get("peTTM")),
                "pbAnnual": _parse_float(metric.get("pbAnnual")),
                "pbQuarterly": _parse_float(metric.get("pbQuarterly")),
                "epsAnnual": _parse_float(metric.get("epsAnnual")),
                "epsTTM": _parse_float(metric.get("epsTTM")),
                "epsGrowthTTMYoy": _parse_float(metric.get("epsGrowthTTMYoy")),
                "epsGrowth3Y": _parse_float(metric.get("epsGrowth3Y")),
                "epsGrowth5Y": _parse_float(metric.get("epsGrowth5Y")),
                # Dividends & other
                "currentDividendYieldTTM": _parse_float(metric.get("currentDividendYieldTTM")),
                "dividendYieldIndicatedAnnual": _parse_float(metric.get("dividendYieldIndicatedAnnual")),
                "dividendGrowthRate5Y": _parse_float(metric.get("dividendGrowthRate5Y")),
                "beta": _parse_float(metric.get("beta")),
                "bookValuePerShareAnnual": _parse_float(metric.get("bookValuePerShareAnnual")),
                "bookValuePerShareQuarterly": _parse_float(metric.get("bookValuePerShareQuarterly")),
                "enterpriseValue": _parse_float(metric.get("enterpriseValue")),
                "52WeekHigh": _parse_float(metric.get("52WeekHigh")),
                "52WeekLow": _parse_float(metric.get("52WeekLow")),
                "marketCapitalization": _parse_float(metric.get("marketCapitalization")),
            }

            # Extract annual time-series data (for historical trends)
            annual_series = series.get("annual", {})
            for series_key in ["roe", "roa", "pe", "pb", "eps", "currentRatio", "netMargin"]:
                series_data = annual_series.get(series_key, [])
                if series_data:
                    result[f"annual_{series_key}"] = series_data[:5]  # Last 5 years

            logger.info("Finnhub metrics fetched for %s: %d non-null values", ticker,
                        sum(1 for v in result.values() if v is not None and not isinstance(v, list)))
            return result
    except Exception as e:
        logger.error("Finnhub metrics fetch failed for %s: %s", ticker, e)
        return None


async def fetch_company_overview(ticker: str) -> dict | None:
    """Fetch company overview from Alpha Vantage OVERVIEW function."""
    if not ALPHA_VANTAGE_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                ALPHA_VANTAGE_BASE,
                params={
                    "function": "OVERVIEW",
                    "symbol": ticker,
                    "apikey": ALPHA_VANTAGE_API_KEY,
                },
            )
            data = resp.json()
            if "Note" in data or "Information" in data:
                logger.warning("Alpha Vantage OVERVIEW rate limited for %s: %s", ticker, data.get("Note") or data.get("Information"))
                return None
            if "Symbol" not in data:
                return None
    except Exception as e:
        logger.error("Alpha Vantage OVERVIEW failed for %s: %s", ticker, e)
        return None
    return {
        "name": data.get("Name", ""),
        "description": data.get("Description", ""),
        "sector": data.get("Sector", ""),
        "industry": data.get("Industry", ""),
        "market_cap": _parse_float(data.get("MarketCapitalization")),
        "pe_ratio": _parse_float(data.get("PERatio")),
        "eps": _parse_float(data.get("EPS")),
        "revenue_ttm": _parse_float(data.get("RevenueTTM")),
        "gross_profit_ttm": _parse_float(data.get("GrossProfitTTM")),
        "profit_margin": _parse_float(data.get("ProfitMargin")),
        "operating_margin": _parse_float(data.get("OperatingMarginTTM")),
        "return_on_equity": _parse_float(data.get("ReturnOnEquityTTM")),
        "return_on_assets": _parse_float(data.get("ReturnOnAssetsTTM")),
        "dividend_yield": _parse_float(data.get("DividendYield")),
        "beta": _parse_float(data.get("Beta")),
        "52_week_high": _parse_float(data.get("52WeekHigh")),
        "52_week_low": _parse_float(data.get("52WeekLow")),
        "analyst_target": _parse_float(data.get("AnalystTargetPrice")),
    }


async def fetch_financials(ticker: str) -> dict | None:
    """Fetch income statement from Alpha Vantage."""
    if not ALPHA_VANTAGE_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                ALPHA_VANTAGE_BASE,
                params={
                    "function": "INCOME_STATEMENT",
                    "symbol": ticker,
                    "apikey": ALPHA_VANTAGE_API_KEY,
                },
            )
            data = resp.json()
            if "Note" in data or "Information" in data:
                logger.warning("Alpha Vantage INCOME_STATEMENT rate limited for %s: %s", ticker, data.get("Note") or data.get("Information"))
                return None
            annual = data.get("annualReports", [])
            if not annual:
                return None

            periods = []
            for report in annual[:5]:  # Last 5 years
                periods.append({
                    "fiscal_date": report.get("fiscalDateEnding", ""),
                    "total_revenue": _parse_float(report.get("totalRevenue")),
                    "gross_profit": _parse_float(report.get("grossProfit")),
                    "operating_income": _parse_float(report.get("operatingIncome")),
                    "net_income": _parse_float(report.get("netIncome")),
                    "ebitda": _parse_float(report.get("ebitda")),
                    "cost_of_revenue": _parse_float(report.get("costOfRevenue")),
                    "rd_expense": _parse_float(report.get("researchAndDevelopment")),
                })
            return {"annual_reports": periods}
    except Exception as e:
        logger.error("Alpha Vantage INCOME_STATEMENT failed for %s: %s", ticker, e)
        return None


def _parse_float(val) -> float | None:
    """Safely parse a numeric string to float."""
    if val is None or val == "None" or val == "-":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
