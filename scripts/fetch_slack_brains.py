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

def get_parent_ts(client, channel_id, ts):
    try:
        res = client.conversations_history(channel=channel_id, latest=ts, limit=1, inclusive=True)
        msgs = res.get("messages", [])
        if msgs:
            m = msgs[0]
            if m.get("thread_ts"):
                return m.get("thread_ts")
            return ts
    except Exception:
        pass
    return ts

def fetch_note_candidates(client):
    import datetime as dt
    user_id = client.auth_test()["user_id"]
    processed = load_processed()
    processed_set = {f"{p['channel']}:{p['ts']}" for p in processed}
    
    # Check last 36 hours for candidate conversations
    start_date = (dt.date.today() - dt.timedelta(days=2)).strftime("%Y-%m-%d")
    
    # 1. Search messages from Justin
    try:
        res_from = client.search_messages(query=f"from:me after:{start_date}", count=30)
        matches_from = res_from.get("messages", {}).get("matches", [])
    except Exception:
        matches_from = []
        
    # 2. Search mentions of Justin
    try:
        res_ment = client.search_messages(query=f"<@{user_id}> after:{start_date}", count=30)
        matches_ment = res_ment.get("messages", {}).get("matches", [])
    except Exception:
        matches_ment = []
        
    all_matches = matches_from + matches_ment
    
    # Find unique (channel_id, parent_ts) threads
    unique_conversations = set()
    for m in all_matches:
        channel_id = (m.get("channel") or {}).get("id")
        ts = m.get("ts")
        if channel_id and ts:
            unique_conversations.add((channel_id, ts))
            
    unique_threads = set()
    for channel_id, ts in unique_conversations:
        parent_ts = get_parent_ts(client, channel_id, ts)
        unique_threads.add((channel_id, parent_ts))
        
    candidates = []
    for channel_id, parent_ts in unique_threads:
        key = f"{channel_id}:{parent_ts}"
        if key in processed_set:
            continue
            
        try:
            r = client.conversations_replies(channel=channel_id, ts=parent_ts, limit=100)
            messages = r.get("messages", [])
        except SlackApiError:
            continue
            
        if len(messages) < 3:
            continue
            
        # Verify Justin participated
        participated = any(m.get("user") == user_id for m in messages)
        if not participated:
            continue
            
        # Verify distinct users
        users = {m.get("user") for m in messages if m.get("user")}
        if len(users) < 2:
            continue
            
        # Check if Justin added a jg_log or jg_decision reaction to any message in the thread
        has_brain = False
        for m in messages:
            for rxn in m.get("reactions", []):
                if rxn.get("name") in ["jg_log", "jg_decision"] and user_id in rxn.get("users", []):
                    has_brain = True
                    break
            if has_brain:
                break
                
        if has_brain:
            continue
            
        # Resolve all users in messages
        resolve_users_in_messages(client, messages)
        
        # Clean messages
        cleaned_messages = [clean_message(m, client) for m in messages]
        
        # Get permalink
        permalink = None
        try:
            pl = client.chat_getPermalink(channel=channel_id, message_ts=parent_ts)
            permalink = pl.get("permalink")
        except SlackApiError:
            permalink = f"https://signlab.slack.com/archives/{channel_id}/p{parent_ts.replace('.', '')}"
            
        channel_name = get_channel_name(client, channel_id)
        
        participants_names = list(set(m["user_name"] for m in cleaned_messages if m.get("user_name")))
        
        candidates.append({
            "channel_id": channel_id,
            "channel_name": channel_name,
            "ts": parent_ts,
            "permalink": permalink,
            "is_thread": True,
            "message_count": len(cleaned_messages),
            "participants": participants_names,
            "messages": cleaned_messages,
            "preview": cleaned_messages[0]["text"][:150] + "..." if len(cleaned_messages[0]["text"]) > 150 else cleaned_messages[0]["text"]
        })
        
    return candidates

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
            
        # Verify Justin added the reaction 'jg_log' or 'jg_decision'
        reaction_type = None
        for rxn in msg.get("reactions", []):
            if rxn.get("name") in ["jg_log", "jg_decision"] and user_id in rxn.get("users", []):
                reaction_type = rxn.get("name")
                break
        
        if not reaction_type:
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
            "reacted_message_ts": ts,
            "reaction_type": reaction_type
        })
        
    return new_brains

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-new", action="store_true", help="List unprocessed messages with brain reaction")
    parser.add_argument("--list-candidates", action="store_true", help="List candidate threads for manual note selection")
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
        
    if args.list_candidates:
        candidates = fetch_note_candidates(client)
        print(json.dumps(candidates, indent=2))
        sys.exit(0)
        
    # Default behavior if no specific command args are passed
    new_items = fetch_new_brains(client)
    print(json.dumps(new_items, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()
