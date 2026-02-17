from fastapi import APIRouter, Depends
from database import get_db
from routers.step1_performance import _generate_auto_swot
from ai_research import is_openai_available

router = APIRouter()


# --- SWOT ---

@router.get("/swot")
async def list_swot(business_unit_id: int = None, db=Depends(get_db)):
    if business_unit_id:
        rows = await db.execute_fetchall(
            "SELECT s.*, bu.name as business_unit_name FROM swot_entries s "
            "JOIN business_units bu ON s.business_unit_id = bu.id WHERE s.business_unit_id = ?",
            (business_unit_id,),
        )
    else:
        rows = await db.execute_fetchall(
            "SELECT s.*, bu.name as business_unit_name FROM swot_entries s "
            "JOIN business_units bu ON s.business_unit_id = bu.id ORDER BY s.category"
        )
    return [dict(r) for r in rows]


@router.post("/swot")
async def create_swot_entry(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO swot_entries (business_unit_id, category, description, data_source, severity, confidence) VALUES (?, ?, ?, ?, ?, ?)",
        (data["business_unit_id"], data["category"], data["description"],
         data.get("data_source"), data.get("severity", "medium"), data.get("confidence", "medium")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.delete("/swot/{entry_id}")
async def delete_swot_entry(entry_id: int, db=Depends(get_db)):
    # Delete any TOWS actions that reference this SWOT entry first (FK constraint)
    await db.execute(
        "DELETE FROM tows_actions WHERE swot_entry_1_id = ? OR swot_entry_2_id = ?",
        (entry_id, entry_id),
    )
    await db.execute("DELETE FROM swot_entries WHERE id = ?", (entry_id,))
    await db.commit()
    return {"deleted": True}


# --- TOWS Actions ---

@router.get("/tows")
async def list_tows(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT t.*, s1.description as swot_1, s1.category as swot_1_cat, "
        "s2.description as swot_2, s2.category as swot_2_cat "
        "FROM tows_actions t "
        "JOIN swot_entries s1 ON t.swot_entry_1_id = s1.id "
        "JOIN swot_entries s2 ON t.swot_entry_2_id = s2.id "
        "ORDER BY t.impact_score DESC, t.priority DESC"
    )
    return [dict(r) for r in rows]


@router.post("/tows")
async def create_tows_action(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO tows_actions (strategy_type, swot_entry_1_id, swot_entry_2_id, action_description, priority, impact_score, rationale) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data["strategy_type"], data["swot_entry_1_id"], data["swot_entry_2_id"],
         data["action_description"], data.get("priority"),
         data.get("impact_score", 5), data.get("rationale")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Auto-Generate SWOT & TOWS ---

@router.post("/auto-generate")
async def auto_generate(data: dict, db=Depends(get_db)):
    """Auto-generate SWOT entries from Step 1 & Step 2 data, then generate TOWS actions.
    Uses AI when OpenAI is available, falls back to rule-based generation."""
    business_unit_id = data["business_unit_id"]
    ai_used = False

    # 1. Cleanup: delete TOWS referencing auto-generated SWOT, then delete those SWOT entries
    auto_ids = await db.execute_fetchall(
        "SELECT id FROM swot_entries WHERE data_source LIKE 'Auto-generated%' AND business_unit_id = ?",
        (business_unit_id,),
    )
    auto_id_list = [r["id"] for r in auto_ids]
    if auto_id_list:
        placeholders = ",".join("?" * len(auto_id_list))
        await db.execute(
            f"DELETE FROM tows_actions WHERE swot_entry_1_id IN ({placeholders}) OR swot_entry_2_id IN ({placeholders})",
            auto_id_list + auto_id_list,
        )
        await db.execute(
            f"DELETE FROM swot_entries WHERE id IN ({placeholders})",
            auto_id_list,
        )

    # 2. Try AI-powered generation first
    if is_openai_available():
        try:
            from ai_swot_strategy import gather_full_context, generate_ai_swot, generate_ai_tows

            context = await gather_full_context(db, business_unit_id)
            ai_swot = await generate_ai_swot(context)

            if ai_swot:
                ai_used = True
                all_inserted = {"strength": [], "weakness": [], "opportunity": [], "threat": []}
                ai_count = 0

                cat_map = {"strengths": "strength", "weaknesses": "weakness",
                           "opportunities": "opportunity", "threats": "threat"}

                for ai_cat, db_cat in cat_map.items():
                    for entry in ai_swot.get(ai_cat, []):
                        desc = entry["description"] if isinstance(entry, dict) else str(entry)
                        severity = entry.get("severity", "medium") if isinstance(entry, dict) else "medium"
                        confidence = entry.get("confidence", "medium") if isinstance(entry, dict) else "medium"
                        data_source_label = entry.get("data_source", "AI-generated") if isinstance(entry, dict) else "AI-generated"

                        cursor = await db.execute(
                            "INSERT INTO swot_entries (business_unit_id, category, description, data_source, severity, confidence) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (business_unit_id, db_cat, desc,
                             f"Auto-generated (AI) — {data_source_label}",
                             severity, confidence),
                        )
                        all_inserted[db_cat].append({
                            "id": cursor.lastrowid, "description": desc,
                            "severity": severity, "confidence": confidence,
                            "category": db_cat,
                        })
                        ai_count += 1

                # Generate AI TOWS
                all_swot_flat = []
                for cat_entries in all_inserted.values():
                    all_swot_flat.extend(cat_entries)

                ai_tows = await generate_ai_tows(all_swot_flat, context)
                tows_count = 0

                if ai_tows:
                    tows_count = await _store_ai_tows(db, ai_tows, all_inserted)
                else:
                    # Fallback to rule-based TOWS with AI SWOT entries
                    tows_count = await _generate_tows_actions(db, all_inserted)

                await db.commit()
                return {
                    "swot_generated": ai_count,
                    "tows_generated": tows_count,
                    "sources": {"ai": ai_count, "step1": 0, "step2": 0},
                    "ai_powered": True,
                }
        except Exception:
            pass  # Fall through to rule-based

    # 3. Rule-based fallback: Step 1 Financial SWOT
    org_rows = await db.execute_fetchall("SELECT * FROM organization ORDER BY id DESC LIMIT 1")
    org = dict(org_rows[0]) if org_rows else None
    org_name = org["name"] if org else None

    revenue_rows = await db.execute_fetchall(
        "SELECT rs.period, rs.dimension_value, rs.revenue, bu.name as business_unit_name "
        "FROM revenue_splits rs JOIN business_units bu ON rs.business_unit_id = bu.id ORDER BY rs.period ASC"
    )
    revenue_trends = [dict(r) for r in revenue_rows]

    ops_rows = await db.execute_fetchall(
        "SELECT oe.metric_name, oe.metric_value, oe.target_value, oe.period, bu.name as business_unit_name "
        "FROM ops_efficiency oe JOIN business_units bu ON oe.business_unit_id = bu.id ORDER BY oe.metric_name"
    )
    ops_metrics = [dict(r) for r in ops_rows]

    comp_rows = await db.execute_fetchall("SELECT * FROM competitors ORDER BY name")
    competitors = [dict(r) for r in comp_rows]

    org_metrics = {}
    for m in ops_metrics:
        if m["business_unit_name"] == org_name:
            org_metrics[m["metric_name"]] = m["metric_value"]

    competitor_comparison = []
    for c in competitors:
        if c.get("profit_margin") is not None or c.get("revenue") is not None:
            competitor_comparison.append({
                "name": c["name"],
                "metrics": {
                    "Profit Margin": c.get("profit_margin"),
                    "Operating Margin": c.get("operating_margin"),
                    "Return on Equity": c.get("return_on_equity"),
                    "Return on Assets": c.get("return_on_assets"),
                },
            })

    # Try to get industry benchmarks for dynamic thresholds
    benchmarks = None
    try:
        from source_gatherers import gather_industry_benchmarks
        vs_rows = await db.execute_fetchall(
            "SELECT name FROM value_streams WHERE business_unit_id = ? LIMIT 1",
            (business_unit_id,),
        )
        segment = dict(vs_rows[0])["name"] if vs_rows else "general"
        industry = org.get("industry", "") if org else ""
        benchmarks = await gather_industry_benchmarks(segment, industry)
    except Exception:
        pass

    step1_swot = _generate_auto_swot(org, revenue_trends, ops_metrics, competitors,
                                     competitor_comparison, org_metrics, benchmarks=benchmarks)

    # Step 2 VSM SWOT
    step2_swot = await _generate_vsm_swot(db, business_unit_id, benchmarks=benchmarks)

    # 4. Save SWOT entries (entries are now dicts with description/severity/confidence)
    step1_count = 0
    step2_count = 0
    all_inserted = {"strength": [], "weakness": [], "opportunity": [], "threat": []}

    for category, entries in [
        ("strength", step1_swot["strengths"]),
        ("weakness", step1_swot["weaknesses"]),
        ("opportunity", step1_swot["opportunities"]),
        ("threat", step1_swot["threats"]),
    ]:
        for entry in entries:
            desc = entry["description"] if isinstance(entry, dict) else str(entry)
            severity = entry.get("severity", "medium") if isinstance(entry, dict) else "medium"
            confidence = entry.get("confidence", "medium") if isinstance(entry, dict) else "medium"

            cursor = await db.execute(
                "INSERT INTO swot_entries (business_unit_id, category, description, data_source, severity, confidence) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (business_unit_id, category, desc, "Auto-generated from Step 1", severity, confidence),
            )
            all_inserted[category].append({"id": cursor.lastrowid, "description": desc})
            step1_count += 1

    for category, entries in [
        ("strength", step2_swot["strengths"]),
        ("weakness", step2_swot["weaknesses"]),
        ("opportunity", step2_swot["opportunities"]),
        ("threat", step2_swot["threats"]),
    ]:
        for entry in entries:
            desc = entry["description"] if isinstance(entry, dict) else str(entry)
            severity = entry.get("severity", "medium") if isinstance(entry, dict) else "medium"
            confidence = entry.get("confidence", "medium") if isinstance(entry, dict) else "medium"

            cursor = await db.execute(
                "INSERT INTO swot_entries (business_unit_id, category, description, data_source, severity, confidence) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (business_unit_id, category, desc, "Auto-generated from Step 2", severity, confidence),
            )
            all_inserted[category].append({"id": cursor.lastrowid, "description": desc})
            step2_count += 1

    # 5. Generate TOWS actions
    tows_count = await _generate_tows_actions(db, all_inserted)

    await db.commit()

    return {
        "swot_generated": step1_count + step2_count,
        "tows_generated": tows_count,
        "sources": {"step1": step1_count, "step2": step2_count},
        "ai_powered": False,
    }


async def _store_ai_tows(db, ai_tows: list[dict], swot_inserted: dict) -> int:
    """Store AI-generated TOWS actions, matching SWOT descriptions to IDs."""
    count = 0

    # Build lookup: description -> id for matching AI TOWS to stored SWOT entries
    all_entries = []
    for cat, entries in swot_inserted.items():
        for e in entries:
            all_entries.append(e)

    def _find_best_match(description: str, category_filter: str = None) -> int | None:
        """Find the SWOT entry ID that best matches a description."""
        if not description:
            return None
        desc_lower = description.lower()
        best_id = None
        best_score = 0
        for e in all_entries:
            if category_filter and e.get("category") != category_filter:
                continue
            e_desc = e.get("description", "").lower()
            # Simple overlap scoring
            words = set(desc_lower.split())
            e_words = set(e_desc.split())
            overlap = len(words & e_words)
            if overlap > best_score:
                best_score = overlap
                best_id = e["id"]
        return best_id

    # Map strategy_type to expected SWOT category pairings
    type_cats = {
        "SO": ("strength", "opportunity"),
        "WO": ("weakness", "opportunity"),
        "ST": ("strength", "threat"),
        "WT": ("weakness", "threat"),
    }

    for action in ai_tows:
        stype = action.get("strategy_type", "SO")
        cat1, cat2 = type_cats.get(stype, ("strength", "opportunity"))

        swot_1_id = _find_best_match(action.get("swot_1_description", ""), cat1)
        swot_2_id = _find_best_match(action.get("swot_2_description", ""), cat2)

        # Fallback: use first entries of appropriate category if no match
        if not swot_1_id and swot_inserted.get(cat1):
            swot_1_id = swot_inserted[cat1][0]["id"]
        if not swot_2_id and swot_inserted.get(cat2):
            swot_2_id = swot_inserted[cat2][0]["id"]

        if not swot_1_id or not swot_2_id:
            continue  # Can't store without valid SWOT entry IDs

        await db.execute(
            "INSERT INTO tows_actions (strategy_type, swot_entry_1_id, swot_entry_2_id, "
            "action_description, priority, impact_score, rationale) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (stype, swot_1_id, swot_2_id,
             action.get("action_description", "Strategic action"),
             action.get("priority", "medium"),
             action.get("impact_score", 5),
             action.get("rationale", "")),
        )
        count += 1

    return count


async def _generate_vsm_swot(db, business_unit_id: int, benchmarks=None) -> dict:
    """Generate SWOT entries from Step 2 value stream data.
    Each entry is a dict with description, severity, confidence keys.
    Uses industry benchmarks for dynamic thresholds when available."""
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    # Dynamic thresholds from benchmarks (or hardcoded fallbacks)
    bench_kpis = (benchmarks or {}).get("industry_kpis", {}) if benchmarks else {}
    fe_strength_threshold = bench_kpis.get("best_in_class_flow_efficiency_pct", 25)
    fe_weakness_threshold = max(bench_kpis.get("avg_flow_efficiency_pct", 15) * 0.7, 10)

    # Get all value streams for this business unit
    vs_rows = await db.execute_fetchall(
        "SELECT vs.id, vs.name FROM value_streams vs WHERE vs.business_unit_id = ?",
        (business_unit_id,),
    )

    for vs in vs_rows:
        vs_id = vs["id"]
        vs_name = vs["name"]

        # Fetch metrics
        metrics_rows = await db.execute_fetchall(
            "SELECT * FROM value_stream_metrics WHERE value_stream_id = ?", (vs_id,),
        )
        if not metrics_rows:
            continue
        m = dict(metrics_rows[0])

        flow_eff = m.get("flow_efficiency") or 0
        total_lt = m.get("total_lead_time_hours") or 0
        total_wt = m.get("total_wait_time_hours") or 0
        total_pt = m.get("total_process_time_hours") or 0
        bottleneck = m.get("bottleneck_step")

        # Flow efficiency analysis (dynamic thresholds)
        if flow_eff > fe_strength_threshold:
            strengths.append({"description": f"{vs_name}: High flow efficiency ({flow_eff:.1f}%)",
                              "severity": "high" if flow_eff > fe_strength_threshold * 1.3 else "medium",
                              "confidence": "high"})
        elif flow_eff < fe_weakness_threshold:
            strengths_gap = fe_weakness_threshold - flow_eff
            weaknesses.append({"description": f"{vs_name}: Low flow efficiency ({flow_eff:.1f}%) — excessive wait times",
                               "severity": "high" if strengths_gap > 10 else "medium",
                               "confidence": "high"})

        # Bottleneck analysis
        if bottleneck:
            weaknesses.append({"description": f"{vs_name}: Bottleneck at '{bottleneck}'",
                               "severity": "high", "confidence": "high"})

        # Wait/process ratio analysis
        if total_pt > 0:
            wait_ratio = total_wt / total_pt
            if wait_ratio > 3:
                opportunities.append({"description": f"{vs_name}: Automation opportunity ({wait_ratio:.1f}x wait-to-process ratio)",
                                      "severity": "high" if wait_ratio > 5 else "medium",
                                      "confidence": "high"})

        # Fetch benchmarks for competitor comparison
        vs_benchmarks = [dict(r) for r in await db.execute_fetchall(
            "SELECT * FROM value_stream_benchmarks WHERE value_stream_id = ?", (vs_id,),
        )]

        if vs_benchmarks:
            # Compare flow efficiency vs competitor average
            comp_fe_vals = [b["flow_efficiency"] for b in vs_benchmarks if b.get("flow_efficiency") is not None]
            if comp_fe_vals:
                comp_fe_avg = sum(comp_fe_vals) / len(comp_fe_vals)
                if flow_eff > comp_fe_avg:
                    strengths.append({"description": f"{vs_name}: Outperforms competitor avg flow efficiency ({flow_eff:.1f}% vs {comp_fe_avg:.1f}%)",
                                      "severity": "medium", "confidence": "high"})
                elif flow_eff < comp_fe_avg:
                    weaknesses.append({"description": f"{vs_name}: Trails competitor avg flow efficiency ({flow_eff:.1f}% vs {comp_fe_avg:.1f}%)",
                                       "severity": "medium", "confidence": "high"})

            # Compare lead time vs competitor average
            comp_lt_vals = [b["total_lead_time_hours"] for b in vs_benchmarks if b.get("total_lead_time_hours") is not None]
            if comp_lt_vals:
                comp_lt_avg = sum(comp_lt_vals) / len(comp_lt_vals)
                if total_lt < comp_lt_avg:
                    strengths.append({"description": f"{vs_name}: Faster lead time than competitors ({total_lt:.1f}h vs {comp_lt_avg:.1f}h avg)",
                                      "severity": "medium", "confidence": "high"})
                elif total_lt > comp_lt_avg * 1.2:
                    threats.append({"description": f"{vs_name}: Competitors have faster lead times ({total_lt:.1f}h vs {comp_lt_avg:.1f}h avg)",
                                    "severity": "high" if total_lt > comp_lt_avg * 1.5 else "medium",
                                    "confidence": "high"})

        # Fetch levers as opportunities
        levers = [dict(r) for r in await db.execute_fetchall(
            "SELECT * FROM value_stream_levers WHERE value_stream_id = ? AND impact_estimate = 'high'",
            (vs_id,),
        )]
        for lever in levers:
            opportunities.append({"description": f"{vs_name}: {lever['opportunity']}",
                                  "severity": "medium", "confidence": "medium"})

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
    }


