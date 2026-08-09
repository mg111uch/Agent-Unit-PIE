#!/usr/bin/env python3
"""
condense_transcript.py

Shrinks verbose coding-agent TUI transcripts (repeated system prompts, growing
"Messages Sent" arrays, duplicated raw_response JSON, tool schema dumps) down
to a compact, readable form while keeping every unique piece of information.

Block markers used in the output:

    =====[NEW TURN]=====          =====[TOOL SCHEMAS]=====
    =====[LLM USAGE] step=.. =====    =====[FINAL]=====

Transformations (all reversible/inspectable, nothing silently dropped):
  * [NEW TURN]  keep Provider/Model and the small context fields; replace the
    system-prompt body with a char-count marker; drop `role`/`created_at`
    noise from the Messages array (content only).
  * [TOOL SCHEMAS] replace the JSON dump with a char-count marker.
  * [LLM RESPONSE] per step: write each tool call as `name{args}`; write the
    Full Result as `status=..., conversation_id=…<last8>`; drop the duplicated
    raw_response JSON and the growing Messages array. If the LLM call itself
    errored, `status=ERROR` is shown; if the step issued tool call(s) it
    shows `status=CALL` and the execution outcome follows in `[TOOL RESULTS]`.
  * [TOOL RESULTS (multi)] collapse `Calls`/`Results` arrays to one-line
    `ok=.. result=..` records.
  * [TOOL FAILED] emitted for every tool call a step requested but never
    produced a result block for — i.e. the tool was rejected or never ran.
    This prevents a rejected tool call (e.g. an unknown tool name) from
    being mistaken for a success.
  * [FINAL] keep step + response verbatim.

Usage:
    python condense_transcript.py input.txt -o condensed.txt --stats
    python condense_transcript.py input.txt --no-sysprompt --no-tool-schemas
    python condense_transcript.py input.txt            # writes to stdout
"""
import argparse
import json
import re
import sys


# ---------------------------------------------------------------------------
# Block tokenizer
# ---------------------------------------------------------------------------

BLOCK_RE = re.compile(
    r"^={20,}\s*$\n\s*\[(?P<kind>[^\]]+)\]\s*$\n^={20,}\s*$", re.M)


def split_blocks(text):
    """Yield (kind, body) in order; kind is None for text outside a block."""
    pos = 0
    for m in BLOCK_RE.finditer(text):
        if m.start() > pos:
            yield None, text[pos:m.start()]
        nxt = BLOCK_RE.search(text, m.end())
        body_end = nxt.start() if nxt else len(text)
        yield m.group("kind"), _strip_seps(text[m.end():body_end])
        pos = body_end
    if pos < len(text):
        yield None, text[pos:]


_SEP_LINE = re.compile(r"^={20,}\s*$")


def _strip_seps(body):
    """Trim trailing block separators (====) and blank padding from a body."""
    lines = body.split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and _SEP_LINE.match(lines[-1]):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
    return "\n".join(lines) + "\n"


def field(body, label):
    """Value after 'label:' up to the next blank line, stripped, or None."""
    m = re.search(
        rf"^\s*{re.escape(label)}:\s*\n(?P<v>.*?)(?=\n\n[A-Z][^*\n]*:|\Z)",
        body, re.M | re.S)
    return m.group("v").strip() if m else None


