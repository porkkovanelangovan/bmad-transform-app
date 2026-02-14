from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter()

# --- Layer-specific epic templates (3 epics per initiative) ---
EPIC_TEMPLATES = {
    "business": [
        ("Market Analysis & Opportunity", "Analyze market positioning, competitive landscape, and identify growth opportunities"),
        ("Revenue Optimization Program", "Design and implement revenue growth strategies and optimization initiatives"),
        ("Customer Program & Experience", "Build customer-centric programs to improve satisfaction and retention"),
    ],
    "digital": [
        ("Platform Build & Infrastructure", "Architect and build core platform infrastructure and services"),
        ("Process Automation & Workflow", "Automate key business processes and optimize digital workflows"),
        ("Integration & API Development", "Develop integration layer and APIs for system interoperability"),
    ],
    "data": [
        ("Data Pipeline & Infrastructure", "Build data ingestion pipelines, storage, and processing infrastructure"),
        ("Dashboard & Analytics", "Create analytics dashboards and reporting capabilities"),
        ("Data Quality & Governance", "Implement data quality frameworks, governance policies, and compliance"),
    ],
    "gen_ai": [
        ("AI Model Development & Training", "Develop, train, and validate AI/ML models for target use cases"),
        ("AI Workflow Automation", "Integrate AI capabilities into business workflows and processes"),
        ("AI Governance & Team Training", "Establish AI governance frameworks and upskill teams on AI tools"),
    ],
}

# Cross-layer dependency rules: dependent_layer -> foundation_layer
CROSS_LAYER_DEPS = [
    ("gen_ai", "data"),
    ("data", "digital"),
    ("business", "digital"),
]


# --- Teams ---

