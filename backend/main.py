from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from routers import (
    step1_performance,
    step1_ai_dashboard,
    step2_value_streams,
    step3_swot_tows,
    step4_strategy_okrs,
    step5_initiatives,
    step6_epics_teams,
    step7_features,
    review_gates,
    auth_router,
)

app = FastAPI(title="Business Transformation Architect", version="1.0.0")

# CORS: configurable origins (default restrictive for production)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(step1_performance.router, prefix="/api/step1", tags=["Step 1: Performance"])
app.include_router(step1_ai_dashboard.router, prefix="/api/step1", tags=["Step 1: AI Dashboard"])
app.include_router(step2_value_streams.router, prefix="/api/step2", tags=["Step 2: Value Streams"])
app.include_router(step3_swot_tows.router, prefix="/api/step3", tags=["Step 3: SWOT/TOWS"])
app.include_router(step4_strategy_okrs.router, prefix="/api/step4", tags=["Step 4: Strategy & OKRs"])
app.include_router(step5_initiatives.router, prefix="/api/step5", tags=["Step 5: Initiatives & RICE"])
app.include_router(step6_epics_teams.router, prefix="/api/step6", tags=["Step 6: Epics & Teams"])
app.include_router(step7_features.router, prefix="/api/step7", tags=["Step 7: Features & Roadmap"])
app.include_router(review_gates.router, prefix="/api/gates", tags=["Review Gates"])


@app.on_event("startup")
async def startup():
    from database import USE_POSTGRES, init_pg_pool
    await init_pg_pool()
    await run_migrations()


@app.on_event("shutdown")
async def shutdown():
    from database import close_pg_pool
    await close_pg_pool()


async def run_migrations():
    """Initialize database from schema if fresh, apply column migrations for existing DBs."""
    from database import USE_POSTGRES, get_db_connection

    db = await get_db_connection()
    try:
        if USE_POSTGRES:
            await _migrate_postgres(db)
        else:
            await _migrate_sqlite(db)
    finally:
        await db.close()


