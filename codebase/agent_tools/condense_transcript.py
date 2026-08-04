#!/usr/bin/env python3
"""
condense_transcript.py

Shrinks verbose coding-agent TUI transcripts (the kind with repeated system
prompts, growing "Messages Sent" arrays, and duplicated raw_response JSON)
down to something small enough to paste into a chat, while keeping every
unique piece of information.

Strategy (all reversible/inspectable — nothing is silently dropped):
  1. Repeated full-text blocks (System Prompt, Session Digest, etc.) are
     hashed. First occurrence is kept in full and registered in a legend;
     every later exact repeat is replaced with a one-line placeholder like
     <<BLOCK sys_prompt#1 (same as first occurrence, 2143 chars)>>.
  2. "Messages Sent" JSON arrays grow by one exchange per step and repeat
     everything before that verbatim. We diff each array against the
     previous one and only print the new suffix, replacing the unchanged
     prefix with <<N PRIOR MESSAGES UNCHANGED (see step S)>>. Inside that
     suffix, tool_calls/tool_results payloads are replaced with pointers to
     the dedicated [LLM RESPONSE] / [TOOL RESULTS] blocks (shown once each),
     so the same questions/args/results are never reprinted by the history.
  3. "Full Result" JSON blocks nest a `raw_response` object that duplicates
     `response`/`tool_calls` already shown elsewhere in the same block.
     That nested duplicate is stripped to a placeholder, keeping only the
     fields that aren't shown anywhere else (usage, latency, retries).
  4. Consecutive near-identical terminal diagnostic lines (e.g. 7 straight
     "parse ok=False" lines) are collapsed into one line with a count/range.

Optional flags:
    --no-sysprompt      replace the System Prompt + agents.md body with a
                        placeholder (reader knows a system prompt was injected
                        without re-reading its text). Keeps the transcript
                        focused on the actual tool-call conversation.
    --no-tool-schemas   replace the [TOOL SCHEMAS] JSON dump with a placeholder.
                        Tool schemas are static boilerplate that repeats on
                        every server run; a marker is enough to know tools exist.

Usage:
    python condense_transcript.py input.txt -o condensed.txt --stats
    python condense_transcript.py input.txt --no-sysprompt --no-tool-schemas
    python condense_transcript.py input.txt            # writes to stdout
"""
import argparse
import hashlib
import json
import re
import sys
from collections import OrderedDict


# ---------------------------------------------------------------------------
# 1. Generic whole-block deduplication (System Prompt, Session Digest, ...)
# ---------------------------------------------------------------------------

# Each entry: (label, regex capturing the block body as group(1))
DEDUPE_BLOCK_PATTERNS = [
    ("sys_prompt", re.compile(r"(System Prompt:\n)(.*?)(\n\nUser Input:)", re.S)),
    ("session_digest", re.compile(r"(Session Digest:\n)(.*?)(\n\nCache Hits:)", re.S)),
]


class BlockLegend:
    """Tracks first-seen content per label so repeats can be placeholdered."""

    def __init__(self):
        self.seen = {}          # (label, hash) -> occurrence index
        self.counts = OrderedDict()  # label -> next index

    def register(self, label, text):
        h = hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()[:10]
        key = (label, h)
        if key in self.seen:
            idx = self.seen[key]
            is_first = False
        else:
            idx = self.counts.get(label, 0) + 1
            self.counts[label] = idx
            self.seen[key] = idx
            is_first = True
        return idx, is_first


def dedupe_named_blocks(text, legend: BlockLegend):
    for label, pattern in DEDUPE_BLOCK_PATTERNS:
        def _sub(m, label=label):
            prefix, body, suffix = m.group(1), m.group(2), m.group(3)
            idx, is_first = legend.register(label, body)
            if is_first:
                return f"{prefix}{body}{suffix}"
            placeholder = (f"<<BLOCK {label}#{idx} — identical to first "
                            f"occurrence, {len(body)} chars omitted>>")
            return f"{prefix}{placeholder}{suffix}"
        text = pattern.sub(_sub, text)
    return text


# ---------------------------------------------------------------------------
# 1b. Optional flag-based placeholders (System Prompt + agents.md, tool schemas)
# ---------------------------------------------------------------------------