@router.get("/teams")
async def list_teams(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT * FROM teams ORDER BY name")
    return [dict(r) for r in rows]


@router.post("/teams")
async def create_team(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO teams (name, capacity) VALUES (?, ?)",
        (data["name"], data.get("capacity")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Product OKRs ---

@router.get("/product-okrs")
async def list_product_okrs(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT po.*, so.objective as strategic_objective, dp.name as product_name "
        "FROM product_okrs po "
        "JOIN strategic_okrs so ON po.strategic_okr_id = so.id "
        "JOIN digital_products dp ON po.digital_product_id = dp.id"
    )
    return [dict(r) for r in rows]


@router.post("/product-okrs")
async def create_product_okr(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO product_okrs (strategic_okr_id, digital_product_id, objective, status) VALUES (?, ?, ?, ?)",
        (data["strategic_okr_id"], data["digital_product_id"], data["objective"], data.get("status", "draft")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Epics ---

@router.get("/epics")
async def list_epics(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT e.*, i.name as initiative_name, t.name as team_name "
        "FROM epics e "
        "JOIN initiatives i ON e.initiative_id = i.id "
        "LEFT JOIN teams t ON e.team_id = t.id "
        "ORDER BY e.priority_score DESC, e.status, e.target_date"
    )
    return [dict(r) for r in rows]


@router.post("/epics")
async def create_epic(data: dict, db=Depends(get_db)):
    value = data.get("value_score", 3)
    size = data.get("size_score", 3)
    effort = data.get("effort_score", 3)
    priority = (value * size) / effort if effort else 0
    cursor = await db.execute(
        "INSERT INTO epics (initiative_id, team_id, product_okr_id, name, description, status, "
        "start_date, target_date, value_score, size_score, effort_score, priority_score, "
        "risk_level, risks, dependencies_text, roadmap_phase) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data["initiative_id"], data.get("team_id"), data.get("product_okr_id"),
         data["name"], data.get("description"), data.get("status", "backlog"),
         data.get("start_date"), data.get("target_date"),
         value, size, effort, priority,
         data.get("risk_level", "medium"), data.get("risks"),
         data.get("dependencies_text"), data.get("roadmap_phase")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.put("/epics/{epic_id}")
async def update_epic(epic_id: int, data: dict, db=Depends(get_db)):
    allowed = [
        "team_id", "product_okr_id", "name", "description", "status",
        "start_date", "target_date", "value_score", "size_score", "effort_score",
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
        # Fetch current values to merge with updates
        cur = await db.execute("SELECT value_score, size_score, effort_score FROM epics WHERE id = ?", (epic_id,))
        row = await cur.fetchone()
        if row:
            v = data.get("value_score", row[0] or 3)
            s = data.get("size_score", row[1] or 3)
            e = data.get("effort_score", row[2] or 3)
            priority = (v * s) / e if e else 0
            fields.append("priority_score = ?")
            values.append(round(priority, 2))

    if fields:
        values.append(epic_id)
        await db.execute(f"UPDATE epics SET {', '.join(fields)} WHERE id = ?", values)
        await db.commit()
    return {"updated": True}


@router.delete("/epics/{epic_id}")
async def delete_epic(epic_id: int, db=Depends(get_db)):
    # Cascade delete: features -> epic_dependencies -> epic
    await db.execute("DELETE FROM features WHERE epic_id = ?", (epic_id,))
    await db.execute("DELETE FROM epic_dependencies WHERE epic_id = ? OR depends_on_epic_id = ?", (epic_id, epic_id))
    await db.execute("DELETE FROM epics WHERE id = ?", (epic_id,))
    await db.commit()
    return {"deleted": True}


# --- Dependencies ---

@router.get("/dependencies")
async def list_dependencies(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT ed.*, e1.name as epic_name, e2.name as depends_on_name "
        "FROM epic_dependencies ed "
        "JOIN epics e1 ON ed.epic_id = e1.id "
        "JOIN epics e2 ON ed.depends_on_epic_id = e2.id"
    )
    return [dict(r) for r in rows]


@router.post("/dependencies")
async def create_dependency(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO epic_dependencies (epic_id, depends_on_epic_id, dependency_type, notes) VALUES (?, ?, ?, ?)",
        (data["epic_id"], data["depends_on_epic_id"], data.get("dependency_type", "blocks"), data.get("notes")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.delete("/dependencies/{dep_id}")
async def delete_dependency(dep_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM epic_dependencies WHERE id = ?", (dep_id,))
    await db.commit()
    return {"deleted": True}


# --- Summary (for Generate tab) ---

@router.get("/summary")
async def get_summary(db=Depends(get_db)):
    init_cur = await db.execute(
        "SELECT COUNT(*) FROM initiatives WHERE status IN ('approved', 'proposed')"
    )
    init_count = (await init_cur.fetchone())[0]

    epic_cur = await db.execute("SELECT COUNT(*) FROM epics")
    epic_count = (await epic_cur.fetchone())[0]

    okr_cur = await db.execute("SELECT COUNT(*) FROM product_okrs")
    okr_count = (await okr_cur.fetchone())[0]

    team_cur = await db.execute("SELECT COUNT(*) FROM teams")
    team_count = (await team_cur.fetchone())[0]

    dep_cur = await db.execute("SELECT COUNT(*) FROM epic_dependencies")
    dep_count = (await dep_cur.fetchone())[0]

    return {
        "initiatives": init_count,
        "epics": epic_count,
        "product_okrs": okr_count,
        "teams": team_count,
        "dependencies": dep_count,
    }


# --- Auto-generate: Decompose initiatives -> epics + product OKRs + cross-layer deps ---

def _infer_risk_level(risks_text):
    """Infer risk level from initiative risks text using keywords."""
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
    # 1. Fetch initiatives with strategy context (approved/proposed)
    rows = await db.execute_fetchall(
        "SELECT i.*, s.layer as strategy_layer, s.name as strategy_name, "
        "dp.name as product_name, dp.id as product_id "
        "FROM initiatives i "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "LEFT JOIN digital_products dp ON i.digital_product_id = dp.id "
        "WHERE i.status IN ('approved', 'proposed') "
        "ORDER BY i.id"
    )
    initiatives = [dict(r) for r in rows]

    created_epics = []
    created_okrs = []
    created_deps = []
    skipped = []

    # Track first epic per layer for cross-layer dependencies
    layer_first_epics = {}  # layer -> first epic id created in this run or existing

    for init in initiatives:
        layer = init.get("strategy_layer") or "digital"
        templates = EPIC_TEMPLATES.get(layer, EPIC_TEMPLATES["digital"])
        init_value = init.get("value_score") or 3
        init_size = init.get("size_score") or 3
        init_risks = init.get("risks") or ""
        risk_level = _infer_risk_level(init_risks)

        # 2a. Create product OKRs from strategic OKRs if not exists
        if init.get("strategy_id") and init.get("product_id"):
            sokr_rows = await db.execute_fetchall(
                "SELECT so.* FROM strategic_okrs so WHERE so.strategy_id = ?",
                (init["strategy_id"],)
            )
            for sokr in sokr_rows:
                sokr = dict(sokr)
                # Check if product OKR already exists for this strategic OKR + product
                existing = await db.execute(
                    "SELECT id FROM product_okrs WHERE strategic_okr_id = ? AND digital_product_id = ?",
                    (sokr["id"], init["product_id"])
                )
                if await existing.fetchone():
                    continue
                obj_text = f"{sokr['objective']} ({init.get('product_name', 'Product')})"
                cur = await db.execute(
                    "INSERT INTO product_okrs (strategic_okr_id, digital_product_id, objective, status) VALUES (?, ?, ?, 'draft')",
                    (sokr["id"], init["product_id"], obj_text)
                )
                pokr_id = cur.lastrowid
                created_okrs.append({"id": pokr_id, "objective": obj_text})

                # Cascade key results
                kr_rows = await db.execute_fetchall(
                    "SELECT * FROM strategic_key_results WHERE okr_id = ?", (sokr["id"],)
                )
                for kr in kr_rows:
                    kr = dict(kr)
                    await db.execute(
                        "INSERT INTO product_key_results (product_okr_id, key_result, metric, current_value, target_value, unit) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (pokr_id, kr["key_result"], kr.get("metric"), kr.get("current_value", 0),
                         kr.get("target_value", 0), kr.get("unit"))
                    )

        # Find a product OKR to link epics to
        pokr_cur = await db.execute(
            "SELECT id FROM product_okrs WHERE digital_product_id = ? LIMIT 1",
            (init.get("product_id"),)
        )
        pokr_row = await pokr_cur.fetchone()
        pokr_id = pokr_row[0] if pokr_row else None

        # 2b. Decompose into 3 epics using layer template
        effort_distribution = [2, 3, 2]  # distribute effort across 3 epics
        for idx, (epic_name_tpl, epic_desc_tpl) in enumerate(templates):
            full_name = f"{epic_name_tpl}: {init['name']}"

            # Idempotent: skip if epic name + initiative_id already exists
            dup_cur = await db.execute(
                "SELECT id FROM epics WHERE name = ? AND initiative_id = ?",
                (full_name, init["id"])
            )
            dup_row = await dup_cur.fetchone()
            if dup_row:
                # Track existing first epic for cross-layer deps
                if idx == 0 and layer not in layer_first_epics:
                    layer_first_epics[layer] = dup_row[0]
                skipped.append(full_name)
                continue

            effort = effort_distribution[idx]
            priority = round((init_value * init_size) / effort, 2) if effort else 0

            cur = await db.execute(
                "INSERT INTO epics (initiative_id, product_okr_id, name, description, status, "
                "value_score, size_score, effort_score, priority_score, risk_level, risks, "
                "dependencies_text, roadmap_phase) "
                "VALUES (?, ?, ?, ?, 'backlog', ?, ?, ?, ?, ?, ?, ?, ?)",
                (init["id"], pokr_id, full_name, epic_desc_tpl,
                 init_value, init_size, effort, priority,
                 risk_level, init_risks, init.get("dependencies"),
                 None)  # roadmap_phase auto-classified in roadmap endpoint
            )
            epic_id = cur.lastrowid
            created_epics.append({"id": epic_id, "name": full_name, "layer": layer})

            # Track first epic per layer
            if idx == 0 and layer not in layer_first_epics:
                layer_first_epics[layer] = epic_id

    # 3. Create cross-layer dependencies
    for dep_layer, foundation_layer in CROSS_LAYER_DEPS:
        dep_epic = layer_first_epics.get(dep_layer)
        found_epic = layer_first_epics.get(foundation_layer)
        if dep_epic and found_epic and dep_epic != found_epic:
            # Check if dependency already exists
            existing = await db.execute(
                "SELECT id FROM epic_dependencies WHERE epic_id = ? AND depends_on_epic_id = ?",
                (dep_epic, found_epic)
            )
            if not await existing.fetchone():
                cur = await db.execute(
                    "INSERT INTO epic_dependencies (epic_id, depends_on_epic_id, dependency_type, notes) "
                    "VALUES (?, ?, 'blocks', ?)",
                    (dep_epic, found_epic, f"Auto: {dep_layer} depends on {foundation_layer}")
                )
                created_deps.append({
                    "id": cur.lastrowid,
                    "from_layer": dep_layer,
                    "to_layer": foundation_layer,
                })

    await db.commit()

    return {
        "epics": created_epics,
        "product_okrs": created_okrs,
        "dependencies": created_deps,
        "skipped": skipped,
    }


# --- Epics Full (rich nested data) ---

@router.get("/epics-full")
async def get_epics_full(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT e.*, "
        "i.name as initiative_name, i.rice_score, i.rice_override, i.status as initiative_status, "
        "s.layer as strategy_layer, s.name as strategy_name, "
        "dp.name as product_name, dp.id as product_id, "
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
        "ORDER BY e.priority_score DESC, e.id"
    )
    epics = [dict(r) for r in rows]

    # Attach dependency info (both directions) per epic
    all_deps = await db.execute_fetchall(
        "SELECT ed.*, e1.name as epic_name, e2.name as depends_on_name "
        "FROM epic_dependencies ed "
        "JOIN epics e1 ON ed.epic_id = e1.id "
        "JOIN epics e2 ON ed.depends_on_epic_id = e2.id"
    )
    deps_list = [dict(d) for d in all_deps]

    for epic in epics:
        eid = epic["id"]
        epic["depends_on"] = [
            {"id": d["depends_on_epic_id"], "name": d["depends_on_name"], "dep_id": d["id"]}
            for d in deps_list if d["epic_id"] == eid
        ]
        epic["blocks"] = [
            {"id": d["epic_id"], "name": d["epic_name"], "dep_id": d["id"]}
            for d in deps_list if d["depends_on_epic_id"] == eid
        ]

        # Attach product key results
        if epic.get("product_okr_id"):
            kr_rows = await db.execute_fetchall(
                "SELECT * FROM product_key_results WHERE product_okr_id = ? ORDER BY id",
                (epic["product_okr_id"],),
            )
            epic["product_key_results"] = [dict(kr) for kr in kr_rows]
        else:
            epic["product_key_results"] = []

    return epics


# --- Roadmap (epics grouped by phase) ---

@router.get("/roadmap")
async def get_roadmap(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT e.*, i.name as initiative_name, i.rice_score, i.rice_override, "
        "s.layer as strategy_layer, t.name as team_name "
        "FROM epics e "
        "JOIN initiatives i ON e.initiative_id = i.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "LEFT JOIN teams t ON e.team_id = t.id "
        "ORDER BY e.priority_score DESC"
    )
    epics = [dict(r) for r in rows]

    # Count dependencies per epic
    dep_rows = await db.execute_fetchall(
        "SELECT epic_id, COUNT(*) as cnt FROM epic_dependencies GROUP BY epic_id"
    )
    dep_counts = {d["epic_id"]: d["cnt"] for d in dep_rows}

    quick_wins = []
    strategic = []
    long_term = []

    for e in epics:
        e["dep_count"] = dep_counts.get(e["id"], 0)
        # Manual override takes precedence
        phase = e.get("roadmap_phase")
        if not phase:
            priority = e.get("priority_score") or 0
            effort = e.get("effort_score") or 3
            if priority >= 4 and effort <= 2:
                phase = "quick_win"
            elif priority >= 2:
                phase = "strategic"
            else:
                phase = "long_term"
        if phase == "quick_win":
            quick_wins.append(e)
        elif phase == "strategic":
            strategic.append(e)
        else:
            long_term.append(e)

    # Dependency edges for visualization
    edge_rows = await db.execute_fetchall(
        "SELECT epic_id, depends_on_epic_id FROM epic_dependencies"
    )
    edges = [{"from": r["epic_id"], "to": r["depends_on_epic_id"]} for r in edge_rows]

    return {
        "quick_wins": quick_wins,
        "strategic": strategic,
        "long_term": long_term,
        "total": len(epics),
        "dependency_edges": edges,
    }
