from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter()


# --- Product Groups ---

@router.get("/product-groups")
async def list_product_groups(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT * FROM product_groups ORDER BY name")
    return [dict(r) for r in rows]


@router.post("/product-groups")
async def create_product_group(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO product_groups (name, description) VALUES (?, ?)",
        (data["name"], data.get("description")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Digital Products ---

@router.get("/digital-products")
async def list_digital_products(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT dp.*, pg.name as product_group_name FROM digital_products dp "
        "JOIN product_groups pg ON dp.product_group_id = pg.id"
    )
    return [dict(r) for r in rows]


@router.post("/digital-products")
async def create_digital_product(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO digital_products (product_group_id, name, description) VALUES (?, ?, ?)",
        (data["product_group_id"], data["name"], data.get("description")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# --- Initiatives with RICE ---

@router.get("/initiatives")
async def list_initiatives(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT i.*, dp.name as product_name, s.name as strategy_name, s.layer as strategy_layer "
        "FROM initiatives i "
        "JOIN digital_products dp ON i.digital_product_id = dp.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "ORDER BY COALESCE(i.rice_override, i.rice_score) DESC"
    )
    return [dict(r) for r in rows]


@router.get("/initiatives-full")
async def list_initiatives_full(db=Depends(get_db)):
    """Return initiatives with nested strategic OKRs and key results."""
    rows = await db.execute_fetchall(
        "SELECT i.*, dp.name as product_name, s.name as strategy_name, s.layer as strategy_layer "
        "FROM initiatives i "
        "JOIN digital_products dp ON i.digital_product_id = dp.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "ORDER BY COALESCE(i.rice_override, i.rice_score) DESC"
    )
    initiatives = [dict(r) for r in rows]

    for init in initiatives:
        if init.get("strategy_id"):
            okrs = await db.execute_fetchall(
                "SELECT * FROM strategic_okrs WHERE strategy_id = ? ORDER BY id",
                (init["strategy_id"],),
            )
            okr_list = []
            for o in okrs:
                o_dict = dict(o)
                krs = await db.execute_fetchall(
                    "SELECT * FROM strategic_key_results WHERE okr_id = ? ORDER BY id",
                    (o_dict["id"],),
                )
                o_dict["key_results"] = [dict(kr) for kr in krs]
                okr_list.append(o_dict)
            init["strategic_okrs"] = okr_list
        else:
            init["strategic_okrs"] = []

    return initiatives


@router.post("/initiatives")
async def create_initiative(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO initiatives (digital_product_id, strategy_id, name, description, "
        "reach, impact, confidence, effort, value_score, size_score, "
        "impacted_segments, dependencies, risks, roadmap_phase, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data["digital_product_id"], data.get("strategy_id"), data["name"], data.get("description"),
         data.get("reach", 1), data.get("impact", 1), data.get("confidence", 1.0),
         data.get("effort", 1), data.get("value_score", 3), data.get("size_score", 3),
         data.get("impacted_segments"), data.get("dependencies"), data.get("risks"),
         data.get("roadmap_phase"), data.get("status", "proposed")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.put("/initiatives/{init_id}")
async def update_initiative(init_id: int, data: dict, db=Depends(get_db)):
    fields = []
    values = []
    for key in ["reach", "impact", "confidence", "effort", "rice_override",
                "rice_override_reason", "status", "name", "description",
                "value_score", "size_score", "impacted_segments",
                "dependencies", "risks", "roadmap_phase"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if fields:
        values.append(init_id)
        await db.execute(f"UPDATE initiatives SET {', '.join(fields)} WHERE id = ?", values)
        await db.commit()
    return {"updated": True}


# ===================== Auto-Generate from Strategies =====================

LAYER_LABELS = {
    "business": "Business Strategy",
    "digital": "Digital Transformation",
    "data": "Data & Analytics",
    "gen_ai": "Gen AI & Automation",
}

LAYER_RICE_DEFAULTS = {
    "business": {"reach": 5, "impact": 2, "confidence": 0.8, "effort": 4},
    "digital": {"reach": 3, "impact": 2, "confidence": 0.8, "effort": 3},
    "data": {"reach": 4, "impact": 1, "confidence": 0.8, "effort": 2},
    "gen_ai": {"reach": 2, "impact": 3, "confidence": 0.5, "effort": 3},
}


@router.post("/auto-generate")
async def auto_generate_initiatives(db=Depends(get_db)):
    """Generate initiatives from approved strategies and their OKRs."""
    # Fetch approved strategies with OKRs
    strategies = await db.execute_fetchall(
        "SELECT * FROM strategies WHERE approved = 1 ORDER BY layer, id"
    )
    if not strategies:
        return {"error": "No approved strategies found. Approve strategies in Step 4 first."}

    created_initiatives = 0
    created_products = 0
    created_groups = 0

    for s in strategies:
        s_dict = dict(s)
        layer = s_dict["layer"]
        strategy_id = s_dict["id"]
        group_name = LAYER_LABELS.get(layer, layer.title())

        # Ensure product group exists
        existing_group = await db.execute_fetchall(
            "SELECT id FROM product_groups WHERE name = ?", (group_name,)
        )
        if existing_group:
            group_id = dict(existing_group[0])["id"]
        else:
            cursor = await db.execute(
                "INSERT INTO product_groups (name, description) VALUES (?, ?)",
                (group_name, f"Product group for {layer} layer strategies"),
            )
            group_id = cursor.lastrowid
            created_groups += 1

        # Ensure digital product exists for this strategy
        product_name = s_dict["name"]
        existing_product = await db.execute_fetchall(
            "SELECT id FROM digital_products WHERE product_group_id = ? AND name = ?",
            (group_id, product_name),
        )
        if existing_product:
            product_id = dict(existing_product[0])["id"]
        else:
            cursor = await db.execute(
                "INSERT INTO digital_products (product_group_id, name, description) VALUES (?, ?, ?)",
                (group_id, product_name, s_dict.get("description", "")),
            )
            product_id = cursor.lastrowid
            created_products += 1

        # Fetch OKRs for this strategy
        okrs = await db.execute_fetchall(
            "SELECT * FROM strategic_okrs WHERE strategy_id = ?", (strategy_id,)
        )

        rice = LAYER_RICE_DEFAULTS.get(layer, {"reach": 3, "impact": 1, "confidence": 0.8, "effort": 3})

        for okr in okrs:
            okr_dict = dict(okr)
            # Fetch key results for initiative description
            krs = await db.execute_fetchall(
                "SELECT key_result FROM strategic_key_results WHERE okr_id = ?", (okr_dict["id"],)
            )
            kr_text = "; ".join(dict(kr)["key_result"] for kr in krs) if krs else ""

            init_name = f"{okr_dict['objective'][:80]}"
            init_desc = f"Initiative from {layer} strategy '{s_dict['name']}'. Key results: {kr_text}" if kr_text else f"Initiative from {layer} strategy '{s_dict['name']}'"

            # Skip if already exists (idempotent)
            existing_init = await db.execute_fetchall(
                "SELECT id FROM initiatives WHERE name = ? AND strategy_id = ?",
                (init_name, strategy_id),
            )
            if existing_init:
                continue

            await db.execute(
                "INSERT INTO initiatives (digital_product_id, strategy_id, name, description, "
                "reach, impact, confidence, effort, value_score, size_score, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed')",
                (product_id, strategy_id, init_name, init_desc,
                 rice["reach"], rice["impact"], rice["confidence"], rice["effort"],
                 3, 3),
            )
            created_initiatives += 1

    await db.commit()
    return {
        "initiatives": created_initiatives,
        "products": created_products,
        "groups": created_groups,
    }


# ===================== Roadmap =====================

@router.get("/roadmap")
async def get_roadmap(db=Depends(get_db)):
    """Return initiatives grouped by phase (quick_win/strategic/long_term)."""
    rows = await db.execute_fetchall(
        "SELECT i.*, dp.name as product_name, s.name as strategy_name, s.layer as strategy_layer "
        "FROM initiatives i "
        "JOIN digital_products dp ON i.digital_product_id = dp.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "ORDER BY COALESCE(i.rice_override, i.rice_score) DESC"
    )

    quick_wins = []
    strategic = []
    long_term = []

    for r in rows:
        item = dict(r)
        rice = item.get("rice_override") or item.get("rice_score") or 0
        effort = item.get("effort") or 1

        # Manual override takes precedence
        phase = item.get("roadmap_phase")
        if not phase:
            if rice >= 3 and effort <= 2:
                phase = "quick_win"
            elif rice >= 2 and effort <= 4:
                phase = "strategic"
            else:
                phase = "long_term"

        item["computed_phase"] = phase

        if phase == "quick_win":
            quick_wins.append(item)
        elif phase == "strategic":
            strategic.append(item)
        else:
            long_term.append(item)

    return {
        "quick_wins": quick_wins,
        "strategic": strategic,
        "long_term": long_term,
        "total": len(quick_wins) + len(strategic) + len(long_term),
    }