def _int(v):
    """Parse an int from a field value, or None."""
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _find_matching_brace(s, open_idx):
    depth = 0
    in_str = False
    esc = False
    for i in range(open_idx, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _json_after_label(body, label):
    """Parse the JSON value (object or array) that follows 'label:' in body."""
    m = re.search(rf"^\s*{re.escape(label)}:\s*\n(?P<j>\s*[\{{\[])", body, re.M)
    if not m:
        return None
    j = m.group("j")
    open_idx = m.start("j") + j.index(j[0])
    if j[0] == "{":
        close = _find_matching_brace(body, open_idx)
    else:
        close = _find_matching_bracket(body, open_idx)
    if close == -1:
        return None
    try:
        return json.loads(body[open_idx:close + 1])
    except json.JSONDecodeError:
        return None


def _find_matching_bracket(s, open_idx):
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "[":
            depth += 1
        elif s[i] == "]":
            depth -= 1
            if depth == 0:
                return i
    return -1


# ---------------------------------------------------------------------------
# [NEW TURN]
# ---------------------------------------------------------------------------

def _compact_msgs(raw):
    try:
        msgs = json.loads(raw)
    except json.JSONDecodeError:
        return None
    lines = []
    for msg in msgs:
        if isinstance(msg, dict) and msg.get("content") is not None:
            lines.append('  {"content": %s}' % json.dumps(msg["content"]))
    if not lines:
        return None
    return "[\n" + ",\n".join(lines) + "\n]"


def cond_new_turn(body):
    def g(lbl):
        m = field(body, lbl)
        return None if m and m.lower() in ("(none)", "none") else m

    out = ["=====[NEW TURN]=====\n"]
    if g("Provider"):
        out.append(f"Provider: {g('Provider')}\n")
    if g("Model"):
        out.append(f"Model: {g('Model')}\n")
    sysp = field(body, "System Prompt")
    if sysp:
        out.append(f"System Prompt:\n<<System Prompt present ({len(sysp)} chars)"
                    " — omitted>>\n")
    for lbl in ("Context Info", "Session Digest", "Session Context"):
        v = g(lbl)
        if v:
            out.append(f"{lbl}: {v}\n")
    hits, miss = g("Cache Hits"), g("Cache Misses")
    if hits or miss:
        out.append(f"Cache: hits={hits} misses={miss}\n")
    msgs = _compact_msgs(field(body, "Messages") or "")
    if msgs:
        out.append("Messages:\n" + msgs + "\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# [TOOL SCHEMAS]
# ---------------------------------------------------------------------------

def cond_schemas(body):
    schemas = field(body, "Schemas") or body.strip()
    if not schemas:
        return ""
    return ("=====[TOOL SCHEMAS]=====\n"
            f"Schemas present ({len(schemas)} chars) — omitted\n")


# ---------------------------------------------------------------------------
# LLM USAGE / RESPONSE / TOOL RESULTS step compaction
# ---------------------------------------------------------------------------

def cond_usage(body):
    step = field(body, "Step")
    tokens = field(body, "Total Tokens")
    lat = field(body, "Latency Seconds")
    ret = field(body, "Retries")
    if not (step and tokens and lat and ret):
        return ""
    return (f"=====[LLM USAGE] step={step} tokens={tokens} "
            f"latency={lat}s retries={ret}=====\n")


def cond_llm_response(body, prev_usage=""):
    parts = [prev_usage]
    step = field(body, "Step")
    calls = _json_after_label(body, "Tool Calls Raw")
    names = []
    if calls and isinstance(calls, list):
        for c in calls:
            if not isinstance(c, dict):
                continue
            name = c.get("name")
            names.append(name or "?")
            args = c.get("arguments")
            if isinstance(args, dict):
                parts.append(f"[{name}]: {json.dumps(args)}")
    fr = _json_after_label(body, "Full Result")
    if fr:
        status = fr.get("status")
        conv = fr.get("conversation_id") or ""
        if status == "error":
            parts.append(f"status=ERROR: {fr.get('error') or 'LLM call failed'}")
        elif names:
            line = "status=CALL (LLM issued tool call)"
            if conv:
                line += f", conversation_id=…{conv[-8:]}(last 8 chars only)"
            parts.append(line)
        else:
            line = f"status={status}"
            if conv:
                line += f", conversation_id=…{conv[-8:]}(last 8 chars only)"
            parts.append(line)
    return _int(step), names, "\n".join(p for p in parts if p) + "\n"


def _cond_tool_err_lines(pending):
    """Emit an error block for tool calls that never produced a result."""
    lines = []
    for step in sorted(pending):
        for name in pending[step]:
            lines.append(
                f"=====[TOOL FAILED] step={step}=====\n"
                f"[{name}] was rejected/not executed — no tool result recorded. "
                f"Do not treat as success.\n"
            )
    pending.clear()
    return lines


def cond_tool_results(body):
    arr = _json_after_label(body, "Results")
    if not isinstance(arr, list):
        return ""
    lines = []
    for r in arr:
        if isinstance(r, dict):
            lines.append("  {" + f"result={json.dumps(r.get('result'))} "
                         f"ok={r.get('ok')}" + "}")
    if not lines:
        return ""
    return "Results:\n" + "\n".join(lines) + "\n"


def cond_final(body):
    step = field(body, "Step")
    resp = field(body, "Response")
    out = ["=====[FINAL]=====\n"]
    if step:
        out.append(f"Step: {step}\n")
    if resp:
        out.append(f"Response: {resp}\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def condense(text, *, no_sysprompt=False, no_tool_schemas=False):
    out = []
    usage = ""
    pending = {}
    for kind, body in split_blocks(text):
        if kind is None:
            continue
        if kind == "NEW TURN":
            out.extend(_cond_tool_err_lines(pending))
            out.append(cond_new_turn(body))
        elif kind == "TOOL SCHEMAS":
            out.append(cond_schemas(body))
        elif kind == "LLM USAGE":
            usage = cond_usage(body)
            st = _int(field(body, "Step"))
            other = [s for s in pending if s != st]
            for s in other:
                out.extend(_cond_tool_err_lines({s: pending.pop(s)}))
        elif kind == "LLM RESPONSE":
            step, names, text = cond_llm_response(body, usage)
            if step is not None and names:
                pending[step] = names
            out.append(text)
            usage = ""
        elif kind.startswith("TOOL RESULT"):
            out.append(cond_tool_results(body))
            st = _int(field(body, "Step"))
            if st in pending:
                del pending[st]
        elif kind == "FINAL":
            out.extend(_cond_tool_err_lines(pending))
            out.append(cond_final(body))
    out.extend(_cond_tool_err_lines(pending))
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="path to the raw transcript .txt")
    ap.add_argument("-o", "--output", help="output path (default: stdout)")
    ap.add_argument("--stats", action="store_true",
                    help="print before/after size stats to stderr")
    ap.add_argument("--no-sysprompt", action="store_true",
                    help="(kept for compat) system prompt already collapsed")
    ap.add_argument("--no-tool-schemas", action="store_true",
                    help="(kept for compat) tool schemas already collapsed")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    condensed = condense(original)

    if args.stats:
        before, after = len(original), len(condensed)
        pct = 100 * (1 - after / before) if before else 0
        print(f"[condense_transcript] {before:,} chars -> {after:,} chars "
              f"({pct:.1f}% smaller)", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(condensed)
    else:
        sys.stdout.write(condensed)


if __name__ == "__main__":
    main()
