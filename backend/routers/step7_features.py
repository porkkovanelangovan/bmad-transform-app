from fastapi import APIRouter, Depends
from database import get_db

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
        cur = await db.execute(
            "SELECT value_score, size_score, effort_score FROM features WHERE id = ?",
            (feature_id,),
        )
        row = await cur.fetchone()
        if row:
            v = data.get("value_score", row[0] or 3)
            s = data.get("size_score", row[1] or 3)
            e = data.get("effort_score", row[2] or 3)
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
    epic_cur = await db.execute("SELECT COUNT(*) FROM epics")
    epic_count = (await epic_cur.fetchone())[0]

    feat_cur = await db.execute("SELECT COUNT(*) FROM features")
    feat_count = (await feat_cur.fetchone())[0]

    dokr_cur = await db.execute("SELECT COUNT(*) FROM delivery_okrs")
    dokr_count = (await dokr_cur.fetchone())[0]

    team_cur = await db.execute("SELECT COUNT(*) FROM teams")
    team_count = (await team_cur.fetchone())[0]

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
        "s.layer as strategy_layer, "
        "dp.id as product_id, dp.name as product_name, "
        "pg.name as product_group_name, "
        "t.name as team_name "
        "FROM epics e "
        "JOIN initiatives i ON e.initiative_id = i.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "LEFT JOIN digital_products dp ON i.digital_product_id = dp.id "
        "LEFT JOIN product_groups pg ON dp.product_group_id = pg.id "
        "LEFT JOIN teams t ON e.team_id = t.id "
        "ORDER BY e.id"
    )
    epics = [dict(r) for r in rows]

    created_features = []
    created_dokrs = []
    skipped = []

    for epic in epics:
        layer = epic.get("strategy_layer") or "digital"
        templates = FEATURE_TEMPLATES.get(layer, FEATURE_TEMPLATES["digital"])
        epic_value = epic.get("value_score") or 3
        epic_size = epic.get("size_score") or 3
        epic_risks = epic.get("risks") or ""
        risk_level = epic.get("risk_level") or _infer_risk_level(epic_risks)

        # Create delivery OKR if epic has product_okr_id AND team_id and doesn't exist yet
        if epic.get("product_okr_id") and epic.get("team_id"):
            existing_dokr = await db.execute(
                "SELECT id FROM delivery_okrs WHERE product_okr_id = ? AND team_id = ?",
                (epic["product_okr_id"], epic["team_id"]),
            )
            if not await existing_dokr.fetchone():
                # Fetch product OKR objective to cascade
                pokr_cur = await db.execute(
                    "SELECT objective FROM product_okrs WHERE id = ?",
                    (epic["product_okr_id"],),
                )
                pokr_row = await pokr_cur.fetchone()
                if pokr_row:
                    dokr_obj = f"Deliver: {pokr_row[0]}"
                    dokr_cur = await db.execute(
                        "INSERT INTO delivery_okrs (product_okr_id, team_id, objective, status) "
                        "VALUES (?, ?, ?, 'draft')",
                        (epic["product_okr_id"], epic["team_id"], dokr_obj),
                    )
                    dokr_id = dokr_cur.lastrowid
                    created_dokrs.append({"id": dokr_id, "objective": dokr_obj})

                    # Cascade key results from product_key_results -> delivery_key_results
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

        # Find delivery OKR to link features to
        dokr_link_id = None
        if epic.get("product_okr_id") and epic.get("team_id"):
            dokr_cur = await db.execute(
                "SELECT id FROM delivery_okrs WHERE product_okr_id = ? AND team_id = ? LIMIT 1",
                (epic["product_okr_id"], epic["team_id"]),
            )
            dokr_row = await dokr_cur.fetchone()
            if dokr_row:
                dokr_link_id = dokr_row[0]

        # Decompose into 3 features using layer template
        effort_distribution = [2, 3, 2]
        for idx, (feat_name_tpl, feat_desc_tpl) in enumerate(templates):
            full_name = f"{feat_name_tpl}: {epic['name']}"

            # Idempotent: skip if feature name + epic_id already exists
            dup_cur = await db.execute(
                "SELECT id FROM features WHERE name = ? AND epic_id = ?",
                (full_name, epic["id"]),
            )
            if await dup_cur.fetchone():
                skipped.append(full_name)
                continue

            effort = effort_distribution[idx]
            priority = round((epic_value * epic_size) / effort, 2) if effort else 0

            cur = await db.execute(
                "INSERT INTO features (epic_id, delivery_okr_id, name, description, status, "
                "value_score, size_score, effort_score, priority_score, "
                "risk_level, risks, dependencies_text, roadmap_phase) "
                "VALUES (?, ?, ?, ?, 'backlog', ?, ?, ?, ?, ?, ?, ?, ?)",
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
        "skipped": skipped,
    }


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
