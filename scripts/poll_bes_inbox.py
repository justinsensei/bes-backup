#!/usr/bin/env python3
"""Poll Bes/Inbox in Justin's personal-main Gmail account for newly forwarded emails.

Layer B of the polling-cron-agent pattern. Queries unread messages with the
`Bes/Inbox` label on the personal-main account, filters against a watermark
of recently-seen message IDs, and emits one machine-parseable line per new
message. Silent (empty stdout) when nothing new — Hermes cron treats empty
stdout as a no-op.

State: ~/.hermes/state/bes-inbox-watermark.json
Account: personal-main (goff.justin@gmail.com)
Label: Bes/Inbox (Gmail-side filter on To: goff.justin+bes@gmail.com)

Read-only on Gmail. Never marks read, never modifies labels — the watermark
is the source of truth for "has Bes seen this?".
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


HERMES_HOME = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
VENV_PY = HERMES_HOME / "hermes-agent" / "venv" / "bin" / "python3"
GAPI = HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts" / "google_api.py"
WATERMARK_PATH = HERMES_HOME / "state" / "bes-inbox-watermark.json"

ACCOUNT = "personal-main"
GMAIL_QUERY = 'label:"Bes/Inbox" in:inbox newer_than:7d'  # Only search for emails in the inbox (excludes archived)
MAX_RESULTS = 25
SCHEMA_VERSION = 1


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def load_watermark() -> dict | None:
    if not WATERMARK_PATH.exists():
        return None
    try:
        return json.loads(WATERMARK_PATH.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARNING: watermark corrupt ({e}); reinitializing", file=sys.stderr)
        return None


def save_watermark(d: dict) -> None:
    WATERMARK_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = WATERMARK_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, indent=2))
    tmp.replace(WATERMARK_PATH)  # atomic


def query_gmail() -> list[dict]:
    env = {**os.environ, "GOOGLE_ACCOUNT": ACCOUNT}
    res = subprocess.run(
        [str(VENV_PY), str(GAPI), "gmail", "search", GMAIL_QUERY, "--max", str(MAX_RESULTS)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"gmail search failed (rc={res.returncode}): {res.stderr.strip()[:500]}"
        )
    out = res.stdout.strip()
    if not out or out == "No messages found.":
        return []
    return json.loads(out)


def main() -> int:
    wm = load_watermark()

    # First-run init: seed empty watermark, emit nothing. Backfill is opt-out
    # by design — Justin's existing test forwards (if any) won't trigger.
    if wm is None:
        save_watermark(
            {
                "schema_version": SCHEMA_VERSION,
                "initialized_at": now_utc_iso(),
                "last_run_at": now_utc_iso(),
                "seen_ids": [],
            }
        )
        return 0

    try:
        msgs = query_gmail()
    except Exception as e:
        # Surface to stderr — cron LLM gets the message but no false-positive lines.
        print(f"ERROR: poll_bes_inbox: {e}", file=sys.stderr)
        return 1

    seen_ids = set(wm.get("seen_ids") or [])
    new_msgs = [m for m in msgs if m.get("id") and m["id"] not in seen_ids]

    # Advance watermark unconditionally. We keep the union of (previously seen) +
    # (currently visible) IDs, capped at 200 to bound state growth. Old IDs
    # naturally fall out of the 7-day query window, so a bounded cap is safe.
    all_ids = list(seen_ids.union(m["id"] for m in msgs if m.get("id")))
    # Newest-first ordering: msgs from API come newest-first; preserve that for the cap.
    visible_ids = [m["id"] for m in msgs if m.get("id")]
    retained = []
    seen_check = set()
    for mid in visible_ids + sorted(seen_ids):  # visible first, then any older seen
        if mid not in seen_check:
            seen_check.add(mid)
            retained.append(mid)
        if len(retained) >= 200:
            break

    save_watermark(
        {
            "schema_version": SCHEMA_VERSION,
            "initialized_at": wm.get("initialized_at") or now_utc_iso(),
            "last_run_at": now_utc_iso(),
            "seen_ids": retained,
        }
    )

    # Silent on no-op
    if not new_msgs:
        return 0

    if "--json" in sys.argv:
        json_msgs = []
        for m in new_msgs:
            json_msgs.append({
                "id": m.get("id"),
                "from": m.get("from", "").replace("\n", " ").strip(),
                "subject": m.get("subject", "").replace("\n", " ").strip(),
                "snippet": m.get("snippet", "").replace("\n", " ").strip()
            })
        print(json.dumps(json_msgs, indent=2))
        return 0

    # Emit summary header + one structured line per new message
    print(f"NEW_FORWARDED_EMAILS: {len(new_msgs)}")
    for m in new_msgs:
        # Best-effort one-line summary; the handler does the real fetch.
        subj = (m.get("subject") or "").replace("\n", " ").strip()[:120]
        frm = (m.get("from") or "").replace("\n", " ").strip()[:80]
        snip = (m.get("snippet") or "").replace("\n", " ").strip()[:140]
        print(f"- id={m.get('id')} from={frm!r} subject={subj!r} snippet={snip!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
