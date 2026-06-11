#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import argparse
import datetime

CACHE_FILE = os.path.expanduser("~/.hermes/processed_telegram_brains.json")
DB_FILE = os.path.expanduser("~/.hermes/state.db")

def load_processed():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_processed(processed):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(processed, f, indent=2)

def mark_session_processed(session_id):
    processed = load_processed()
    if session_id not in processed:
        processed.append(session_id)
        save_processed(processed)
    
    # Also update DB ingested = 1
    if os.path.exists(DB_FILE):
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE sessions SET ingested = 1 WHERE id = ?", (session_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            sys.stderr.write(f"Error updating DB for session {session_id}: {e}\n")

def fetch_flagged_sessions():
    if not os.path.exists(DB_FILE):
        sys.stderr.write(f"Database file not found: {DB_FILE}\n")
        return []

    processed_set = set(load_processed())

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Find candidate sessions
    # Filter out already processed sessions using ingested = 0
    query = """
    SELECT DISTINCT s.id, s.title, s.started_at, s.ended_at, s.message_count, s.source
    FROM sessions s
    LEFT JOIN messages m ON s.id = m.session_id
    WHERE s.source = 'telegram'
      AND s.ingested = 0
      AND (s.brain_flagged = 1 OR (m.role = 'user' AND m.content LIKE '%🧠%'))
    """
    
    c.execute(query)
    rows = c.fetchall()

    results = []
    for r in rows:
        session_id = r["id"]
        
        # Double check cache file
        if session_id in processed_set:
            # Sync DB state to make sure ingested=1
            try:
                db_conn2 = sqlite3.connect(DB_FILE)
                db_conn2.execute("UPDATE sessions SET ingested = 1 WHERE id = ?", (session_id,))
                db_conn2.commit()
                db_conn2.close()
            except Exception:
                pass
            continue

        # Fetch messages for this session
        c.execute("""
            SELECT role, content, timestamp, platform_message_id
            FROM messages
            WHERE session_id = ? AND active = 1
            ORDER BY timestamp ASC
        """, (session_id,))
        msg_rows = c.fetchall()

        messages = []
        for mr in msg_rows:
            content = mr["content"] or ""
            messages.append({
                "role": mr["role"],
                "content": content,
                "timestamp": mr["timestamp"],
                "message_id": mr["platform_message_id"]
            })

        if not messages:
            continue

        # Format started_at to ISO string
        started_dt = datetime.datetime.fromtimestamp(r["started_at"])
        started_iso = started_dt.isoformat()

        title = r["title"] or f"Telegram Session {started_dt.strftime('%Y-%m-%d %H:%M')}"

        results.append({
            "session_id": session_id,
            "title": title,
            "started_at": started_iso,
            "source_db": DB_FILE,
            "message_count": len(messages),
            "messages": messages
        })

    conn.close()
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-processed", help="Mark a session ID as processed")
    args = parser.parse_args()

    if args.mark_processed:
        mark_session_processed(args.mark_processed)
        print(json.dumps({"ok": True, "marked": args.mark_processed}))
        sys.exit(0)

    sessions = fetch_flagged_sessions()
    print(json.dumps(sessions, indent=2))

if __name__ == "__main__":
    main()
