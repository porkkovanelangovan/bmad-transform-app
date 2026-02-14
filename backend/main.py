from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from routers import (
    step1_performance,
    step2_value_streams,
    step3_swot_tows,
    step4_strategy_okrs,
    step5_initiatives,
    step6_epics_teams,
    step7_features,
    review_gates,
)

app = FastAPI(title="BMAD Business Transformation Tool", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(step1_performance.router, prefix="/api/step1", tags=["Step 1: Performance"])
app.include_router(step2_value_streams.router, prefix="/api/step2", tags=["Step 2: Value Streams"])
app.include_router(step3_swot_tows.router, prefix="/api/step3", tags=["Step 3: SWOT/TOWS"])
app.include_router(step4_strategy_okrs.router, prefix="/api/step4", tags=["Step 4: Strategy & OKRs"])
app.include_router(step5_initiatives.router, prefix="/api/step5", tags=["Step 5: Initiatives & RICE"])
app.include_router(step6_epics_teams.router, prefix="/api/step6", tags=["Step 6: Epics & Teams"])
app.include_router(step7_features.router, prefix="/api/step7", tags=["Step 7: Features & Roadmap"])
app.include_router(review_gates.router, prefix="/api/gates", tags=["Review Gates"])

@app.on_event("startup")
async def startup_migrate():
    """Initialize database from schema.sql if fresh, then apply column migrations for existing DBs."""
    import aiosqlite
    from database import DB_PATH

    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if DB is fresh (no tables yet)
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organization'")
        exists = await cursor.fetchone()

        if not exists:
            # Fresh DB: run full schema
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            await db.executescript(schema_sql)
        else:
            # Existing DB: add new columns if missing
            for col in ["competitor_1_name TEXT", "competitor_2_name TEXT"]:
                try:
                    await db.execute(f"ALTER TABLE organization ADD COLUMN {col}")
                except Exception:
                    pass

            for col in [
                "ticker TEXT", "revenue REAL", "profit_margin REAL",
                "operating_margin REAL", "return_on_equity REAL",
                "return_on_assets REAL", "pe_ratio REAL", "eps REAL",
                "market_cap_value REAL",
            ]:
                try:
                    await db.execute(f"ALTER TABLE competitors ADD COLUMN {col}")
                except Exception:
                    pass

            # New Step 2 tables for value stream mapping
            await db.execute("""CREATE TABLE IF NOT EXISTS value_stream_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
                step_order INTEGER NOT NULL,
                step_name TEXT NOT NULL,
                description TEXT,
                step_type TEXT NOT NULL DEFAULT 'process' CHECK (step_type IN ('trigger', 'process', 'decision', 'delivery')),
                process_time_hours REAL DEFAULT 0,
                wait_time_hours REAL DEFAULT 0,
                lead_time_hours REAL DEFAULT 0,
                resources TEXT,
                is_bottleneck INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS value_stream_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value_stream_id INTEGER NOT NULL UNIQUE REFERENCES value_streams(id),
                total_lead_time_hours REAL DEFAULT 0,
                total_process_time_hours REAL DEFAULT 0,
                total_wait_time_hours REAL DEFAULT 0,
                flow_efficiency REAL DEFAULT 0,
                bottleneck_step TEXT,
                bottleneck_reason TEXT,
                data_source TEXT DEFAULT 'manual' CHECK (data_source IN ('ai_generated', 'template', 'uploaded', 'manual')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS value_stream_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
                competitor_name TEXT NOT NULL,
                total_lead_time_hours REAL,
                total_process_time_hours REAL,
                flow_efficiency REAL,
                bottleneck_step TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            # --- Step 4 migrations: strategy_inputs table, approved column, 'data' layer ---
            await db.execute("""CREATE TABLE IF NOT EXISTS strategy_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_type TEXT NOT NULL CHECK (input_type IN (
                    'business_strategy', 'digital_strategy', 'data_strategy', 'gen_ai_strategy',
                    'competitor_strategy', 'ongoing_initiatives', 'document_reference'
                )),
                title TEXT,
                content TEXT NOT NULL,
                file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            try:
                await db.execute("ALTER TABLE strategies ADD COLUMN approved INTEGER DEFAULT 0")
            except Exception:
                pass

            # Rebuild strategies table to expand layer CHECK to include 'data'
            # Also fix any FK references broken by previous rename migrations
            needs_rebuild = False
            try:
                await db.execute("INSERT INTO strategies (layer, name, description) VALUES ('data', '__migration_test__', NULL)")
                await db.execute("DELETE FROM strategies WHERE name = '__migration_test__'")
            except Exception:
                needs_rebuild = True

            # Check if any tables have broken FK references to strategies_old
            fk_broken = False
            for tbl_name in ['strategic_okrs', 'initiatives']:
                cursor = await db.execute("SELECT sql FROM sqlite_master WHERE name = ?", (tbl_name,))
                row = await cursor.fetchone()
                if row and 'strategies_old' in (row[0] or ''):
                    fk_broken = True
                    break

            if needs_rebuild or fk_broken:
                try:
                    await db.execute("PRAGMA foreign_keys = OFF")

                    if needs_rebuild:
                        await db.execute("DROP TABLE IF EXISTS strategies_old")
                        await db.execute("ALTER TABLE strategies RENAME TO strategies_old")
                        await db.execute("""CREATE TABLE strategies (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            layer TEXT NOT NULL CHECK (layer IN ('business', 'digital', 'data', 'gen_ai')),
                            name TEXT NOT NULL,
                            description TEXT,
                            tows_action_id INTEGER REFERENCES tows_actions(id),
                            approved INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""")
                        await db.execute("""INSERT INTO strategies (id, layer, name, description, tows_action_id, approved, created_at)
                            SELECT id, layer, name, description, tows_action_id,
                                   COALESCE(approved, 0), created_at FROM strategies_old""")
                        await db.execute("DROP TABLE strategies_old")

                    if fk_broken:
                        # Rebuild strategic_okrs to fix FK reference
                        await db.execute("ALTER TABLE strategic_okrs RENAME TO strategic_okrs_old")
                        await db.execute("""CREATE TABLE strategic_okrs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            strategy_id INTEGER NOT NULL REFERENCES strategies(id),
                            objective TEXT NOT NULL,
                            time_horizon TEXT,
                            status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""")
                        await db.execute("""INSERT INTO strategic_okrs (id, strategy_id, objective, time_horizon, status, created_at)
                            SELECT id, strategy_id, objective, time_horizon, status, created_at FROM strategic_okrs_old""")
                        await db.execute("DROP TABLE strategic_okrs_old")

                        # Rebuild strategic_key_results too if it references old table
                        cursor2 = await db.execute("SELECT sql FROM sqlite_master WHERE name = 'strategic_key_results'")
                        kr_row = await cursor2.fetchone()
                        if kr_row and 'okrs_old' in (kr_row[0] or ''):
                            await db.execute("ALTER TABLE strategic_key_results RENAME TO strategic_key_results_old")
                            await db.execute("""CREATE TABLE strategic_key_results (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
                                key_result TEXT NOT NULL,
                                metric TEXT,
                                current_value REAL DEFAULT 0,
                                target_value REAL NOT NULL,
                                unit TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )""")
                            await db.execute("""INSERT INTO strategic_key_results (id, okr_id, key_result, metric, current_value, target_value, unit, created_at)
                                SELECT id, okr_id, key_result, metric, current_value, target_value, unit, created_at FROM strategic_key_results_old""")
                            await db.execute("DROP TABLE strategic_key_results_old")

                        # Rebuild initiatives table if it references strategies_old
                        cursor3 = await db.execute("SELECT sql FROM sqlite_master WHERE name = 'initiatives'")
                        init_row = await cursor3.fetchone()
                        if init_row and 'strategies_old' in (init_row[0] or ''):
                            await db.execute("ALTER TABLE initiatives RENAME TO initiatives_old")
                            await db.execute("""CREATE TABLE initiatives (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
                                strategy_id INTEGER REFERENCES strategies(id),
                                name TEXT NOT NULL,
                                description TEXT,
                                reach INTEGER NOT NULL DEFAULT 1,
                                impact REAL NOT NULL DEFAULT 1 CHECK (impact IN (0.25, 0.5, 1, 2, 3)),
                                confidence REAL NOT NULL DEFAULT 1 CHECK (confidence IN (0.5, 0.8, 1.0)),
                                effort INTEGER NOT NULL DEFAULT 1,
                                rice_score REAL GENERATED ALWAYS AS ((reach * impact * confidence * 1.0) / effort) STORED,
                                rice_override REAL,
                                rice_override_reason TEXT,
                                value_score INTEGER DEFAULT 3,
                                size_score INTEGER DEFAULT 3,
                                impacted_segments TEXT,
                                dependencies TEXT,
                                risks TEXT,
                                roadmap_phase TEXT,
                                status TEXT DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'in_progress', 'completed', 'deferred')),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )""")
                            await db.execute("""INSERT INTO initiatives (id, digital_product_id, strategy_id, name, description,
                                reach, impact, confidence, effort, rice_override, rice_override_reason,
                                value_score, size_score, impacted_segments, dependencies, risks, roadmap_phase,
                                status, created_at)
                                SELECT id, digital_product_id, strategy_id, name, description,
                                reach, impact, confidence, effort, rice_override, rice_override_reason,
                                COALESCE(value_score, 3), COALESCE(size_score, 3), impacted_segments, dependencies, risks, roadmap_phase,
                                status, created_at FROM initiatives_old""")
                            await db.execute("DROP TABLE initiatives_old")

                    await db.execute("PRAGMA foreign_keys = ON")
                except Exception:
                    await db.execute("PRAGMA foreign_keys = ON")

            # --- Step 5 migrations: new initiative columns ---
            for col in [
                "value_score INTEGER DEFAULT 3",
                "size_score INTEGER DEFAULT 3",
                "impacted_segments TEXT",
                "dependencies TEXT",
                "risks TEXT",
                "roadmap_phase TEXT",
            ]:
                try:
                    await db.execute(f"ALTER TABLE initiatives ADD COLUMN {col}")
                except Exception:
                    pass

            # --- Step 6 migrations: new epic columns ---
            for col in [
                "value_score INTEGER DEFAULT 3",
                "size_score INTEGER DEFAULT 3",
                "effort_score INTEGER DEFAULT 3",
                "priority_score REAL DEFAULT 0",
                "risk_level TEXT DEFAULT 'medium'",
                "risks TEXT",
                "dependencies_text TEXT",
                "roadmap_phase TEXT",
            ]:
                try:
                    await db.execute(f"ALTER TABLE epics ADD COLUMN {col}")
                except Exception:
                    pass

            # --- Step 7 migrations: new feature scoring columns ---
            for col in [
                "value_score INTEGER DEFAULT 3", "size_score INTEGER DEFAULT 3",
                "effort_score INTEGER DEFAULT 3", "priority_score REAL DEFAULT 0",
                "risk_level TEXT DEFAULT 'medium'", "risks TEXT",
                "dependencies_text TEXT", "roadmap_phase TEXT",
            ]:
                try:
                    await db.execute(f"ALTER TABLE features ADD COLUMN {col}")
                except Exception:
                    pass

            # Fix broken FKs: rebuild any table whose CREATE SQL contains
            # references to renamed tables (_old or _rebuild suffixes).
            # Strategy: DROP + re-CREATE (not RENAME) to avoid SQLite FK propagation.
            all_tables_to_check = [
                'product_okrs', 'product_key_results', 'delivery_okrs',
                'epics', 'epic_dependencies', 'features',
            ]
            broken_tables = set()
            for tbl in all_tables_to_check:
                c = await db.execute("SELECT sql FROM sqlite_master WHERE name = ?", (tbl,))
                r = await c.fetchone()
                if r and ('_old' in (r[0] or '') or '_rebuild' in (r[0] or '')):
                    broken_tables.add(tbl)

            if broken_tables:
                try:
                    await db.execute("PRAGMA foreign_keys = OFF")

                    # Rebuild in dependency order (base tables first)
                    rebuild_defs = {
                        'product_okrs': ("""CREATE TABLE product_okrs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            strategic_okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
                            digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
                            objective TEXT NOT NULL,
                            status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                            "INSERT INTO product_okrs_new SELECT * FROM product_okrs", []),
                        'product_key_results': ("""CREATE TABLE product_key_results (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
                            key_result TEXT NOT NULL, metric TEXT,
                            current_value REAL DEFAULT 0, target_value REAL NOT NULL,
                            unit TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                            "INSERT INTO product_key_results_new SELECT * FROM product_key_results", []),
                        'delivery_okrs': ("""CREATE TABLE delivery_okrs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
                            team_id INTEGER NOT NULL REFERENCES teams(id),
                            objective TEXT NOT NULL,
                            status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                            "INSERT INTO delivery_okrs_new SELECT * FROM delivery_okrs", []),
                        'epics': ("""CREATE TABLE epics (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            initiative_id INTEGER NOT NULL REFERENCES initiatives(id),
                            team_id INTEGER REFERENCES teams(id),
                            product_okr_id INTEGER REFERENCES product_okrs(id),
                            name TEXT NOT NULL, description TEXT,
                            status TEXT DEFAULT 'backlog' CHECK (status IN ('backlog', 'in_progress', 'done', 'blocked')),
                            start_date TEXT, target_date TEXT,
                            value_score INTEGER DEFAULT 3, size_score INTEGER DEFAULT 3,
                            effort_score INTEGER DEFAULT 3, priority_score REAL DEFAULT 0,
                            risk_level TEXT DEFAULT 'medium', risks TEXT,
                            dependencies_text TEXT, roadmap_phase TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                            """INSERT INTO epics_new (id, initiative_id, team_id, product_okr_id,
                            name, description, status, start_date, target_date,
                            value_score, size_score, effort_score, priority_score,
                            risk_level, risks, dependencies_text, roadmap_phase, created_at)
                            SELECT id, initiative_id, team_id, product_okr_id,
                            name, description, status, start_date, target_date,
                            COALESCE(value_score, 3), COALESCE(size_score, 3), COALESCE(effort_score, 3),
                            COALESCE(priority_score, 0), COALESCE(risk_level, 'medium'),
                            risks, dependencies_text, roadmap_phase, created_at FROM epics""",
                            ["CREATE INDEX IF NOT EXISTS idx_epics_status ON epics(status)"]),
                        'epic_dependencies': ("""CREATE TABLE epic_dependencies (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            epic_id INTEGER NOT NULL REFERENCES epics(id),
                            depends_on_epic_id INTEGER NOT NULL REFERENCES epics(id),
                            dependency_type TEXT DEFAULT 'blocks' CHECK (dependency_type IN ('blocks', 'relates_to')),
                            notes TEXT, CHECK (epic_id != depends_on_epic_id))""",
                            "INSERT INTO epic_dependencies_new SELECT * FROM epic_dependencies", []),
                        'features': ("""CREATE TABLE features (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            epic_id INTEGER NOT NULL REFERENCES epics(id),
                            delivery_okr_id INTEGER REFERENCES delivery_okrs(id),
                            name TEXT NOT NULL, description TEXT,
                            priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
                            status TEXT DEFAULT 'backlog' CHECK (status IN ('backlog', 'ready', 'in_progress', 'done')),
                            estimated_effort INTEGER, start_date TEXT, target_date TEXT,
                            completion_date TEXT,
                            value_score INTEGER DEFAULT 3, size_score INTEGER DEFAULT 3,
                            effort_score INTEGER DEFAULT 3, priority_score REAL DEFAULT 0,
                            risk_level TEXT DEFAULT 'medium', risks TEXT,
                            dependencies_text TEXT, roadmap_phase TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                            """INSERT INTO features_new (id, epic_id, delivery_okr_id, name, description,
                            priority, status, estimated_effort, start_date, target_date, completion_date,
                            value_score, size_score, effort_score, priority_score,
                            risk_level, risks, dependencies_text, roadmap_phase, created_at)
                            SELECT id, epic_id, delivery_okr_id, name, description,
                            priority, status, estimated_effort, start_date, target_date, completion_date,
                            COALESCE(value_score, 3), COALESCE(size_score, 3), COALESCE(effort_score, 3),
                            COALESCE(priority_score, 0), COALESCE(risk_level, 'medium'),
                            risks, dependencies_text, roadmap_phase, created_at FROM features""",
                            ["CREATE INDEX IF NOT EXISTS idx_features_status ON features(status)",
                             "CREATE INDEX IF NOT EXISTS idx_features_epic ON features(epic_id)"]),
                    }

                    # Also rebuild dependent tables even if not directly broken
                    if 'product_okrs' in broken_tables:
                        broken_tables.update(['product_key_results', 'delivery_okrs', 'epics'])
                    if 'epics' in broken_tables:
                        broken_tables.update(['epic_dependencies', 'features'])

                    for tbl in all_tables_to_check:
                        if tbl not in broken_tables:
                            continue
                        create_sql, insert_sql, indexes = rebuild_defs[tbl]
                        # Use _new suffix: create new, copy, drop old, rename new
                        new_create = create_sql.replace(f"CREATE TABLE {tbl}", f"CREATE TABLE {tbl}_new")
                        await db.execute(new_create)
                        await db.execute(insert_sql)
                        await db.execute(f"DROP TABLE {tbl}")
                        await db.execute(f"ALTER TABLE {tbl}_new RENAME TO {tbl}")
                        for idx_sql in indexes:
                            await db.execute(idx_sql)

                    await db.execute("PRAGMA foreign_keys = ON")
                except Exception as e:
                    await db.execute("PRAGMA foreign_keys = ON")

        await db.commit()


frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
