import json, time
from kernel.persistence.db import kernel_db

def tool_stats(params: dict) -> str:
    rows = kernel_db.get_tool_stats()
    if not rows:
        return "No tool calls recorded yet."
    lines = ["Tool call statistics (most called first):"]
    lines.append(f"{'Tool':<30} {'Calls':<8} {'Avg ms':<8} {'Err%':<7} {'Avg tok':<8} {'Last called'}")
    lines.append("-" * 80)
    for r in rows:
        tool = r["tool_name"]
        calls = r["call_count"]
        avg = f"{r['avg_duration_ms']:.1f}"
        err_pct = f"{r['error_rate'] * 100:.0f}%"
        avg_tok = r["avg_tokens"]
        last = time.strftime("%H:%M:%S", time.localtime(r["last_called_at"]))
        flag = " ⚠︎" if r["error_rate"] > 0.3 and calls > 1 else ""
        lines.append(f"{tool:<30} {calls:<8} {avg:<8} {err_pct:<7} {avg_tok:<8} {last}{flag}")
    if any(r["error_rate"] > 0.3 and r["call_count"] > 1 for r in rows):
        lines.append("")
        lines.append("⚠︎  High error rate (>30%) — consider reviewing or replacing these tools.")
    return "\n".join(lines)


def file_stats(params: dict) -> str:
    limit = 20
    if isinstance(params, dict):
        limit = int(params.get("limit", 20))
    rows = kernel_db.get_file_stats(limit)
    if not rows:
        return "No file accesses recorded yet."
    lines = [f"Top {len(rows)} most accessed files:"]
    lines.append(f"{'File':<60} {'Op':<10} {'Count':<8} {'Last accessed'}")
    lines.append("-" * 90)
    # Group by file to flag churn
    by_file: dict[str, int] = {}
    for r in rows:
        fpath = r["file_path"]
        op = r["operation"]
        cnt = r["access_count"]
        last = time.strftime("%H:%M:%S", time.localtime(r["last_accessed_at"]))
        by_file[fpath] = by_file.get(fpath, 0) + cnt
        lines.append(f"{fpath:<60} {op:<10} {cnt:<8} {last}")
    churners = {f: c for f, c in by_file.items() if c > 5}
    if churners:
        lines.append("")
        lines.append("⚠︎  High-churn files (>5 total ops) — refactoring candidates:")
        for f, c in sorted(churners.items(), key=lambda x: -x[1]):
            lines.append(f"       {f} ({c} ops)")
    return "\n".join(lines)


def user_reading_budget(params: dict) -> str:
    if isinstance(params, dict):
        record = params.get("record_lines")
        if record is not None:
            kernel_db.record_llm_output_lines(int(record))
    budget = kernel_db.get_daily_budget()
    pct = (budget["lines_used"] / budget["budget"] * 100) if budget["budget"] > 0 else 0
    remaining = budget["remaining"]
    alert = ""
    if remaining < budget["budget"] * 0.2:
        alert = "\n⚠︎  Less than 20% remaining. The agent will start truncating responses."
    return (
        f"User reading budget for {budget['date']}:\n"
        f"  Used: {budget['lines_used']} of {budget['budget']} lines\n"
        f"  Remaining: {remaining} lines ({pct:.0f}% used){alert}"
    )
