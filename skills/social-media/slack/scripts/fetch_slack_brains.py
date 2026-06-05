#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

CACHE_FILE = os.path.expanduser("~/.hermes/processed_slack_brains.json")

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

def get_client():
    token = os.environ.get("SLACK_USER_TOKEN")
    if not token:
        # Try loading from ~/.hermes/.env
        env_path = os.path.expanduser("~/.hermes/.env")
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SLACK_USER_TOKEN=") and "=" in line:
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        os.environ["SLACK_USER_TOKEN"] = token
                        break
    if not token:
        print("Error: SLACK_USER_TOKEN not set", file=sys.stderr)
        sys.exit(3)
    return WebClient(token=token)

_USER_CACHE = {}

def pick_user_display(profile, fallback=""):
    p = profile or {}
    return (
        p.get("display_name_normalized")
        or p.get("display_name")
        or p.get("real_name_normalized")
        or p.get("real_name")
        or fallback
    )

def resolve_user(client, user_id):
    if not user_id:
        return "?"
    if not user_id.startswith("U"):
        return user_id
    if user_id in _USER_CACHE:
        return _USER_CACHE[user_id]
    try:
        r = client.users_info(user=user_id)
        name = pick_user_display(r["user"].get("profile", {}), user_id)
        _USER_CACHE[user_id] = name
        return name
    except SlackApiError:
        _USER_CACHE[user_id] = user_id
        return user_id

def resolve_users_in_messages(client, messages):
    uids = set()
    for m in messages:
        if m.get("user"):
            uids.add(m["user"])
        for mt in re.findall(r"<@(U[A-Z0-9]+)>", m.get("text") or ""):
            uids.add(mt)
    for uid in uids:
        resolve_user(client, uid)

def clean_message(m, client):
    user_id = m.get("user") or m.get("bot_id") or "?"
    user_name = resolve_user(client, user_id)
    text = m.get("text") or ""
    
    # Resolve inline user mentions
    def _sub(match):
        uid = match.group(1)
        return f"@{resolve_user(client, uid)}"
    text = re.sub(r"<@(U[A-Z0-9]+)>", _sub, text)
    
    return {
        "ts": m.get("ts"),
        "user_id": user_id,
        "user_name": user_name,
        "text": text
    }

def get_channel_name(client, channel_id):
    try:
        r = client.conversations_info(channel=channel_id)
        ch = r.get("channel") or {}
        if ch.get("is_im"):
            user_id = ch.get("user")
            user_name = resolve_user(client, user_id)
            return f"dm-{user_name}"
        return ch.get("name") or channel_id
    except Exception:
        return channel_id

def fetch_new_brains(client):
    user_id = client.auth_test()["user_id"]
    processed = load_processed()
    processed_set = {f"{p['channel']}:{p['ts']}" for p in processed}
    
    try:
        res = client.reactions_list(user=user_id, limit=30)
    except SlackApiError as e:
        print(f"Error fetching reactions list: {e}", file=sys.stderr)
        sys.exit(1)
        
    new_brains = []
    for item in res.get("items", []):
        if item.get("type") != "message":
            continue
        channel_id = item.get("channel")
        msg = item.get("message", {})
        ts = msg.get("ts")
        
        # Check if already processed
        key = f"{channel_id}:{ts}"
        if key in processed_set:
            continue
            
        # Verify Justin added the reaction 'brain'
        has_brain = False
        for rxn in msg.get("reactions", []):
            if rxn.get("name") == "brain" and user_id in rxn.get("users", []):
                has_brain = True
                break
        
        if not has_brain:
            continue
            
        # Retrieve context
        thread_ts = msg.get("thread_ts")
        messages = []
        is_thread = False
        
        if thread_ts:
            # Fetch full thread
            try:
                r = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=100)
                messages = r.get("messages", [])
                is_thread = True
            except SlackApiError as e:
                print(f"Error fetching thread {thread_ts} in {channel_id}: {e}", file=sys.stderr)
                # Fall back to single message if thread reading fails
                messages = [msg]
        else:
            # Fetch surrounding context (5 before, 5 after)
            try:
                # 5 preceding messages (including current)
                res_prec = client.conversations_history(channel=channel_id, latest=ts, limit=6, inclusive=True)
                msgs_prec = res_prec.get("messages", [])
                
                # 5 subsequent messages (including current)
                res_sub = client.conversations_history(channel=channel_id, oldest=ts, limit=6, inclusive=True)
                msgs_sub = res_sub.get("messages", [])
                
                # Combine and deduplicate
                combined = {}
                for m in msgs_prec + msgs_sub:
                    combined[m["ts"]] = m
                messages = [combined[key_ts] for key_ts in sorted(combined.keys())]
            except SlackApiError as e:
                print(f"Error fetching context for {ts} in {channel_id}: {e}", file=sys.stderr)
                messages = [msg]
                
        # Resolve all users in messages
        resolve_users_in_messages(client, messages)
        
        # Clean messages
        cleaned_messages = [clean_message(m, client) for m in messages]
        
        # Get permalink
        permalink = None
        try:
            pl = client.chat_getPermalink(channel=channel_id, message_ts=ts)
            permalink = pl.get("permalink")
        except SlackApiError:
            permalink = f"https://signlab.slack.com/archives/{channel_id}/p{ts.replace('.', '')}"
            
        channel_name = get_channel_name(client, channel_id)
        
        new_brains.append({
            "channel_id": channel_id,
            "channel_name": channel_name,
            "ts": ts,
            "permalink": permalink,
            "is_thread": is_thread,
            "messages": cleaned_messages,
            "reacted_message_ts": ts
        })
        
    return new_brains

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-new", action="store_true", help="List unprocessed messages with brain reaction")
    parser.add_argument("--mark-processed", nargs=2, metavar=("CHANNEL_ID", "TS"), help="Mark message as processed")
    args = parser.parse_args()
    
    client = get_client()
    
    if args.mark_processed:
        channel_id, ts = args.mark_processed
        processed = load_processed()
        # check if already exists to prevent duplicate
        key = f"{channel_id}:{ts}"
        if not any(p["channel"] == channel_id and p["ts"] == ts for p in processed):
            processed.append({"channel": channel_id, "ts": ts})
            save_processed(processed)
            print(json.dumps({"ok": True, "marked": key}))
        else:
            print(json.dumps({"ok": True, "already_processed": key}))
        sys.exit(0)
        
    if args.list_new:
        new_items = fetch_new_brains(client)
        print(json.dumps(new_items, indent=2))
        sys.exit(0)
        
    parser.print_help()

if __name__ == "__main__":
    main()
