from fastapi import APIRouter, Depends
from database import get_db
from data_ingestion import (
    search_ticker,
    fetch_company_profile,
    fetch_peers,
    fetch_company_overview,
    fetch_financials,
)

router = APIRouter()


# --- Organization ---

@router.get("/organization")
async def get_organization(db=Depends(get_db)):
    row = await db.execute_fetchall("SELECT * FROM organization ORDER BY id DESC LIMIT 1")
    return dict(row[0]) if row else None


@router.post("/organization")
async def create_organization(data: dict, db=Depends(get_db)):
    # Upsert: delete existing, insert new
    await db.execute("DELETE FROM organization")
    cursor = await db.execute(
        "INSERT INTO organization (name, industry, competitor_1_name, competitor_2_name) VALUES (?, ?, ?, ?)",
        (data["name"], data["industry"], data.get("competitor_1_name"), data.get("competitor_2_name")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Ingest (Auto-fetch from APIs) ---

@router.post("/ingest")
async def ingest_data(db=Depends(get_db)):
    """Auto-fetch company data from Finnhub & Alpha Vantage APIs."""
    org_rows = await db.execute_fetchall("SELECT * FROM organization ORDER BY id DESC LIMIT 1")
    if not org_rows:
        return {"error": "No organization set. Create one first."}
    org = dict(org_rows[0])
    org_name = org["name"]
    summary = {"ticker": None, "profile": False, "financials": 0, "ops_metrics": 0, "competitors": 0}

    # 1. Search for ticker
    ticker = await search_ticker(org_name)
    if not ticker:
        return {"error": f"Could not find ticker for '{org_name}'. Try entering a publicly traded company name.", "summary": summary}
    summary["ticker"] = ticker

    # 2. Fetch company profile and update organization
    profile = await fetch_company_profile(ticker)
    if profile:
        await db.execute(
            "UPDATE organization SET ticker=?, sub_industry=?, market_cap=?, country=?, currency=? WHERE id=?",
            (profile["ticker"], profile.get("industry"), profile.get("market_cap"),
             profile.get("country"), profile.get("currency"), org["id"]),
        )
        summary["profile"] = True

    # 3. Ensure a business unit exists for this company
    existing_bu = await db.execute_fetchall(
        "SELECT id FROM business_units WHERE name = ?", (org_name,)
    )
    if existing_bu:
        bu_id = existing_bu[0]["id"]
    else:
        cursor = await db.execute(
            "INSERT INTO business_units (name, description) VALUES (?, ?)",
            (org_name, f"Primary business unit for {org_name}"),
        )
        bu_id = cursor.lastrowid

    # 4. Fetch financials (income statement) -> revenue_splits
    financials = await fetch_financials(ticker)
    if financials and financials.get("annual_reports"):
        for report in financials["annual_reports"]:
            period = report["fiscal_date"][:4] if report.get("fiscal_date") else "Unknown"
            revenue = report.get("total_revenue")
            if revenue:
                # Check if already exists
                existing = await db.execute_fetchall(
                    "SELECT id FROM revenue_splits WHERE business_unit_id=? AND period=? AND dimension='product' AND dimension_value='Total Revenue'",
                    (bu_id, period),
                )
                if not existing:
                    await db.execute(
                        "INSERT INTO revenue_splits (business_unit_id, dimension, dimension_value, revenue, period) VALUES (?, ?, ?, ?, ?)",
                        (bu_id, "product", "Total Revenue", revenue, period),
                    )
                    summary["financials"] += 1

    # 5. Fetch company overview -> ops_efficiency metrics
    overview = await fetch_company_overview(ticker)
    if overview:
        metrics = {
            "Profit Margin": overview.get("profit_margin"),
            "Operating Margin": overview.get("operating_margin"),
            "Return on Equity": overview.get("return_on_equity"),
            "Return on Assets": overview.get("return_on_assets"),
            "PE Ratio": overview.get("pe_ratio"),
            "EPS": overview.get("eps"),
        }
        for metric_name, metric_value in metrics.items():
            if metric_value is not None:
                existing = await db.execute_fetchall(
                    "SELECT id FROM ops_efficiency WHERE business_unit_id=? AND metric_name=? AND period='TTM'",
                    (bu_id, metric_name),
                )
                if not existing:
                    await db.execute(
                        "INSERT INTO ops_efficiency (business_unit_id, metric_name, metric_value, period) VALUES (?, ?, ?, ?)",
                        (bu_id, metric_name, metric_value, "TTM"),
                    )
                    summary["ops_metrics"] += 1

    # 6. Fetch named competitors with full financial data
    competitor_names = []
    if org.get("competitor_1_name"):
        competitor_names.append(org["competitor_1_name"])
    if org.get("competitor_2_name"):
        competitor_names.append(org["competitor_2_name"])

    for comp_name in competitor_names:
        comp_ticker = await search_ticker(comp_name)
        if not comp_ticker:
            continue

        comp_profile = await fetch_company_profile(comp_ticker)
        comp_overview = await fetch_company_overview(comp_ticker)
        comp_financials = await fetch_financials(comp_ticker)

        display_name = comp_profile.get("name", comp_name) if comp_profile else comp_name

        # Insert/update competitor record with financial columns
        existing = await db.execute_fetchall(
            "SELECT id FROM competitors WHERE name = ?", (display_name,)
        )
        if not existing:
            await db.execute(
                """INSERT INTO competitors
                   (name, ticker, revenue, profit_margin, operating_margin,
                    return_on_equity, return_on_assets, pe_ratio, eps,
                    market_cap_value, strengths, data_source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    display_name,
                    comp_ticker,
                    comp_overview.get("revenue_ttm") if comp_overview else None,
                    comp_overview.get("profit_margin") if comp_overview else None,
                    comp_overview.get("operating_margin") if comp_overview else None,
                    comp_overview.get("return_on_equity") if comp_overview else None,
                    comp_overview.get("return_on_assets") if comp_overview else None,
                    comp_overview.get("pe_ratio") if comp_overview else None,
                    comp_overview.get("eps") if comp_overview else None,
                    comp_profile.get("market_cap") if comp_profile else None,
                    f"Market Cap: ${comp_profile['market_cap']:,.0f}M" if comp_profile and comp_profile.get("market_cap") else None,
                    f"Finnhub + Alpha Vantage (ticker: {comp_ticker})",
                ),
            )
            summary["competitors"] += 1

        # Create business unit for competitor
        existing_bu = await db.execute_fetchall(
            "SELECT id FROM business_units WHERE name = ?", (display_name,)
        )
        if existing_bu:
            comp_bu_id = existing_bu[0]["id"]
        else:
            cursor = await db.execute(
                "INSERT INTO business_units (name, description) VALUES (?, ?)",
                (display_name, f"Competitor: {display_name}"),
            )
            comp_bu_id = cursor.lastrowid

        # Store competitor revenue history
        if comp_financials and comp_financials.get("annual_reports"):
            for report in comp_financials["annual_reports"]:
                period = report["fiscal_date"][:4] if report.get("fiscal_date") else "Unknown"
                revenue = report.get("total_revenue")
                if revenue:
                    existing = await db.execute_fetchall(
                        "SELECT id FROM revenue_splits WHERE business_unit_id=? AND period=? AND dimension='product' AND dimension_value='Total Revenue'",
                        (comp_bu_id, period),
                    )
                    if not existing:
                        await db.execute(
                            "INSERT INTO revenue_splits (business_unit_id, dimension, dimension_value, revenue, period) VALUES (?, ?, ?, ?, ?)",
                            (comp_bu_id, "product", "Total Revenue", revenue, period),
                        )

        # Store competitor ops metrics
        if comp_overview:
            comp_metrics = {
                "Profit Margin": comp_overview.get("profit_margin"),
                "Operating Margin": comp_overview.get("operating_margin"),
                "Return on Equity": comp_overview.get("return_on_equity"),
                "Return on Assets": comp_overview.get("return_on_assets"),
                "PE Ratio": comp_overview.get("pe_ratio"),
                "EPS": comp_overview.get("eps"),
            }
            for metric_name, metric_value in comp_metrics.items():
                if metric_value is not None:
                    existing = await db.execute_fetchall(
                        "SELECT id FROM ops_efficiency WHERE business_unit_id=? AND metric_name=? AND period='TTM'",
                        (comp_bu_id, metric_name),
                    )
                    if not existing:
                        await db.execute(
                            "INSERT INTO ops_efficiency (business_unit_id, metric_name, metric_value, period) VALUES (?, ?, ?, ?)",
                            (comp_bu_id, metric_name, metric_value, "TTM"),
                        )

    # 7. Also fetch peers for additional context (names only)
    peers = await fetch_peers(ticker)
    for peer_ticker in peers[:4]:
        peer_profile = await fetch_company_profile(peer_ticker)
        if peer_profile and peer_profile.get("name"):
            existing = await db.execute_fetchall(
                "SELECT id FROM competitors WHERE name = ?", (peer_profile["name"],)
            )
            if not existing:
                market_cap = peer_profile.get("market_cap")
                await db.execute(
                    """INSERT INTO competitors (name, ticker, market_cap_value, strengths, data_source)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        peer_profile["name"],
                        peer_ticker,
                        market_cap,
                        f"Market Cap: ${market_cap:,.0f}M" if market_cap else None,
                        f"Finnhub peer (ticker: {peer_ticker})",
                    ),
                )
                summary["competitors"] += 1

    await db.commit()
    return {"success": True, "summary": summary}


# --- Analysis ---

@router.get("/analysis")
async def get_analysis(db=Depends(get_db)):
    """Return aggregated analysis data including revenue trends, ops benchmarks, competitor comparison, and auto-SWOT."""
    org_rows = await db.execute_fetchall("SELECT * FROM organization ORDER BY id DESC LIMIT 1")
    org = dict(org_rows[0]) if org_rows else None

    org_name = org["name"] if org else None

    # Revenue trends
    revenue_rows = await db.execute_fetchall(
        "SELECT rs.period, rs.dimension_value, rs.revenue, bu.name as business_unit_name "
        "FROM revenue_splits rs JOIN business_units bu ON rs.business_unit_id = bu.id "
        "ORDER BY rs.period ASC"
    )
    revenue_trends = [dict(r) for r in revenue_rows]

    # Ops efficiency
    ops_rows = await db.execute_fetchall(
        "SELECT oe.metric_name, oe.metric_value, oe.target_value, oe.period, bu.name as business_unit_name "
        "FROM ops_efficiency oe JOIN business_units bu ON oe.business_unit_id = bu.id "
        "ORDER BY oe.metric_name"
    )
    ops_metrics = [dict(r) for r in ops_rows]

    # Competitors
    comp_rows = await db.execute_fetchall("SELECT * FROM competitors ORDER BY name")
    competitors = [dict(r) for r in comp_rows]

    # Build org metrics dict
    org_metrics = {}
    for m in ops_metrics:
        if m["business_unit_name"] == org_name:
            org_metrics[m["metric_name"]] = m["metric_value"]

    # Build competitor comparison (named competitors with financial data)
    competitor_comparison = []
    for c in competitors:
        if c.get("profit_margin") is not None or c.get("revenue") is not None:
            competitor_comparison.append({
                "name": c["name"],
                "ticker": c.get("ticker"),
                "metrics": {
                    "Profit Margin": c.get("profit_margin"),
                    "Operating Margin": c.get("operating_margin"),
                    "Return on Equity": c.get("return_on_equity"),
                    "Return on Assets": c.get("return_on_assets"),
                    "PE Ratio": c.get("pe_ratio"),
                    "EPS": c.get("eps"),
                    "Revenue (TTM)": c.get("revenue"),
                    "Market Cap": c.get("market_cap_value"),
                },
            })

    # Build revenue comparison across org and competitors
    revenue_comparison = {"org": [], "competitors": []}
    org_rev = [r for r in revenue_trends if r["business_unit_name"] == org_name and r["dimension_value"] == "Total Revenue"]
    revenue_comparison["org"] = [{"period": r["period"], "revenue": r["revenue"]} for r in org_rev]

    comp_names = set()
    if org and org.get("competitor_1_name"):
        comp_names.add(org["competitor_1_name"])
    if org and org.get("competitor_2_name"):
        comp_names.add(org["competitor_2_name"])
    # Also match by display name from competitors table
    for cc in competitor_comparison:
        comp_names.add(cc["name"])

    for cname in comp_names:
        comp_rev = [r for r in revenue_trends if r["business_unit_name"] == cname and r["dimension_value"] == "Total Revenue"]
        if comp_rev:
            revenue_comparison["competitors"].append({
                "name": cname,
                "data": [{"period": r["period"], "revenue": r["revenue"]} for r in comp_rev],
            })

    # Auto-generate SWOT based on financial data (enhanced with competitor comparison)
    swot = _generate_auto_swot(org, revenue_trends, ops_metrics, competitors, competitor_comparison, org_metrics)

    return {
        "organization": {**(org or {}), "metrics": org_metrics},
        "revenue_trends": revenue_trends,
        "ops_metrics": ops_metrics,
        "competitors": competitors,
        "competitor_comparison": competitor_comparison,
        "revenue_comparison": revenue_comparison,
        "swot": swot,
    }


@router.post("/analysis/save-swot")
async def save_analysis_swot(data: dict, db=Depends(get_db)):
    """Save auto-generated SWOT entries to the swot_entries table for Step 3."""
    entries = data.get("entries", [])
    bu_rows = await db.execute_fetchall("SELECT id FROM business_units LIMIT 1")
    if not bu_rows:
        return {"error": "No business unit exists"}
    bu_id = bu_rows[0]["id"]

    saved = 0
    for entry in entries:
        category = entry.get("category")
        description = entry.get("description")
        if category and description:
            await db.execute(
                "INSERT INTO swot_entries (business_unit_id, category, description, data_source) VALUES (?, ?, ?, ?)",
                (bu_id, category, description, "Auto-generated from Step 1 Analysis"),
            )
            saved += 1
    await db.commit()
    return {"saved": saved}


def _generate_auto_swot(org, revenue_trends, ops_metrics, competitors, competitor_comparison=None, org_metrics=None):
    """Generate SWOT entries from financial data analysis, benchmarked against competitors."""
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    org_name = org["name"] if org else "Organization"

    # Analyze ops metrics (org only)
    metrics_by_name = org_metrics or {}
    if not metrics_by_name:
        for m in ops_metrics:
            metrics_by_name[m["metric_name"]] = m["metric_value"]

    # Compute competitor averages for benchmarking
    comp_avgs = {}
    if competitor_comparison:
        for metric_key in ["Profit Margin", "Operating Margin", "Return on Equity", "Return on Assets"]:
            vals = [c["metrics"].get(metric_key) for c in competitor_comparison if c["metrics"].get(metric_key) is not None]
            if vals:
                comp_avgs[metric_key] = sum(vals) / len(vals)

    # Benchmark profit margin against competitors
    profit_margin = metrics_by_name.get("Profit Margin")
    comp_pm = comp_avgs.get("Profit Margin")
    if profit_margin is not None:
        if comp_pm is not None:
            if profit_margin > comp_pm:
                strengths.append(f"Profit margin ({profit_margin:.1%}) exceeds competitor avg ({comp_pm:.1%})")
            else:
                weaknesses.append(f"Profit margin ({profit_margin:.1%}) trails competitor avg ({comp_pm:.1%})")
        elif profit_margin > 0.15:
            strengths.append(f"Strong profit margin ({profit_margin:.1%})")
        elif profit_margin < 0.05:
            weaknesses.append(f"Low profit margin ({profit_margin:.1%})")

    # Benchmark operating margin
    op_margin = metrics_by_name.get("Operating Margin")
    comp_om = comp_avgs.get("Operating Margin")
    if op_margin is not None:
        if comp_om is not None:
            if op_margin > comp_om:
                strengths.append(f"Operating margin ({op_margin:.1%}) above competitor avg ({comp_om:.1%})")
            else:
                weaknesses.append(f"Operating margin ({op_margin:.1%}) below competitor avg ({comp_om:.1%})")
        elif op_margin > 0.20:
            strengths.append(f"High operating efficiency ({op_margin:.1%} operating margin)")
        elif op_margin < 0.10:
            weaknesses.append(f"Below-average operating margin ({op_margin:.1%})")

    # Benchmark ROE
    roe = metrics_by_name.get("Return on Equity")
    comp_roe = comp_avgs.get("Return on Equity")
    if roe is not None:
        if comp_roe is not None:
            if roe > comp_roe:
                strengths.append(f"ROE ({roe:.1%}) outperforms competitor avg ({comp_roe:.1%})")
            else:
                weaknesses.append(f"ROE ({roe:.1%}) lags competitor avg ({comp_roe:.1%})")
        elif roe > 0.15:
            strengths.append(f"Strong return on equity ({roe:.1%})")
        elif roe < 0.08:
            weaknesses.append(f"Low return on equity ({roe:.1%})")

    # ROA analysis
    roa = metrics_by_name.get("Return on Assets")
    if roa is not None:
        if roa > 0.10:
            strengths.append(f"Efficient asset utilization (ROA: {roa:.1%})")
        elif roa < 0.03:
            weaknesses.append(f"Low return on assets ({roa:.1%})")

    # Analyze revenue trends (org only)
    org_revenues = [r for r in revenue_trends if r.get("business_unit_name") == org_name and r.get("dimension_value") == "Total Revenue" and r.get("revenue")]
    if not org_revenues:
        org_revenues = [r for r in revenue_trends if r.get("dimension_value") == "Total Revenue" and r.get("revenue")]
    if len(org_revenues) >= 2:
        sorted_rev = sorted(org_revenues, key=lambda x: x["period"])
        latest = sorted_rev[-1]["revenue"]
        prev = sorted_rev[-2]["revenue"]
        if prev > 0:
            growth = (latest - prev) / prev
            if growth > 0.10:
                strengths.append(f"Strong revenue growth ({growth:.1%} YoY)")
                opportunities.append("Momentum for market share expansion")
            elif growth < 0:
                weaknesses.append(f"Declining revenue ({growth:.1%} YoY)")
                threats.append("Revenue contraction may signal market challenges")

    # Analyze market cap
    if org and org.get("market_cap"):
        mc = org["market_cap"]
        if mc > 100000:
            strengths.append(f"Large market capitalization (${mc:,.0f}M)")
        elif mc < 2000:
            weaknesses.append(f"Small market capitalization (${mc:,.0f}M) — limited resources")

    # Competitive landscape analysis
    if competitor_comparison:
        comp_names = [c["name"] for c in competitor_comparison]
        threats.append(f"Direct competition from {', '.join(comp_names)}")
        opportunities.append("Potential for strategic partnerships or differentiation vs. key competitors")
    elif competitors:
        num_competitors = len(competitors)
        if num_competitors > 5:
            threats.append(f"Highly competitive landscape ({num_competitors} identified peers)")
        opportunities.append("Potential for strategic partnerships or acquisitions among peer companies")

    # Default entries if we couldn't generate enough
    if not strengths:
        strengths.append("Established market presence")
    if not weaknesses:
        weaknesses.append("Limited financial data available for deep analysis")
    if not opportunities:
        opportunities.append("Digital transformation and AI adoption opportunities")
    if not threats:
        threats.append("Increasing market competition and economic uncertainty")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
    }