def _extract_key_area(description: str) -> str:
    """Extract a short key area label from a SWOT description for TOWS action text."""
    import re
    desc_lower = description.lower()
    if "bottleneck" in desc_lower:
        return "process bottleneck"
    if "flow efficiency" in desc_lower:
        return "flow efficiency"
    if "lead time" in desc_lower:
        return "lead time advantage"
    if "automation" in desc_lower or "wait-to-process" in desc_lower:
        return "automation potential"
    if "profit margin" in desc_lower:
        return "profit margin"
    if "operating margin" in desc_lower:
        return "operating efficiency"
    if "roe" in desc_lower or "return on equity" in desc_lower:
        return "capital efficiency"
    if "roa" in desc_lower or "return on assets" in desc_lower:
        return "asset utilization"
    if "revenue" in desc_lower:
        return "revenue performance"
    if "market cap" in desc_lower:
        return "market position"
    if "competition" in desc_lower or "competitor" in desc_lower:
        return "competitive landscape"
    if "partnership" in desc_lower or "differentiation" in desc_lower:
        return "strategic positioning"
    if "digital" in desc_lower or re.search(r'\bai\b', desc_lower):
        return "digital transformation"
    if "market" in desc_lower:
        return "market position"
    if "financial" in desc_lower:
        return "financial performance"
    # Fallback: use first ~40 chars, lowercased for natural phrasing
    return description[:40].rstrip(" .,;—-").lower()


