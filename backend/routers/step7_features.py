from fastapi import APIRouter, Depends
from database import get_db
from ai_initiatives import gather_initiative_context, generate_ai_features
from ai_research import is_openai_available

router = APIRouter()

# --- Layer-specific feature templates (3 features per epic) ---
FEATURE_TEMPLATES = {
    "business": [
        ("Research & Discovery", "Conduct research, gather insights, and identify key requirements"),
        ("Implementation & Rollout", "Build and deploy core functionality with stakeholder alignment"),
        ("Monitoring & Optimization", "Track performance metrics and continuously optimize outcomes"),
    ],
    "digital": [
        ("Architecture & Design", "Design system architecture, technical specifications, and interfaces"),
        ("Core Development", "Implement core functionality, APIs, and integration points"),
        ("Testing & Deployment", "Comprehensive testing, CI/CD setup, and production deployment"),
    ],
    "data": [
        ("Data Modeling & Schema", "Design data models, schemas, and storage architecture"),
        ("ETL & Processing", "Build data extraction, transformation, and loading pipelines"),
        ("Validation & Monitoring", "Implement data quality checks, validation rules, and monitoring"),
    ],
    "gen_ai": [
        ("Research & Prototyping", "Explore approaches, build prototypes, and validate feasibility"),
        ("Model Training & Tuning", "Train, fine-tune, and optimize models for target use cases"),
        ("Integration & Evaluation", "Integrate models into workflows and evaluate real-world performance"),
    ],
}


# --- Delivery OKRs ---

@router.get("/delivery-okrs")
async def list_delivery_okrs(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT do.*, po.objective as product_objective, t.name as team_name "
        "FROM delivery_okrs do "
        "JOIN product_okrs po ON do.product_okr_id = po.id "
        "JOIN teams t ON do.team_id = t.id"
    )
    return [dict(r) for r in rows]


