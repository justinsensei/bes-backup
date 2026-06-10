#!/usr/bin/env python3
"""Load context for one forwarded email and parse out Justin's instruction.

Reads a Gmail message ID from argv, fetches via the google-workspace skill's
google_api.py against the personal-main account, and returns a JSON payload
with the parsed-out instruction, forwarded-original metadata, and a cleaned
body. Always exits 0 even on error — errors land in the JSON as
`is_real: false` + `error: "..."`. The caller decides what to do.

Usage:
  python3 load_context.py <MESSAGE_ID>

Output: JSON to stdout, one object.
"""
from __future__ import annotations

import html as html_module
import json
import os
import re
import subprocess
import sys
from pathlib import Path


HERMES_HOME = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
VENV_PY = HERMES_HOME / "hermes-agent" / "venv" / "bin" / "python3"
GAPI = HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts" / "google_api.py"
ACCOUNT = "personal-main"  # goff.justin@gmail.com


# Common quoted-reply markers people's mail clients prepend on forward.
FORWARD_MARKERS = [
    r"-+\s*Forwarded message\s*-+",
    r"Begin forwarded message:",
    r"_{3,}\s*\n\s*From:",  # Outlook-style hr + From:
]
FORWARD_MARKER_RE = re.compile("|".join(FORWARD_MARKERS), re.IGNORECASE)

