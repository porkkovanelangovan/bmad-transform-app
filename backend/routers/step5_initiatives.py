from fastapi import APIRouter, Depends
from database import get_db
from ai_initiatives import gather_initiative_context, generate_ai_initiatives
from ai_research import is_openai_available

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


async def _ensure_product_group(db, layer):
    """Ensure product group exists for a strategy layer, return group_id."""
    group_name = LAYER_LABELS.get(layer, layer.title())
    existing_group = await db.execute_fetchall(
        "SELECT id FROM product_groups WHERE name = ?", (group_name,)
    )
    if existing_group:
        return dict(existing_group[0])["id"], False
    cursor = await db.execute(
        "INSERT INTO product_groups (name, description) VALUES (?, ?)",
        (group_name, f"Product group for {layer} layer strategies"),
    )
    return cursor.lastrowid, True


async def _ensure_digital_product(db, group_id, name, description=""):
    """Ensure digital product exists, return product_id."""
    existing = await db.execute_fetchall(
        "SELECT id FROM digital_products WHERE product_group_id = ? AND name = ?",
        (group_id, name),
    )
    if existing:
        return dict(existing[0])["id"], False
    cursor = await db.execute(
        "INSERT INTO digital_products (product_group_id, name, description) VALUES (?, ?, ?)",
        (group_id, name, description),
    )
    return cursor.lastrowid, True


@router.post("/auto-generate")
async def auto_generate_initiatives(db=Depends(get_db)):
    """Generate initiatives from approved strategies and their OKRs."""
    # Fetch approved strategies with OKRs
    strategies = await db.execute_fetchall(
        "SELECT * FROM strategies WHERE approved = 1 ORDER BY layer, id"
    )
    if not strategies:
        return {"error": "No approved strategies found. Approve strategies in Step 4 first."}

    ai_powered = False
    created_initiatives = 0
    created_products = 0
    created_groups = 0

    # Build strategy lookup for matching AI results
    strategy_list = [dict(s) for s in strategies]
    strategy_lookup = {}
    for s in strategy_list:
        strategy_lookup[(s["name"], s["layer"])] = s
        strategy_lookup[s["name"]] = s  # also by name alone for fuzzy matching

    # Try AI-powered generation
    if is_openai_available():
        context = await gather_initiative_context(db)
        ai_initiatives = await generate_ai_initiatives(context)

        if ai_initiatives:
            ai_powered = True
            for ai_init in ai_initiatives:
                # Match to strategy
                s_dict = strategy_lookup.get(
                    (ai_init["strategy_name"], ai_init["strategy_layer"])
                ) or strategy_lookup.get(ai_init["strategy_name"])

                if not s_dict:
                    # Fallback: use first strategy of matching layer
                    for sl in strategy_list:
                        if sl["layer"] == ai_init.get("strategy_layer"):
                            s_dict = sl
                            break
                if not s_dict:
                    s_dict = strategy_list[0]

                layer = s_dict["layer"]
                strategy_id = s_dict["id"]

                # Ensure product group + digital product
                group_id, new_group = await _ensure_product_group(db, layer)
                if new_group:
                    created_groups += 1

                product_id, new_product = await _ensure_digital_product(
                    db, group_id, s_dict["name"], s_dict.get("description", "")
                )
                if new_product:
                    created_products += 1

                init_name = ai_init["name"][:80]

                # Skip if already exists
                existing_init = await db.execute_fetchall(
                    "SELECT id FROM initiatives WHERE name = ? AND strategy_id = ?",
                    (init_name, strategy_id),
                )
                if existing_init:
                    continue

                await db.execute(
                    "INSERT INTO initiatives (digital_product_id, strategy_id, name, description, "
                    "reach, impact, confidence, effort, value_score, size_score, "
                    "impacted_segments, dependencies, risks, roadmap_phase, "
                    "ai_generated, ai_rationale, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 'proposed')",
                    (product_id, strategy_id, init_name, ai_init.get("description", ""),
                     ai_init["reach"], ai_init["impact"], ai_init["confidence"], ai_init["effort"],
                     ai_init.get("value_score", 3), ai_init.get("size_score", 3),
                     ai_init.get("impacted_segments"), ai_init.get("dependencies"),
                     ai_init.get("risks"), ai_init.get("roadmap_phase"),
                     ai_init.get("rationale")),
                )
                created_initiatives += 1

    # Fallback: rule-based generation (if AI not available or failed)
    if not ai_powered:
        for s in strategy_list:
            layer = s["layer"]
            strategy_id = s["id"]

            group_id, new_group = await _ensure_product_group(db, layer)
            if new_group:
                created_groups += 1

            product_id, new_product = await _ensure_digital_product(
                db, group_id, s["name"], s.get("description", "")
            )
            if new_product:
                created_products += 1

            okrs = await db.execute_fetchall(
                "SELECT * FROM strategic_okrs WHERE strategy_id = ?", (strategy_id,)
            )

            rice = LAYER_RICE_DEFAULTS.get(layer, {"reach": 3, "impact": 1, "confidence": 0.8, "effort": 3})

            for okr in okrs:
                okr_dict = dict(okr)
                krs = await db.execute_fetchall(
                    "SELECT key_result FROM strategic_key_results WHERE okr_id = ?", (okr_dict["id"],)
                )
                kr_text = "; ".join(dict(kr)["key_result"] for kr in krs) if krs else ""

                init_name = f"{okr_dict['objective'][:80]}"
                init_desc = f"Initiative from {layer} strategy '{s['name']}'. Key results: {kr_text}" if kr_text else f"Initiative from {layer} strategy '{s['name']}'"

                existing_init = await db.execute_fetchall(
                    "SELECT id FROM initiatives WHERE name = ? AND strategy_id = ?",
                    (init_name, strategy_id),
                )
                if existing_init:
                    continue

                await db.execute(
                    "INSERT INTO initiatives (digital_product_id, strategy_id, name, description, "
                    "reach, impact, confidence, effort, value_score, size_score, "
                    "ai_generated, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'proposed')",
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
        "ai_powered": ai_powered,
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