@router.post("/delivery-okrs")
async def create_delivery_okr(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO delivery_okrs (product_okr_id, team_id, objective, status) VALUES (?, ?, ?, ?)",
        (data["product_okr_id"], data["team_id"], data["objective"], data.get("status", "draft")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Features ---

@router.get("/features")
async def list_features(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT f.*, e.name as epic_name FROM features f "
        "JOIN epics e ON f.epic_id = e.id "
        "ORDER BY f.priority_score DESC, f.status"
    )
    return [dict(r) for r in rows]


@router.post("/features")
async def create_feature(data: dict, db=Depends(get_db)):
    value = data.get("value_score", 3)
    size = data.get("size_score", 3)
    effort = data.get("effort_score", 3)
    priority = round((value * size) / effort, 2) if effort else 0
    cursor = await db.execute(
        "INSERT INTO features (epic_id, delivery_okr_id, name, description, priority, status, "
        "estimated_effort, start_date, target_date, value_score, size_score, effort_score, "
        "priority_score, risk_level, risks, dependencies_text, roadmap_phase) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data["epic_id"], data.get("delivery_okr_id"), data["name"], data.get("description"),
         data.get("priority", "medium"), data.get("status", "backlog"),
         data.get("estimated_effort"), data.get("start_date"), data.get("target_date"),
         value, size, effort, priority,
         data.get("risk_level", "medium"), data.get("risks"),
         data.get("dependencies_text"), data.get("roadmap_phase")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.put("/features/{feature_id}")
async def update_feature(feature_id: int, data: dict, db=Depends(get_db)):
    allowed = [
        "delivery_okr_id", "name", "description", "priority", "status",
        "estimated_effort", "start_date", "target_date", "completion_date",
        "value_score", "size_score", "effort_score",
        "risk_level", "risks", "dependencies_text", "roadmap_phase",
    ]
    fields = []
    values = []
    for key in allowed:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])

    # Auto-recalculate priority_score if any scoring field changed
    scoring_fields = {"value_score", "size_score", "effort_score"}
    if scoring_fields & set(data.keys()):
        row = await db.execute_fetchone(
            "SELECT value_score, size_score, effort_score FROM features WHERE id = ?",
            (feature_id,),
        )
        if row:
            v = data.get("value_score", row["value_score"] or 3)
            s = data.get("size_score", row["size_score"] or 3)
            e = data.get("effort_score", row["effort_score"] or 3)
            priority = round((v * s) / e, 2) if e else 0
            fields.append("priority_score = ?")
            values.append(priority)

    if fields:
        values.append(feature_id)
        await db.execute(
            f"UPDATE features SET {', '.join(fields)} WHERE id = ?", values
        )
        await db.commit()
    return {"updated": True}


@router.delete("/features/{feature_id}")
async def delete_feature(feature_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM features WHERE id = ?", (feature_id,))
    await db.commit()
    return {"deleted": True}


# --- Summary (for Generate tab) ---

@router.get("/summary")
async def get_summary(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM epics")
    epic_count = rows[0]["cnt"] if rows else 0

    rows = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM features")
    feat_count = rows[0]["cnt"] if rows else 0

    rows = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM delivery_okrs")
    dokr_count = rows[0]["cnt"] if rows else 0

    rows = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM teams")
    team_count = rows[0]["cnt"] if rows else 0

    return {
        "epics": epic_count,
        "features": feat_count,
        "delivery_okrs": dokr_count,
        "teams": team_count,
    }


# --- Auto-generate: Decompose epics -> features + delivery OKRs ---

def _infer_risk_level(risks_text):
    if not risks_text:
        return "medium"
    t = risks_text.lower()
    if "critical" in t:
        return "critical"
    if "high" in t:
        return "high"
    if "low" in t or "minimal" in t:
        return "low"
    return "medium"


@router.post("/auto-generate")
async def auto_generate(db=Depends(get_db)):
    # Fetch all epics with initiative/strategy/product/team context
    rows = await db.execute_fetchall(
        "SELECT e.*, "
        "i.name as initiative_name, i.strategy_id, "
        "s.layer as strategy_layer, s.name as strategy_name, "
        "dp.id as product_id, dp.name as product_name, "
        "pg.name as product_group_name, "
        "t.name as team_name, "
        "po.objective as okr_objective "
        "FROM epics e "
        "JOIN initiatives i ON e.initiative_id = i.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "LEFT JOIN digital_products dp ON i.digital_product_id = dp.id "
        "LEFT JOIN product_groups pg ON dp.product_group_id = pg.id "
        "LEFT JOIN teams t ON e.team_id = t.id "
        "LEFT JOIN product_okrs po ON e.product_okr_id = po.id "
        "ORDER BY e.id"
    )
    epics = [dict(r) for r in rows]

    created_features = []
    created_dokrs = []
    created_feat_deps = []
    skipped = []
    ai_powered = False

    # Try AI-powered generation
    if is_openai_available():
        context = await gather_initiative_context(db)
        ai_result = await generate_ai_features(epics, context)

        if ai_result:
            ai_powered = True
            ai_features = ai_result["features"]
            ai_dokrs = ai_result.get("delivery_okrs", [])
            ai_feat_deps = ai_result.get("feature_dependencies", [])

            # Build epic name -> id lookup
            epic_lookup = {}
            for epic in epics:
                epic_lookup[epic["name"]] = epic

            # Create AI-generated delivery OKRs
            for ai_dokr in ai_dokrs:
                pokr_obj = ai_dokr.get("product_okr_objective", "")
                team_name = ai_dokr.get("team_name", "")

                # Find product OKR by objective match
                pokr_rows = await db.execute_fetchall(
                    "SELECT id FROM product_okrs WHERE objective = ? LIMIT 1",
                    (pokr_obj,)
                )
                if not pokr_rows:
                    # Try partial match
                    pokr_rows = await db.execute_fetchall(
                        "SELECT id FROM product_okrs ORDER BY id DESC LIMIT 1"
                    )
                if not pokr_rows:
                    continue
                pokr_id = pokr_rows[0]["id"]

                # Find team by name
                team_rows = await db.execute_fetchall(
                    "SELECT id FROM teams WHERE name = ? LIMIT 1",
                    (team_name,)
                )
                if not team_rows:
                    # Use first available team
                    team_rows = await db.execute_fetchall("SELECT id FROM teams LIMIT 1")
                if not team_rows:
                    continue
                team_id = team_rows[0]["id"]

                # Check if exists
                existing = await db.execute_fetchall(
                    "SELECT id FROM delivery_okrs WHERE product_okr_id = ? AND team_id = ? LIMIT 1",
                    (pokr_id, team_id)
                )
                if existing:
                    continue

                cur = await db.execute(
                    "INSERT INTO delivery_okrs (product_okr_id, team_id, objective, ai_generated, status) "
                    "VALUES (?, ?, ?, 1, 'draft')",
                    (pokr_id, team_id, ai_dokr["objective"])
                )
                dokr_id = cur.lastrowid
                created_dokrs.append({"id": dokr_id, "objective": ai_dokr["objective"]})

                # Create delivery key results
                for kr in ai_dokr.get("key_results", []):
                    await db.execute(
                        "INSERT INTO delivery_key_results "
                        "(delivery_okr_id, key_result, metric, current_value, target_value, unit) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (dokr_id, kr.get("key_result", ""), kr.get("metric", ""),
                         kr.get("current_value", 0), kr.get("target_value", 0), kr.get("unit", ""))
                    )

            # Create AI-generated features
            feat_name_to_id = {}
            for ai_feat in ai_features:
                # Match to epic
                epic_match = epic_lookup.get(ai_feat.get("epic_name"))
                if not epic_match:
                    for ename, edata in epic_lookup.items():
                        if ai_feat.get("epic_name", "").lower() in ename.lower() or ename.lower() in ai_feat.get("epic_name", "").lower():
                            epic_match = edata
                            break
                if not epic_match:
                    epic_match = epics[0] if epics else None
                if not epic_match:
                    continue

                feat_name = ai_feat["name"]

                # Idempotent
                dup_rows = await db.execute_fetchall(
                    "SELECT id FROM features WHERE name = ? AND epic_id = ? LIMIT 1",
                    (feat_name, epic_match["id"])
                )
                if dup_rows:
                    skipped.append(feat_name)
                    continue

                # Find delivery OKR to link
                dokr_link_id = None
                if epic_match.get("product_okr_id") and epic_match.get("team_id"):
                    dokr_rows = await db.execute_fetchall(
                        "SELECT id FROM delivery_okrs WHERE product_okr_id = ? AND team_id = ? LIMIT 1",
                        (epic_match["product_okr_id"], epic_match["team_id"])
                    )
                    if dokr_rows:
                        dokr_link_id = dokr_rows[0]["id"]

                value = ai_feat.get("value_score", 3)
                size = ai_feat.get("size_score", 3)
                effort = ai_feat.get("effort_score", 3)
                priority = round((value * size) / effort, 2) if effort else 0

                cur = await db.execute(
                    "INSERT INTO features (epic_id, delivery_okr_id, name, description, status, "
                    "estimated_effort, value_score, size_score, effort_score, priority_score, "
                    "risk_level, risks, dependencies_text, roadmap_phase, "
                    "ai_generated, ai_rationale, acceptance_criteria) "
                    "VALUES (?, ?, ?, ?, 'backlog', ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                    (epic_match["id"], dokr_link_id, feat_name, ai_feat.get("description", ""),
                     ai_feat.get("estimated_effort"),
                     value, size, effort, priority,
                     ai_feat.get("risk_level", "medium"), ai_feat.get("risks", ""),
                     ai_feat.get("dependencies_text", ""), None,
                     ai_feat.get("rationale", ""), ai_feat.get("acceptance_criteria", ""))
                )
                feat_id = cur.lastrowid
                feat_name_to_id[feat_name] = feat_id
                layer = epic_match.get("strategy_layer") or "digital"
                created_features.append({"id": feat_id, "name": feat_name, "layer": layer})

            # Create feature dependencies
            for dep in ai_feat_deps:
                feat_id = feat_name_to_id.get(dep.get("feature_name"))
                depends_on_id = feat_name_to_id.get(dep.get("depends_on_feature_name"))
                if feat_id and depends_on_id and feat_id != depends_on_id:
                    existing = await db.execute_fetchall(
                        "SELECT id FROM feature_dependencies WHERE feature_id = ? AND depends_on_feature_id = ? LIMIT 1",
                        (feat_id, depends_on_id)
                    )
                    if not existing:
                        cur = await db.execute(
                            "INSERT INTO feature_dependencies (feature_id, depends_on_feature_id, dependency_type, notes) "
                            "VALUES (?, ?, 'blocks', ?)",
                            (feat_id, depends_on_id, dep.get("notes", "AI-generated dependency"))
                        )
                        created_feat_deps.append({"id": cur.lastrowid})

    # Fallback: rule-based generation
    if not ai_powered:
        for epic in epics:
            layer = epic.get("strategy_layer") or "digital"
            templates = FEATURE_TEMPLATES.get(layer, FEATURE_TEMPLATES["digital"])
            epic_value = epic.get("value_score") or 3
            epic_size = epic.get("size_score") or 3
            epic_risks = epic.get("risks") or ""
            risk_level = epic.get("risk_level") or _infer_risk_level(epic_risks)

            # Create delivery OKR
            if epic.get("product_okr_id") and epic.get("team_id"):
                existing_dokr = await db.execute_fetchall(
                    "SELECT id FROM delivery_okrs WHERE product_okr_id = ? AND team_id = ? LIMIT 1",
                    (epic["product_okr_id"], epic["team_id"]),
                )
                if not existing_dokr:
                    pokr_rows = await db.execute_fetchall(
                        "SELECT objective FROM product_okrs WHERE id = ? LIMIT 1",
                        (epic["product_okr_id"],),
                    )
                    if pokr_rows:
                        dokr_obj = f"Deliver: {pokr_rows[0]['objective']}"
                        dokr_cur = await db.execute(
                            "INSERT INTO delivery_okrs (product_okr_id, team_id, objective, ai_generated, status) "
                            "VALUES (?, ?, ?, 0, 'draft')",
                            (epic["product_okr_id"], epic["team_id"], dokr_obj),
                        )
                        dokr_id = dokr_cur.lastrowid
                        created_dokrs.append({"id": dokr_id, "objective": dokr_obj})

                        pkr_rows = await db.execute_fetchall(
                            "SELECT * FROM product_key_results WHERE product_okr_id = ?",
                            (epic["product_okr_id"],),
                        )
                        for pkr in pkr_rows:
                            pkr = dict(pkr)
                            await db.execute(
                                "INSERT INTO delivery_key_results "
                                "(delivery_okr_id, key_result, metric, current_value, target_value, unit) "
                                "VALUES (?, ?, ?, ?, ?, ?)",
                                (dokr_id, pkr["key_result"], pkr.get("metric"),
                                 pkr.get("current_value", 0), pkr.get("target_value", 0),
                                 pkr.get("unit")),
                            )

            # Find delivery OKR to link
            dokr_link_id = None
            if epic.get("product_okr_id") and epic.get("team_id"):
                dokr_rows = await db.execute_fetchall(
                    "SELECT id FROM delivery_okrs WHERE product_okr_id = ? AND team_id = ? LIMIT 1",
                    (epic["product_okr_id"], epic["team_id"]),
                )
                if dokr_rows:
                    dokr_link_id = dokr_rows[0]["id"]

            # Decompose into 3 features using layer template
            effort_distribution = [2, 3, 2]
            for idx, (feat_name_tpl, feat_desc_tpl) in enumerate(templates):
                full_name = f"{feat_name_tpl}: {epic['name']}"

                dup_rows = await db.execute_fetchall(
                    "SELECT id FROM features WHERE name = ? AND epic_id = ? LIMIT 1",
                    (full_name, epic["id"]),
                )
                if dup_rows:
                    skipped.append(full_name)
                    continue

                effort = effort_distribution[idx]
                priority = round((epic_value * epic_size) / effort, 2) if effort else 0

                cur = await db.execute(
                    "INSERT INTO features (epic_id, delivery_okr_id, name, description, status, "
                    "value_score, size_score, effort_score, priority_score, "
                    "risk_level, risks, dependencies_text, roadmap_phase, ai_generated) "
                    "VALUES (?, ?, ?, ?, 'backlog', ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                    (epic["id"], dokr_link_id, full_name, feat_desc_tpl,
                     epic_value, epic_size, effort, priority,
                     risk_level, epic_risks, epic.get("dependencies_text"),
                     None),
                )
                created_features.append({
                    "id": cur.lastrowid, "name": full_name, "layer": layer,
                })

    await db.commit()

    return {
        "features": created_features,
        "delivery_okrs": created_dokrs,
        "feature_dependencies": created_feat_deps,
        "skipped": skipped,
        "ai_powered": ai_powered,
    }