async def _migrate_postgres(db):
    """Run PostgreSQL schema (all CREATE IF NOT EXISTS)."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema_postgres.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    await db.executescript(schema_sql)


async def _migrate_sqlite(db):
    """Initialize SQLite database from schema.sql if fresh, then apply column migrations."""
    import aiosqlite
    from database import DB_PATH

    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")

    # We need raw aiosqlite connection for SQLite-specific migration logic
    async with aiosqlite.connect(DB_PATH) as raw_db:
        cursor = await raw_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organization'")
        exists = await cursor.fetchone()

        if not exists:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            await raw_db.executescript(schema_sql)
        else:
            # Add users table for existing DBs
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            # Existing DB: add new columns if missing
            for col in ["competitor_1_name TEXT", "competitor_2_name TEXT"]:
                try:
                    await raw_db.execute(f"ALTER TABLE organization ADD COLUMN {col}")
                except Exception:
                    pass

            for col in [
                "ticker TEXT", "revenue REAL", "profit_margin REAL",
                "operating_margin REAL", "return_on_equity REAL",
                "return_on_assets REAL", "pe_ratio REAL", "eps REAL",
                "market_cap_value REAL",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE competitors ADD COLUMN {col}")
                except Exception:
                    pass

            # New Step 2 tables for value stream mapping
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS value_stream_steps (
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
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS value_stream_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value_stream_id INTEGER NOT NULL UNIQUE REFERENCES value_streams(id),
                total_lead_time_hours REAL DEFAULT 0,
                total_process_time_hours REAL DEFAULT 0,
                total_wait_time_hours REAL DEFAULT 0,
                flow_efficiency REAL DEFAULT 0,
                bottleneck_step TEXT,
                bottleneck_reason TEXT,
                data_source TEXT DEFAULT 'manual' CHECK (data_source IN ('ai_generated', 'template', 'uploaded', 'manual', 'visual_upload', 'url_extraction')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS value_stream_benchmarks (
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
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS strategy_inputs (
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
                await raw_db.execute("ALTER TABLE strategies ADD COLUMN approved INTEGER DEFAULT 0")
            except Exception:
                pass

            # Rebuild strategies table to expand layer CHECK to include 'data'
            needs_rebuild = False
            try:
                await raw_db.execute("INSERT INTO strategies (layer, name, description) VALUES ('data', '__migration_test__', NULL)")
                await raw_db.execute("DELETE FROM strategies WHERE name = '__migration_test__'")
            except Exception:
                needs_rebuild = True

            # Check if any tables have broken FK references to strategies_old
            fk_broken = False
            for tbl_name in ['strategic_okrs', 'initiatives']:
                cursor = await raw_db.execute("SELECT sql FROM sqlite_master WHERE name = ?", (tbl_name,))
                row = await cursor.fetchone()
                if row and 'strategies_old' in (row[0] or ''):
                    fk_broken = True
                    break

            if needs_rebuild or fk_broken:
                try:
                    await raw_db.execute("PRAGMA foreign_keys = OFF")

                    if needs_rebuild:
                        await raw_db.execute("DROP TABLE IF EXISTS strategies_old")
                        await raw_db.execute("ALTER TABLE strategies RENAME TO strategies_old")
                        await raw_db.execute("""CREATE TABLE strategies (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            layer TEXT NOT NULL CHECK (layer IN ('business', 'digital', 'data', 'gen_ai')),
                            name TEXT NOT NULL,
                            description TEXT,
                            tows_action_id INTEGER REFERENCES tows_actions(id),
                            approved INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""")
                        await raw_db.execute("""INSERT INTO strategies (id, layer, name, description, tows_action_id, approved, created_at)
                            SELECT id, layer, name, description, tows_action_id,
                                   COALESCE(approved, 0), created_at FROM strategies_old""")
                        await raw_db.execute("DROP TABLE strategies_old")

                    if fk_broken:
                        await raw_db.execute("ALTER TABLE strategic_okrs RENAME TO strategic_okrs_old")
                        await raw_db.execute("""CREATE TABLE strategic_okrs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            strategy_id INTEGER NOT NULL REFERENCES strategies(id),
                            objective TEXT NOT NULL,
                            time_horizon TEXT,
                            status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""")
                        await raw_db.execute("""INSERT INTO strategic_okrs (id, strategy_id, objective, time_horizon, status, created_at)
                            SELECT id, strategy_id, objective, time_horizon, status, created_at FROM strategic_okrs_old""")
                        await raw_db.execute("DROP TABLE strategic_okrs_old")

                        cursor2 = await raw_db.execute("SELECT sql FROM sqlite_master WHERE name = 'strategic_key_results'")
                        kr_row = await cursor2.fetchone()
                        if kr_row and 'okrs_old' in (kr_row[0] or ''):
                            await raw_db.execute("ALTER TABLE strategic_key_results RENAME TO strategic_key_results_old")
                            await raw_db.execute("""CREATE TABLE strategic_key_results (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
                                key_result TEXT NOT NULL,
                                metric TEXT,
                                current_value REAL DEFAULT 0,
                                target_value REAL NOT NULL,
                                unit TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )""")
                            await raw_db.execute("""INSERT INTO strategic_key_results (id, okr_id, key_result, metric, current_value, target_value, unit, created_at)
                                SELECT id, okr_id, key_result, metric, current_value, target_value, unit, created_at FROM strategic_key_results_old""")
                            await raw_db.execute("DROP TABLE strategic_key_results_old")

                        cursor3 = await raw_db.execute("SELECT sql FROM sqlite_master WHERE name = 'initiatives'")
                        init_row = await cursor3.fetchone()
                        if init_row and 'strategies_old' in (init_row[0] or ''):
                            await raw_db.execute("ALTER TABLE initiatives RENAME TO initiatives_old")
                            await raw_db.execute("""CREATE TABLE initiatives (
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
                            await raw_db.execute("""INSERT INTO initiatives (id, digital_product_id, strategy_id, name, description,
                                reach, impact, confidence, effort, rice_override, rice_override_reason,
                                value_score, size_score, impacted_segments, dependencies, risks, roadmap_phase,
                                status, created_at)
                                SELECT id, digital_product_id, strategy_id, name, description,
                                reach, impact, confidence, effort, rice_override, rice_override_reason,
                                COALESCE(value_score, 3), COALESCE(size_score, 3), impacted_segments, dependencies, risks, roadmap_phase,
                                status, created_at FROM initiatives_old""")
                            await raw_db.execute("DROP TABLE initiatives_old")

                    await raw_db.execute("PRAGMA foreign_keys = ON")
                except Exception:
                    await raw_db.execute("PRAGMA foreign_keys = ON")

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
                    await raw_db.execute(f"ALTER TABLE initiatives ADD COLUMN {col}")
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
                    await raw_db.execute(f"ALTER TABLE epics ADD COLUMN {col}")
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
                    await raw_db.execute(f"ALTER TABLE features ADD COLUMN {col}")
                except Exception:
                    pass

            # Fix broken FKs
            all_tables_to_check = [
                'product_okrs', 'product_key_results', 'delivery_okrs',
                'epics', 'epic_dependencies', 'features',
            ]
            broken_tables = set()
            for tbl in all_tables_to_check:
                c = await raw_db.execute("SELECT sql FROM sqlite_master WHERE name = ?", (tbl,))
                r = await c.fetchone()
                if r and ('_old' in (r[0] or '') or '_rebuild' in (r[0] or '')):
                    broken_tables.add(tbl)

            if broken_tables:
                try:
                    await raw_db.execute("PRAGMA foreign_keys = OFF")

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

                    if 'product_okrs' in broken_tables:
                        broken_tables.update(['product_key_results', 'delivery_okrs', 'epics'])
                    if 'epics' in broken_tables:
                        broken_tables.update(['epic_dependencies', 'features'])

                    for tbl in all_tables_to_check:
                        if tbl not in broken_tables:
                            continue
                        create_sql, insert_sql, indexes = rebuild_defs[tbl]
                        new_create = create_sql.replace(f"CREATE TABLE {tbl}", f"CREATE TABLE {tbl}_new")
                        await raw_db.execute(new_create)
                        await raw_db.execute(insert_sql)
                        await raw_db.execute(f"DROP TABLE {tbl}")
                        await raw_db.execute(f"ALTER TABLE {tbl}_new RENAME TO {tbl}")
                        for idx_sql in indexes:
                            await raw_db.execute(idx_sql)

                    await raw_db.execute("PRAGMA foreign_keys = ON")
                except Exception:
                    await raw_db.execute("PRAGMA foreign_keys = ON")

            # --- Phase 4 migration: new columns for AI-powered SWOT, TOWS, and Strategy ---
            for col in [
                "severity TEXT DEFAULT 'medium'",
                "confidence TEXT DEFAULT 'medium'",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE swot_entries ADD COLUMN {col}")
                except Exception:
                    pass

            for col in [
                "impact_score INTEGER DEFAULT 5",
                "rationale TEXT",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE tows_actions ADD COLUMN {col}")
                except Exception:
                    pass

            for col in [
                "risk_level TEXT DEFAULT 'medium'",
                "risks TEXT",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE strategies ADD COLUMN {col}")
                except Exception:
                    pass

            for col in [
                "target_optimistic REAL",
                "target_pessimistic REAL",
                "rationale TEXT",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE strategic_key_results ADD COLUMN {col}")
                except Exception:
                    pass

            # --- Phase 5 migration: AI-powered initiatives, epics, features ---
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS feature_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER NOT NULL REFERENCES features(id),
                depends_on_feature_id INTEGER NOT NULL REFERENCES features(id),
                dependency_type TEXT DEFAULT 'blocks' CHECK (dependency_type IN ('blocks', 'relates_to')),
                notes TEXT,
                CHECK (feature_id != depends_on_feature_id)
            )""")

            for col in [
                "ai_generated INTEGER DEFAULT 0",
                "ai_rationale TEXT",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE initiatives ADD COLUMN {col}")
                except Exception:
                    pass

            for col in [
                "ai_generated INTEGER DEFAULT 0",
                "estimated_effort_days REAL",
                "ai_rationale TEXT",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE epics ADD COLUMN {col}")
                except Exception:
                    pass

            for col in [
                "ai_generated INTEGER DEFAULT 0",
                "ai_rationale TEXT",
                "acceptance_criteria TEXT",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE features ADD COLUMN {col}")
                except Exception:
                    pass

            try:
                await raw_db.execute("ALTER TABLE product_okrs ADD COLUMN ai_generated INTEGER DEFAULT 0")
            except Exception:
                pass

            try:
                await raw_db.execute("ALTER TABLE delivery_okrs ADD COLUMN ai_generated INTEGER DEFAULT 0")
            except Exception:
                pass

            # --- Phase 3 migration: expand data_source CHECK constraint on value_stream_metrics ---
            try:
                await raw_db.execute(
                    "INSERT INTO value_stream_metrics (value_stream_id, data_source) VALUES (-1, 'visual_upload')"
                )
                await raw_db.execute("DELETE FROM value_stream_metrics WHERE value_stream_id = -1")
            except Exception:
                # CHECK constraint rejects new values — recreate the table
                try:
                    await raw_db.execute("PRAGMA foreign_keys = OFF")
                    await raw_db.execute("""CREATE TABLE IF NOT EXISTS value_stream_metrics_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
                        total_lead_time_hours REAL DEFAULT 0,
                        total_process_time_hours REAL DEFAULT 0,
                        total_wait_time_hours REAL DEFAULT 0,
                        flow_efficiency REAL DEFAULT 0,
                        bottleneck_step TEXT,
                        bottleneck_reason TEXT,
                        data_source TEXT DEFAULT 'manual' CHECK (data_source IN ('ai_generated', 'template', 'uploaded', 'manual', 'visual_upload', 'url_extraction')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )""")
                    await raw_db.execute("""INSERT INTO value_stream_metrics_new
                        (id, value_stream_id, total_lead_time_hours, total_process_time_hours,
                         total_wait_time_hours, flow_efficiency, bottleneck_step, bottleneck_reason,
                         data_source, created_at)
                        SELECT id, value_stream_id, total_lead_time_hours, total_process_time_hours,
                         total_wait_time_hours, flow_efficiency, bottleneck_step, bottleneck_reason,
                         data_source, created_at FROM value_stream_metrics""")
                    await raw_db.execute("DROP TABLE value_stream_metrics")
                    await raw_db.execute("ALTER TABLE value_stream_metrics_new RENAME TO value_stream_metrics")
                    await raw_db.execute("PRAGMA foreign_keys = ON")
                except Exception:
                    await raw_db.execute("PRAGMA foreign_keys = ON")

            # --- Step 1 Data Ingestion Hub: saved URLs table ---
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS step1_data_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                label TEXT,
                url_type TEXT DEFAULT 'external',
                last_fetched_at TIMESTAMP,
                last_result_json TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            # --- Phase 6 migration: AI Dashboard tables ---
            await raw_db.execute("""CREATE TABLE IF NOT EXISTS ai_analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                result_json TEXT NOT NULL,
                ai_model TEXT DEFAULT 'gpt-4o-mini',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )""")

            await raw_db.execute("""CREATE TABLE IF NOT EXISTS ai_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT NOT NULL,
                scenario_type TEXT NOT NULL CHECK (scenario_type IN ('revenue_change', 'market_entry', 'cost_change', 'custom')),
                parameters_json TEXT NOT NULL,
                result_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            await raw_db.execute("""CREATE TABLE IF NOT EXISTS nlq_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer_json TEXT NOT NULL,
                data_tables_queried TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            for col in [
                "ai_executive_summary TEXT",
                "ai_health_score REAL",
                "ai_summary_updated_at TIMESTAMP",
            ]:
                try:
                    await raw_db.execute(f"ALTER TABLE organization ADD COLUMN {col}")
                except Exception:
                    pass

        await raw_db.commit()


frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
