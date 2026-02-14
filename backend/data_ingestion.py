"""
Data Ingestion Module — Finnhub & Alpha Vantage API Client
Fetches company profiles, financials, peers, and key ratios from free APIs.
"""

import os
import httpx

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
    # Try adding corporate suffixes
    for suffix in ["Corp", "Inc", "Corporation", "Bancorp", "Company"]:
        if suffix.lower() not in name_lower:
            queries.append(f"{company_name} {suffix}")
    # Try removing common short prefixes like "US" -> "U.S."
    if name_lower.startswith("us "):
        queries.append("U.S. " + company_name[3:])
        queries.append("U.S. " + company_name[3:] + "corp")

    async with httpx.AsyncClient(timeout=15) as client:
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
    async with httpx.AsyncClient(timeout=15) as client:
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
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{FINNHUB_BASE}/stock/peers",
            params={"symbol": ticker, "token": FINNHUB_API_KEY},
        )
        peers = resp.json()
        if isinstance(peers, list):
            # Remove self from peers
            return [p for p in peers if p != ticker][:8]
        return []


async def fetch_company_overview(ticker: str) -> dict | None:
    """Fetch company overview from Alpha Vantage OVERVIEW function."""
    if not ALPHA_VANTAGE_API_KEY:
        return None
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            ALPHA_VANTAGE_BASE,
            params={
                "function": "OVERVIEW",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_API_KEY,
            },
        )
        data = resp.json()
        if "Symbol" not in data:
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
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            ALPHA_VANTAGE_BASE,
            params={
                "function": "INCOME_STATEMENT",
                "symbol": ticker,
                "apikey": ALPHA_VANTAGE_API_KEY,
            },
        )
        data = resp.json()
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


def _parse_float(val) -> float | None:
    """Safely parse a numeric string to float."""
    if val is None or val == "None" or val == "-":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
