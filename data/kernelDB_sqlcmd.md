# Count rows with `topic_id`
sqlite3 data/kernel.db "SELECT COUNT(*) FROM semantic_nodes WHERE topic_id='_smoke_k'"