# Canonical dump form: "System Prompt:\n<body>\n\nUser Input:"
SYS_PROMPT_RE = re.compile(r"(System Prompt:\n)(.*?)(\n\nUser Input:)", re.S)
# Hand-trimmed variant seen in some transcripts: a bare marker line on its own.
BARE_SYS_PROMPT_RE = re.compile(r"^<System Prompt \+ agents\.md>\s*$", re.M)
# "[TOOL SCHEMAS]" header + separator + "Schemas:\n[ ... ]\n"
TOOL_SCHEMAS_RE = re.compile(
    r"(\[TOOL SCHEMAS\]\s*={5,}\s*\n\s*Schemas:\n)(\[.*?\n\])(\n)", re.S
)


def strip_sys_prompt(text: str) -> str:
    """Replace the System Prompt + agents.md body with a short placeholder."""
    def _sub(m):
        body = m.group(2)
        marker = (f"<<System Prompt + agents.md present ({len(body)} chars) — "
                  f"omitted by --no-sysprompt>>")
        return f"{m.group(1)}{marker}{m.group(3)}"
    text = SYS_PROMPT_RE.sub(_sub, text)
    text = BARE_SYS_PROMPT_RE.sub(
        "<<System Prompt + agents.md present (trimmed) — omitted by "
        "--no-sysprompt>>", text
    )
    return text


def strip_tool_schemas(text: str) -> str:
    """Replace the [TOOL SCHEMAS] JSON array with a placeholder."""
    def _sub(m):
        schemas = m.group(2)
        marker = (f"<<tool schemas present ({len(schemas)} chars) — "
                  f"omitted by --no-tool-schemas>>")
        return f"{m.group(1)}{marker}{m.group(3)}"
    return TOOL_SCHEMAS_RE.sub(_sub, text)


# ---------------------------------------------------------------------------
# 2. "Messages Sent" JSON array prefix-delta compression
# ---------------------------------------------------------------------------

MESSAGES_SENT_RE = re.compile(r"Messages Sent:\n(\[.*?\n\])\n", re.S)
STEP_RE = re.compile(r"^Step:\n(\d+)\s*$", re.M)


def _msg_key(msg):
    """Stable string form of one message element, for equality comparison."""
    return json.dumps(msg, sort_keys=True)


_TOOL_CALLS_PLACEHOLDER = ("<<tool_calls omitted - see [LLM RESPONSE] "
                           "Tool Calls Raw>>")
_TOOL_RESULTS_PLACEHOLDER = ("<<tool_results omitted - see [TOOL RESULTS] "
                             "Results>>")


def _compact_msg(msg):
    """Copy of a message with tool payloads replaced by pointers to the
    dedicated [LLM RESPONSE] / [TOOL RESULTS] blocks. Every tool_call /
    tool_result is always shown there too, so nothing is lost — this only
    stops the growing Messages Sent history from re-printing them verbatim."""
    if not isinstance(msg, dict):
        return msg
    if msg.get("tool_calls"):
        msg = dict(msg)
        msg["tool_calls"] = _TOOL_CALLS_PLACEHOLDER
    if msg.get("tool_results"):
        msg = dict(msg)
        msg["tool_results"] = _TOOL_RESULTS_PLACEHOLDER
    return msg


def compress_messages_sent(text):
    prev_msgs = []
    prev_step = "start"
    out_parts = []
    pos = 0
    for m in MESSAGES_SENT_RE.finditer(text):
        out_parts.append(text[pos:m.start()])
        raw = m.group(1)
        try:
            msgs = json.loads(raw)
        except json.JSONDecodeError:
            # Not parseable (shouldn't normally happen) — leave untouched.
            out_parts.append(m.group(0))
            pos = m.end()
            continue

        # length of common prefix vs. previous array
        common = 0
        for a, b in zip(prev_msgs, msgs):
            if _msg_key(a) != _msg_key(b):
                break
            common += 1

        new_tail = msgs[common:]
        block = "Messages Sent:\n["
        if common:
            block += (f"\n  <<{common} PRIOR MESSAGES UNCHANGED "
                       f"(same as step {prev_step})>>,")
        for i, msg in enumerate(new_tail):
            body = json.dumps(_compact_msg(msg), indent=2)
            body = "\n".join("  " + line for line in body.splitlines())
            block += "\n" + body
            if i != len(new_tail) - 1:
                block += ","
        block += "\n]\n"
        out_parts.append(block)

        # figure out this record's own step label for the *next* iteration
        step_match = STEP_RE.search(text[max(0, m.start() - 200):m.start()])
        prev_step = step_match.group(1) if step_match else prev_step
        prev_msgs = msgs
        pos = m.end()

    out_parts.append(text[pos:])
    return "".join(out_parts)


