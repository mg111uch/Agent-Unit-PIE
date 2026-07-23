# Codebase Atlas Status
_Last verified: 2026-07-23_

> Capability claims are hypotheses. Re-validate: `python scripts/validate_capabilities.py`

## Current Capability
- Multi-language parsing with dependency analysis and 3-layer output — `modules/codebase_atlas/main.py:generate_atlas()`
- Graph building from atlas data with directory clustering — `modules/codebase_atlas/main.py:generate_atlas()`
- Interactive graph viewer served via browser — `modules/codebase_atlas/graph/backend/serve.py:create_app()`
- Graph JSON export for browser rendering — `modules/codebase_atlas/graph/backend/serve.py:_load_positions_with_meta()`
- RAG index generation with function/class/file indexing — `modules/codebase_atlas/rag/db.py:insert_function()`
- Position save/load with per-cluster layout persistence — `modules/codebase_atlas/graph/backend/serve.py:_write_positions()`

## Known Gaps
- Dead code detection not yet implemented — med
- Test coverage mapping across functions — low
- Incremental regeneration (hash-based diff) — low

## Recent Changes (newest first, max 10)
- (No recent changes tracked in this format yet)