async def _generate_tows_actions(db, swot_entries: dict) -> int:
    """Generate TOWS strategic actions by pairing SWOT entries (rule-based fallback)."""
    strengths = swot_entries.get("strength", [])
    weaknesses = swot_entries.get("weakness", [])
    opportunities = swot_entries.get("opportunity", [])
    threats = swot_entries.get("threat", [])

    count = 0

    # SO: top 3 strengths x top 2 opportunities (priority: high)
    for s in strengths[:3]:
        for o in opportunities[:2]:
            s_area = _extract_key_area(s["description"])
            o_area = _extract_key_area(o["description"])
            action = f"Leverage {s_area} to capitalize on {o_area}"
            await db.execute(
                "INSERT INTO tows_actions (strategy_type, swot_entry_1_id, swot_entry_2_id, action_description, priority, impact_score, rationale) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("SO", s["id"], o["id"], action, "high", 7, f"Pairing strength ({s_area}) with opportunity ({o_area})"),
            )
            count += 1

    # WO: top 3 weaknesses x top 2 opportunities (priority: high if bottleneck, else medium)
    for w in weaknesses[:3]:
        for o in opportunities[:2]:
            w_area = _extract_key_area(w["description"])
            o_area = _extract_key_area(o["description"])
            is_bottleneck = "bottleneck" in w["description"].lower()
            priority = "high" if is_bottleneck else "medium"
            impact = 8 if is_bottleneck else 5
            action = f"Address {w_area} by leveraging {o_area}"
            await db.execute(
                "INSERT INTO tows_actions (strategy_type, swot_entry_1_id, swot_entry_2_id, action_description, priority, impact_score, rationale) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("WO", w["id"], o["id"], action, priority, impact, f"Addressing weakness ({w_area}) through opportunity ({o_area})"),
            )
            count += 1

    # ST: top 2 strengths x top 2 threats (priority: high)
    for s in strengths[:2]:
        for t in threats[:2]:
            s_area = _extract_key_area(s["description"])
            t_area = _extract_key_area(t["description"])
            action = f"Deploy {s_area} to counter {t_area}"
            await db.execute(
                "INSERT INTO tows_actions (strategy_type, swot_entry_1_id, swot_entry_2_id, action_description, priority, impact_score, rationale) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("ST", s["id"], t["id"], action, "high", 6, f"Using strength ({s_area}) to mitigate threat ({t_area})"),
            )
            count += 1

    # WT: top 2 weaknesses x top 2 threats (priority: medium)
    for w in weaknesses[:2]:
        for t in threats[:2]:
            w_area = _extract_key_area(w["description"])
            t_area = _extract_key_area(t["description"])
            action = f"Minimize {t_area} exposure while addressing {w_area}"
            await db.execute(
                "INSERT INTO tows_actions (strategy_type, swot_entry_1_id, swot_entry_2_id, action_description, priority, impact_score, rationale) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("WT", w["id"], t["id"], action, "medium", 4, f"Risk mitigation: addressing {w_area} while defending against {t_area}"),
            )
            count += 1

    return count