# --- Feature Dependencies ---

@router.get("/feature-dependencies")
async def list_feature_dependencies(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT fd.*, f1.name as feature_name, f2.name as depends_on_name "
        "FROM feature_dependencies fd "
        "JOIN features f1 ON fd.feature_id = f1.id "
        "JOIN features f2 ON fd.depends_on_feature_id = f2.id"
    )
    return [dict(r) for r in rows]


@router.post("/feature-dependencies")
async def create_feature_dependency(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO feature_dependencies (feature_id, depends_on_feature_id, dependency_type, notes) "
        "VALUES (?, ?, ?, ?)",
        (data["feature_id"], data["depends_on_feature_id"],
         data.get("dependency_type", "blocks"), data.get("notes")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.delete("/feature-dependencies/{dep_id}")
async def delete_feature_dependency(dep_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM feature_dependencies WHERE id = ?", (dep_id,))
    await db.commit()
    return {"deleted": True}


# --- Features Full (rich nested data) ---

@router.get("/features-full")
async def get_features_full(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT f.*, "
        "e.name as epic_name, e.value_score as epic_value, e.size_score as epic_size, "
        "e.effort_score as epic_effort, e.priority_score as epic_priority, "
        "e.risk_level as epic_risk_level, e.initiative_id, "
        "i.name as initiative_name, i.rice_score, i.rice_override, "
        "s.layer as strategy_layer, s.name as strategy_name, "
        "dp.name as product_name, "
        "pg.name as product_group_name, "
        "t.name as team_name, "
        "do2.objective as delivery_okr_objective, "
        "po.objective as product_okr_objective "
        "FROM features f "
        "JOIN epics e ON f.epic_id = e.id "
        "JOIN initiatives i ON e.initiative_id = i.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "LEFT JOIN digital_products dp ON i.digital_product_id = dp.id "
        "LEFT JOIN product_groups pg ON dp.product_group_id = pg.id "
        "LEFT JOIN teams t ON e.team_id = t.id "
        "LEFT JOIN delivery_okrs do2 ON f.delivery_okr_id = do2.id "
        "LEFT JOIN product_okrs po ON e.product_okr_id = po.id "
        "ORDER BY f.priority_score DESC, f.id"
    )
    return [dict(r) for r in rows]


# --- Roadmap (features grouped by phase) ---

@router.get("/roadmap")
async def get_roadmap(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT f.*, e.name as epic_name, "
        "i.name as initiative_name, i.rice_score, i.rice_override, "
        "s.layer as strategy_layer, t.name as team_name "
        "FROM features f "
        "JOIN epics e ON f.epic_id = e.id "
        "JOIN initiatives i ON e.initiative_id = i.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "LEFT JOIN teams t ON e.team_id = t.id "
        "ORDER BY f.priority_score DESC"
    )
    features = [dict(r) for r in rows]

    quick_wins = []
    strategic = []
    long_term = []

    for f in features:
        phase = f.get("roadmap_phase")
        if not phase:
            priority = f.get("priority_score") or 0
            effort = f.get("effort_score") or 3
            if priority >= 4 and effort <= 2:
                phase = "quick_win"
            elif priority >= 2:
                phase = "strategic"
            else:
                phase = "long_term"
        if phase == "quick_win":
            quick_wins.append(f)
        elif phase == "strategic":
            strategic.append(f)
        else:
            long_term.append(f)

    return {
        "quick_wins": quick_wins,
        "strategic": strategic,
        "long_term": long_term,
        "total": len(features),
    }