# ---------------------------------------------------------------------------
# 3. Strip the duplicated `raw_response` sub-object inside "Full Result"
# ---------------------------------------------------------------------------

def _find_matching_brace(s, open_idx):
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def strip_raw_response_dupe(text):
    marker = '"raw_response": {'
    out = []
    pos = 0
    while True:
        idx = text.find(marker, pos)
        if idx == -1:
            out.append(text[pos:])
            break
        open_brace = idx + len(marker) - 1
        close_brace = _find_matching_brace(text, open_brace)
        if close_brace == -1:
            out.append(text[pos:])
            break
        out.append(text[pos:idx])
        out.append('"raw_response": "<<omitted, duplicates response/'
                    'tool_calls/usage already shown above>>"')
        pos = close_brace + 1
    return "".join(out)


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
# 3b. Strip same-record duplicates of "Tool Calls Raw:" that reappear as
#     Full Result.tool_calls (same block) and as "Calls:" in the very next
#     [TOOL RESULTS (multi)] record. Both are byte-identical restatements
#     of what was already printed once under "Tool Calls Raw:".
# ---------------------------------------------------------------------------

TCR_HEADER = "Tool Calls Raw:\n"
FR_HEADER_TAIL = "\n\nFull Result:\n"
CALLS_HEADER = "Calls:\n"


def strip_full_result_tool_calls_dupe(text):
    """Within one [LLM RESPONSE] record, Full Result.tool_calls repeats
    "Tool Calls Raw:" verbatim as nested JSON. Collapse it."""
    out = []
    pos = 0
    while True:
        idx = text.find(TCR_HEADER, pos)
        if idx == -1:
            out.append(text[pos:])
            break
        body_start = idx + len(TCR_HEADER)
        fr_idx = text.find(FR_HEADER_TAIL, body_start)
        if fr_idx == -1:
            out.append(text[pos:])
            break
        tcr_body = text[body_start:fr_idx]
        out.append(text[pos:idx])
        out.append(TCR_HEADER)
        out.append(tcr_body)
        out.append(FR_HEADER_TAIL.rstrip("\n") + "\n")

        json_start = fr_idx + len(FR_HEADER_TAIL)
        if json_start >= len(text) or text[json_start] != "{":
            pos = json_start
            continue
        close_brace = _find_matching_brace(text, json_start)
        if close_brace == -1:
            pos = json_start
            continue
        fr_json = text[json_start:close_brace + 1]
        if tcr_body.strip() != "None":
            key = '"tool_calls": ['
            k_idx = fr_json.find(key)
            if k_idx != -1:
                arr_open = k_idx + len(key) - 1
                arr_close = _find_matching_bracket(fr_json, arr_open)
                if arr_close != -1:
                    fr_json = (fr_json[:k_idx] + '"tool_calls": '
                               '"<<same as Tool Calls Raw shown above>>"'
                               + fr_json[arr_close + 1:])
        out.append(fr_json)
        pos = close_brace + 1
    return "".join(out)


def _strip_internal_keys(v):
    """Recursively drop keys prefixed with '_' (e.g. `_session_id` injected
    into tool args by the loop, absent from the original LLM response)."""
    if isinstance(v, dict):
        return {k: _strip_internal_keys(val)
                for k, val in v.items() if not k.startswith("_")}
    if isinstance(v, list):
        return [_strip_internal_keys(x) for x in v]
    return v