# --- Business Units ---

@router.get("/business-units")
async def list_business_units(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT * FROM business_units ORDER BY name")
    return [dict(r) for r in rows]


@router.post("/business-units")
async def create_business_unit(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO business_units (name, description) VALUES (?, ?)",
        (data["name"], data.get("description")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.delete("/business-units/{unit_id}")
async def delete_business_unit(unit_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM business_units WHERE id = ?", (unit_id,))
    await db.commit()
    return {"deleted": True}


# --- Revenue Splits ---

@router.get("/revenue-splits")
async def list_revenue_splits(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT rs.*, bu.name as business_unit_name FROM revenue_splits rs "
        "JOIN business_units bu ON rs.business_unit_id = bu.id ORDER BY rs.period DESC"
    )
    return [dict(r) for r in rows]


@router.post("/revenue-splits")
async def create_revenue_split(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO revenue_splits (business_unit_id, dimension, dimension_value, revenue, period) "
        "VALUES (?, ?, ?, ?, ?)",
        (data["business_unit_id"], data["dimension"], data["dimension_value"], data["revenue"], data["period"]),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Ops Efficiency ---

@router.get("/ops-efficiency")
async def list_ops_efficiency(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT oe.*, bu.name as business_unit_name FROM ops_efficiency oe "
        "JOIN business_units bu ON oe.business_unit_id = bu.id ORDER BY oe.period DESC"
    )
    return [dict(r) for r in rows]


@router.post("/ops-efficiency")
async def create_ops_metric(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO ops_efficiency (business_unit_id, metric_name, metric_value, target_value, period) "
        "VALUES (?, ?, ?, ?, ?)",
        (data["business_unit_id"], data["metric_name"], data["metric_value"], data.get("target_value"), data["period"]),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Competitors ---

@router.get("/competitors")
async def list_competitors(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT * FROM competitors ORDER BY name")
    return [dict(r) for r in rows]


@router.post("/competitors")
async def create_competitor(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO competitors (name, market_share, strengths, weaknesses, data_source) "
        "VALUES (?, ?, ?, ?, ?)",
        (data["name"], data.get("market_share"), data.get("strengths"), data.get("weaknesses"), data.get("data_source")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}
