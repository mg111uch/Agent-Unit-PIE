<!-- read_only -->
TOOL USAGE:
- read_file "(cached: N lines, unchanged)" -> content in context. no re-read. offset/limit only for section.
- grep_search over reading many files for find/usages.
- tool 2x same fail -> change approach, no repeat.
- read/list fail -> error lists nearby files; use exact; missing -> glob_search("**/<name>") before "absent".
- verify dir paths w/ list_files before read. no guessed paths.
- read_file offset/limit portions; offset 1-based (omit=1); limit=max lines (omit=rest).
- existence check -> stop at list_files/glob. no read_file/content unless asked.
<!-- /read_only -->
- open-ended research -> subagent_task: sub explores, read only its edit targets.
- >1 file / ~3+ calls: todo(create) short plan; update as you go; read=view.
- edit: read first. never guess content/whitespace.
- edit_file fail (old_string missing/dup): re-read, copy exact + context. no repeat identical call.
- edit diff = verification. re-read only 3+ edits/unexpected diff/tests.
- old_string exact (whitespace), appears once.
- glob hints: use listed paths, no guessed prefixes.