def strip_tool_results_calls_dupe(text):
    """The "Calls:" list inside [TOOL RESULTS (multi)] repeats the
    preceding record's "Tool Calls Raw:" verbatim. Collapse it."""
    out = []
    pos = 0
    last_tcr_body = None
    while pos < len(text):
        tcr_idx = text.find(TCR_HEADER, pos)
        calls_idx = text.find(CALLS_HEADER, pos)
        if tcr_idx == -1 and calls_idx == -1:
            out.append(text[pos:])
            break
        if calls_idx == -1 or (tcr_idx != -1 and tcr_idx < calls_idx):
            body_start = tcr_idx + len(TCR_HEADER)
            fr_idx = text.find(FR_HEADER_TAIL, body_start)
            if fr_idx == -1:
                out.append(text[pos:])
                break
            last_tcr_body = text[body_start:fr_idx]
            out.append(text[pos:tcr_idx + len(TCR_HEADER)])
            out.append(last_tcr_body)
            pos = fr_idx
            continue
        # calls_idx comes next
        arr_start = calls_idx + len(CALLS_HEADER)
        if arr_start >= len(text) or text[arr_start] != "[":
            out.append(text[pos:calls_idx + len(CALLS_HEADER)])
            pos = arr_start
            continue
        arr_close = _find_matching_bracket(text, arr_start)
        if arr_close == -1:
            out.append(text[pos:calls_idx + len(CALLS_HEADER)])
            pos = arr_start
            continue
        calls_body = text[arr_start:arr_close + 1]
        out.append(text[pos:calls_idx])
        if last_tcr_body is not None and last_tcr_body.strip() != "None":
            try:
                tcr_parsed = json.loads(last_tcr_body)
                calls_parsed = json.loads(calls_body)
                tcr_norm = [{"name": c.get("name"), "args": c.get("arguments"),
                             "call_id": c.get("id")} for c in tcr_parsed]
                same = _strip_internal_keys(tcr_norm) == _strip_internal_keys(calls_parsed)
            except (json.JSONDecodeError, TypeError, AttributeError):
                same = False
            if same:
                out.append(CALLS_HEADER)
                out.append("<<same as Tool Calls Raw shown above>>")
                pos = arr_close + 1
                continue
        out.append(CALLS_HEADER)
        out.append(calls_body)
        pos = arr_close + 1
    return "".join(out)


# ---------------------------------------------------------------------------
# 4. Collapse runs of near-identical terminal diagnostic lines
# ---------------------------------------------------------------------------

# e.g. "[WS-DIAG] forwarding tool_result: tool=parse step=5 ok=False call_id='' result_len=260"
DIAG_LINE_RE = re.compile(
    r"^\[WS-DIAG\] forwarding tool_result: tool=(\S+) step=(\d+) ok=(\S+) "
    r"call_id='([^']*)' result_len=(\d+)\s*$"
)


def collapse_repeated_diag_lines(text):
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        m = DIAG_LINE_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        tool, step, ok, call_id, rlen = m.groups()
        run_start_step = step
        j = i + 1
        run_len = 1
        while j < len(lines):
            m2 = DIAG_LINE_RE.match(lines[j])
            if not m2:
                break
            t2, s2, ok2, cid2, rl2 = m2.groups()
            # only collapse the genuinely repetitive "parse rejection" pattern
            if t2 != tool or ok2 != ok or cid2 != call_id or rl2 != rlen:
                break
            # only worth collapsing runs of the same LLM-call boilerplate
            interstitial = lines[j - 1:j]
            run_len += 1
            j += 1
        if run_len >= 3:
            out.append(f"[WS-DIAG] forwarding tool_result: tool={tool} "
                       f"ok={ok} call_id='{call_id}' result_len={rlen} "
                       f"  <<repeated for steps {run_start_step}..{step_at(lines, j-1)} "
                       f"({run_len}x)>>")
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def step_at(lines, idx):
    m = DIAG_LINE_RE.match(lines[idx])
    return m.group(2) if m else "?"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def condense(
    text: str,
    *,
    no_sysprompt: bool = False,
    no_tool_schemas: bool = False,
) -> str:
    legend = BlockLegend()
    text = dedupe_named_blocks(text, legend)
    text = compress_messages_sent(text)
    text = strip_raw_response_dupe(text)
    text = strip_full_result_tool_calls_dupe(text)
    text = strip_tool_results_calls_dupe(text)
    text = collapse_repeated_diag_lines(text)
    if no_sysprompt:
        text = strip_sys_prompt(text)
    if no_tool_schemas:
        text = strip_tool_schemas(text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="path to the raw transcript .txt")
    ap.add_argument("-o", "--output", help="output path (default: stdout)")
    ap.add_argument("--stats", action="store_true",
                     help="print before/after size stats to stderr")
    ap.add_argument("--no-sysprompt", action="store_true",
                     help="replace System Prompt + agents.md content with a placeholder")
    ap.add_argument("--no-tool-schemas", action="store_true",
                     help="replace the [TOOL SCHEMAS] JSON dump with a placeholder")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    condensed = condense(
        original,
        no_sysprompt=args.no_sysprompt,
        no_tool_schemas=args.no_tool_schemas,
    )

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