# Headers that appear inside the forwarded block.
HEADER_RE = re.compile(
    r"^\s*(From|To|Cc|Sent|Date|Subject)\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def run_gmail_get(message_id: str) -> dict:
    """Invoke google_api.py gmail get <id> on the personal-main account."""
    env = {**os.environ, "GOOGLE_ACCOUNT": ACCOUNT}
    res = subprocess.run(
        [str(VENV_PY), str(GAPI), "gmail", "get", message_id],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"google_api.py exited {res.returncode}: {res.stderr.strip()[:500]}"
        )
    return json.loads(res.stdout)


def html_to_text(s: str) -> str:
    """Best-effort HTML → plaintext. Stdlib-only; for high-quality conversion the
    handler can re-fetch and run a richer converter. For instruction-parsing we
    just need readable plaintext at the top of the body.
    """
    if not s:
        return ""
    # Drop <style> and <script> blocks entirely
    s = re.sub(r"(?is)<(style|script)[^>]*>.*?</\1>", " ", s)
    # Turn <br>, </p>, </div>, <tr> into newlines
    s = re.sub(r"(?i)<\s*(br|/p|/div|/tr|/li)\s*/?\s*>", "\n", s)
    # Strip remaining tags
    s = re.sub(r"<[^>]+>", "", s)
    # Decode entities
    s = html_module.unescape(s)
    # Collapse runs of blank lines and trailing whitespace per line
    lines = [ln.rstrip() for ln in s.splitlines()]
    out_lines: list[str] = []
    prev_blank = False
    for ln in lines:
        is_blank = (ln.strip() == "")
        if is_blank and prev_blank:
            continue
        out_lines.append(ln)
        prev_blank = is_blank
    return "\n".join(out_lines).strip()


def looks_like_html(s: str) -> bool:
    if not s:
        return False
    head = s.lstrip()[:512].lower()
    return ("<html" in head) or ("<!doctype html" in head) or ("<body" in head) or \
           ("<table" in head and "<tr" in head) or ("<div" in head and "</div>" in s.lower())


def clean_subject(subject: str) -> str:
    """Strip leading Fwd:/Fw: prefixes (possibly nested) and collapse whitespace."""
    if not subject:
        return ""
    s = subject
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"^\s*(Fwd?|FW|Re):\s*", "", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()


def split_instruction_and_forward(body_text: str) -> tuple[str, str | None]:
    """Return (instruction_text, body_after_forward_marker_or_None).

    `body_text` should already be plaintext (HTML stripped). Splits on the
    first forwarding marker. Text before the marker is Justin's instruction
    (often empty if he just forwarded without commenting). Text including+after
    the marker is the original email.

    If no forward marker is present, we DO NOT treat the whole body as an
    instruction — that produces garbage when an HTML email has no plaintext
    forward wrapper. Instead, return ("", None) and let the caller fall back
    to default-save semantics.
    """
    if not body_text:
        return "", None
    m = FORWARD_MARKER_RE.search(body_text)
    if not m:
        return "", None
    head = body_text[: m.start()].strip()
    tail = body_text[m.start() :]
    return head, tail


def strip_quote_markers(text: str) -> str:
    """Drop leading '>' quote markers many clients add."""
    lines = []
    for line in text.splitlines():
        stripped = re.sub(r"^>+\s?", "", line)
        lines.append(stripped)
    return "\n".join(lines).strip()


def parse_forwarded_headers(tail: str) -> dict:
    """Pull From/Subject/Date out of the top of the forwarded block."""
    if not tail:
        return {}
    # Look only in the first ~20 non-empty lines after the marker.
    lines = tail.splitlines()
    # Skip the marker line itself.
    marker_idx = 0
    for i, ln in enumerate(lines):
        if FORWARD_MARKER_RE.search(ln):
            marker_idx = i
            break
    header_block = "\n".join(lines[marker_idx : marker_idx + 25])
    headers = {}
    for m in HEADER_RE.finditer(header_block):
        key = m.group(1).lower()
        val = m.group(2).strip()
        if key not in headers:  # take first occurrence
            headers[key] = val
    return headers


def forwarded_body_only(tail: str) -> str:
    """Return the forwarded-message body, dropping the header block."""
    if not tail:
        return ""
    lines = tail.splitlines()
    # Find marker line, then skip past contiguous header lines (and blanks).
    start = 0
    for i, ln in enumerate(lines):
        if FORWARD_MARKER_RE.search(ln):
            start = i + 1
            break
    # Now skip lines that look like headers or blanks.
    i = start
    while i < len(lines):
        ln = lines[i].strip()
        if not ln:
            i += 1
            continue
        if HEADER_RE.match(lines[i]):
            i += 1
            continue
        break
    return strip_quote_markers("\n".join(lines[i:]).strip())


def determine_instruction(parsed_head: str, subject_clean: str, raw_subject: str) -> tuple[str, str]:
    """Return (instruction_text, instruction_source).

    Source is "body", "subject", or "none".
    """
    head = strip_quote_markers(parsed_head).strip()
    if head:
        # First paragraph (up to first blank line) is the instruction. Cap at
        # 600 chars defensively — anything longer is suspicious for an
        # instruction and likely indicates a parsing miss.
        para = head.split("\n\n", 1)[0].strip()
        if para and len(para) <= 600:
            return para, "body"
        if para:
            # Truncate but flag in source label
            return para[:600].rstrip() + " …[truncated]", "body"
    # Check whether the subject (after stripping Fwd:) starts with a bracket
    # tag like [note], [person:Jane]. Treat that as instruction source.
    m = re.match(r"^\s*\[([^\]]+)\]\s*", raw_subject or "")
    if m:
        return f"[{m.group(1).strip()}]", "subject"
    return "", "none"


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"is_real": False, "error": "usage: load_context.py <MESSAGE_ID>"}))
        return 0
    message_id = sys.argv[1].strip()
    if not message_id:
        print(json.dumps({"is_real": False, "error": "empty message id"}))
        return 0

    try:
        msg = run_gmail_get(message_id)
    except Exception as e:
        print(json.dumps({"is_real": False, "id": message_id, "error": str(e)[:500]}))
        return 0

    body_raw = msg.get("body") or ""
    is_html = looks_like_html(body_raw)
    body_text = html_to_text(body_raw) if is_html else body_raw

    subject_raw = msg.get("subject") or ""
    subject_clean = clean_subject(subject_raw)

    head, tail = split_instruction_and_forward(body_text)
    fwd_headers = parse_forwarded_headers(tail) if tail else {}
    fwd_body = forwarded_body_only(tail) if tail else body_text

    instruction, instruction_source = determine_instruction(head, subject_clean, subject_raw)

    out = {
        "is_real": True,
        "id": msg.get("id") or message_id,
        "thread_id": msg.get("threadId"),
        "from": msg.get("from") or "",
        "to": msg.get("to") or "",
        "date": msg.get("date") or "",
        "subject": subject_raw,
        "subject_clean": subject_clean,
        "labels": msg.get("labels") or [],
        "body_text": body_text,           # plaintext (HTML stripped if needed)
        "body_is_html": is_html,
        "instruction": instruction,
        "instruction_source": instruction_source,
        "forwarded_from": fwd_headers.get("from", ""),
        "forwarded_to": fwd_headers.get("to", ""),
        "forwarded_subject": fwd_headers.get("subject", "") or subject_clean,
        "forwarded_date": fwd_headers.get("date", "") or fwd_headers.get("sent", ""),
        "forwarded_body": fwd_body,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
