#!/usr/bin/env python3
"""Thin Slack user-token wrapper for Bes.

Operates as Justin via xoxp- token. All subcommands print JSON unless --text
is passed (only meaningful for message-list outputs).

Env vars:
  SLACK_USER_TOKEN  required, starts with xoxp-

Exit codes:
  0  success
  1  Slack API error
  2  usage / missing arg
  3  auth (missing or invalid token)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from typing import Any

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("slack_sdk not installed in this venv. Run:", file=sys.stderr)
    print(
        "  VIRTUAL_ENV=~/.hermes/hermes-agent/venv ~/.local/bin/uv pip install slack_sdk",
        file=sys.stderr,
    )
    sys.exit(3)


# ──────────────────────────────────────────────────────────────────────────
# pure helpers (unit-testable)
# ──────────────────────────────────────────────────────────────────────────

_RELATIVE_RE = re.compile(r"^(\d+)([hdw])$")


def parse_since(since: str) -> float:
    """Convert '24h' / '2d' / '1w' / 'YYYY-MM-DD' to a unix timestamp (UTC)."""
    if not since:
        # default: 24h
        return time.time() - 86400
    m = _RELATIVE_RE.match(since.strip().lower())
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"h": 3600, "d": 86400, "w": 604800}[unit] * n
        return time.time() - delta
    # try YYYY-MM-DD
    try:
        d = dt.datetime.strptime(since.strip(), "%Y-%m-%d").replace(
            tzinfo=dt.timezone.utc
        )
        return d.timestamp()
    except ValueError:
        raise SystemExit(f"unrecognized --since value: {since!r}")


def render_message_line(msg: dict, user_lookup: dict[str, str]) -> str:
    """Render one message dict as a human-readable line."""
    ts_str = msg.get("ts") or "0"
    try:
        when = dt.datetime.fromtimestamp(float(ts_str), tz=dt.timezone.utc)
        ts_fmt = when.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        ts_fmt = "??"
    user_id = msg.get("user") or msg.get("bot_id") or "?"
    user_name = user_lookup.get(user_id, user_id)
    text = msg.get("text") or ""
    # resolve <@U...> mentions inline
    def _sub(m):
        uid = m.group(1)
        return f"@{user_lookup.get(uid, uid)}"

    text = re.sub(r"<@(U[A-Z0-9]+)>", _sub, text)
    reply_count = msg.get("reply_count")
    suffix = f"  [+{reply_count} replies]" if reply_count else ""
    return f"{ts_fmt}  {user_name}: {text}{suffix}"


def pick_user_display(profile: dict, fallback: str = "") -> str:
    """Best-name choice for a Slack user."""
    p = profile or {}
    return (
        p.get("display_name_normalized")
        or p.get("display_name")
        or p.get("real_name_normalized")
        or p.get("real_name")
        or fallback
    )


# ──────────────────────────────────────────────────────────────────────────
# client
# ──────────────────────────────────────────────────────────────────────────


def get_client() -> WebClient:
    tok = os.environ.get("SLACK_USER_TOKEN")
    if not tok:
        print("SLACK_USER_TOKEN not set in environment", file=sys.stderr)
        sys.exit(3)
    if not tok.startswith("xoxp-"):
        print(
            f"SLACK_USER_TOKEN does not look like a user token (got {tok[:5]}...). "
            "This skill is designed for xoxp- tokens, not xoxb-.",
            file=sys.stderr,
        )
        sys.exit(3)
    return WebClient(token=tok)


_USER_CACHE: dict[str, str] = {}


def resolve_users(client: WebClient, user_ids: list[str]) -> dict[str, str]:
    """Return id -> display name map; caches across calls in this process."""
    missing = [u for u in user_ids if u and u not in _USER_CACHE and u.startswith("U")]
    for uid in missing:
        try:
            r = client.users_info(user=uid)
            _USER_CACHE[uid] = pick_user_display(r["user"].get("profile", {}), uid)
        except SlackApiError:
            _USER_CACHE[uid] = uid
    return {u: _USER_CACHE.get(u, u) for u in user_ids if u}


def call(method, **kwargs):
    """Run a Slack API call; print the error JSON cleanly on failure."""
    try:
        return method(**kwargs)
    except SlackApiError as e:
        err = e.response.get("error") if e.response else str(e)
        needed = e.response.get("needed") if e.response else None
        out = {"ok": False, "error": err}
        if needed:
            out["needed_scope"] = needed
        print(json.dumps(out, indent=2), file=sys.stderr)
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────
# subcommands
# ──────────────────────────────────────────────────────────────────────────


def cmd_whoami(args, client):
    r = call(client.auth_test)
    print(
        json.dumps(
            {
                "user_id": r["user_id"],
                "team_id": r["team_id"],
                "team": r["team"],
                "user": r["user"],
                "url": r.get("url"),
            },
            indent=2,
        )
    )


def cmd_channels(args, client):
    type_map = {
        "public": "public_channel",
        "private": "private_channel",
        "im": "im",
        "mpim": "mpim",
        "all": "public_channel,private_channel,im,mpim",
    }
    types = type_map.get(args.type, "public_channel,private_channel")
    out: list[dict] = []
    cursor = None
    fetched = 0
    while True:
        r = call(
            client.conversations_list,
            types=types,
            limit=200,
            cursor=cursor,
            exclude_archived=True,
        )
        for ch in r.get("channels", []):
            if args.member_only and not ch.get("is_member") and not ch.get("is_im") and not ch.get("is_mpim"):
                continue
            entry = {
                "id": ch["id"],
                "name": ch.get("name") or ch.get("name_normalized") or "",
                "is_private": ch.get("is_private", False),
                "is_im": ch.get("is_im", False),
                "is_mpim": ch.get("is_mpim", False),
                "is_member": ch.get("is_member", False),
                "num_members": ch.get("num_members"),
            }
            if ch.get("is_im"):
                entry["user"] = ch.get("user")
            out.append(entry)
            fetched += 1
            if args.limit and fetched >= args.limit:
                break
        if args.limit and fetched >= args.limit:
            break
        cursor = (r.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
    # resolve IM user names if we have any
    im_user_ids = [c["user"] for c in out if c.get("is_im") and c.get("user")]
    if im_user_ids:
        names = resolve_users(client, im_user_ids)
        for c in out:
            if c.get("user"):
                c["user_name"] = names.get(c["user"], c["user"])
    print(json.dumps(out, indent=2))


def cmd_read(args, client):
    oldest = parse_since(args.since)
    r = call(
        client.conversations_history,
        channel=args.channel,
        oldest=str(oldest),
        limit=args.limit,
    )
    msgs = list(reversed(r.get("messages", [])))  # oldest first
    # resolve user IDs
    uids = set()
    for m in msgs:
        if m.get("user"):
            uids.add(m["user"])
        for mt in re.findall(r"<@(U[A-Z0-9]+)>", m.get("text") or ""):
            uids.add(mt)
    name_lookup = resolve_users(client, list(uids))
    if args.text:
        for m in msgs:
            print(render_message_line(m, name_lookup))
        return
    # JSON: strip noise, attach resolved names
    out = []
    for m in msgs:
        out.append(
            {
                "ts": m.get("ts"),
                "user": m.get("user"),
                "user_name": name_lookup.get(m.get("user"), m.get("user")),
                "text": m.get("text"),
                "thread_ts": m.get("thread_ts"),
                "reply_count": m.get("reply_count"),
                "reactions": [
                    {"name": rxn["name"], "count": rxn["count"]}
                    for rxn in (m.get("reactions") or [])
                ],
            }
        )
    print(json.dumps(out, indent=2))


def cmd_thread(args, client):
    r = call(
        client.conversations_replies,
        channel=args.channel,
        ts=args.thread_ts,
        limit=200,
    )
    msgs = r.get("messages", [])
    uids = set()
    for m in msgs:
        if m.get("user"):
            uids.add(m["user"])
        for mt in re.findall(r"<@(U[A-Z0-9]+)>", m.get("text") or ""):
            uids.add(mt)
    name_lookup = resolve_users(client, list(uids))
    if args.text:
        for m in msgs:
            print(render_message_line(m, name_lookup))
        return
    out = []
    for m in msgs:
        out.append(
            {
                "ts": m.get("ts"),
                "user": m.get("user"),
                "user_name": name_lookup.get(m.get("user"), m.get("user")),
                "text": m.get("text"),
                "thread_ts": m.get("thread_ts"),
                "reactions": [
                    {"name": rxn["name"], "count": rxn["count"]}
                    for rxn in (m.get("reactions") or [])
                ],
            }
        )
    print(json.dumps(out, indent=2))


def cmd_search(args, client):
    r = call(
        client.search_messages,
        query=args.query,
        count=args.limit,
        sort="timestamp",
        sort_dir="desc",
    )
    matches = (r.get("messages") or {}).get("matches", [])
    if args.text:
        # collect users for prettier DM rendering
        dm_users = set()
        for m in matches:
            ch = m.get("channel") or {}
            if ch.get("is_im") and ch.get("user"):
                dm_users.add(ch["user"])
        names = resolve_users(client, list(dm_users)) if dm_users else {}
        for m in matches:
            ts = m.get("ts", "0")
            try:
                when = dt.datetime.fromtimestamp(
                    float(ts), tz=dt.timezone.utc
                ).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                when = "??"
            ch = m.get("channel") or {}
            if ch.get("is_im"):
                ch_label = f"dm:{names.get(ch.get('user'), ch.get('user', '?'))}"
            elif ch.get("is_mpim"):
                ch_label = f"gdm:{ch.get('name', '?')}"
            elif ch.get("is_private"):
                ch_label = f"priv:{ch.get('name', '?')}"
            else:
                ch_label = f"#{ch.get('name') or ch.get('id', '?')}"
            user = m.get("username") or m.get("user") or "?"
            text = (m.get("text") or "").replace("\n", " ")
            print(f"{when}  {ch_label}  {user}: {text[:160]}")
        return
    out = []
    for m in matches:
        out.append(
            {
                "ts": m.get("ts"),
                "channel_id": (m.get("channel") or {}).get("id"),
                "channel_name": (m.get("channel") or {}).get("name"),
                "user": m.get("user"),
                "username": m.get("username"),
                "text": m.get("text"),
                "permalink": m.get("permalink"),
            }
        )
    print(json.dumps(out, indent=2))


def cmd_post(args, client):
    kwargs = {"channel": args.channel, "text": args.text, "as_user": True}
    if args.thread:
        kwargs["thread_ts"] = args.thread
        if args.broadcast:
            kwargs["reply_broadcast"] = True
    r = call(client.chat_postMessage, **kwargs)
    out = {"ok": True, "ts": r.get("ts"), "channel": r.get("channel")}
    # fetch permalink for citation
    try:
        pl = client.chat_getPermalink(channel=r["channel"], message_ts=r["ts"])
        out["permalink"] = pl.get("permalink")
    except SlackApiError:
        pass
    print(json.dumps(out, indent=2))


def cmd_react(args, client):
    r = call(
        client.reactions_add,
        channel=args.channel,
        timestamp=args.timestamp,
        name=args.emoji.strip(":"),
    )
    print(json.dumps({"ok": r.get("ok", False)}, indent=2))


def cmd_permalink(args, client):
    r = call(client.chat_getPermalink, channel=args.channel, message_ts=args.timestamp)
    print(json.dumps({"permalink": r.get("permalink")}, indent=2))


def cmd_user(args, client):
    r = call(client.users_info, user=args.user_id)
    u = r.get("user") or {}
    p = u.get("profile") or {}
    print(
        json.dumps(
            {
                "id": u.get("id"),
                "name": u.get("name"),
                "real_name": u.get("real_name"),
                "display_name": pick_user_display(p, u.get("name", "")),
                "email": p.get("email"),
                "title": p.get("title"),
                "status_text": p.get("status_text"),
                "is_bot": u.get("is_bot", False),
                "deleted": u.get("deleted", False),
            },
            indent=2,
        )
    )


def cmd_dm(args, client):
    # resolve @name to user_id if needed
    user_id = args.user
    if user_id.startswith("@"):
        target = user_id.lstrip("@").lower()
        cursor = None
        found = None
        while not found:
            r = call(client.users_list, limit=200, cursor=cursor)
            for u in r.get("members", []):
                if u.get("name", "").lower() == target or pick_user_display(
                    u.get("profile") or {}, ""
                ).lower() == target:
                    found = u["id"]
                    break
            cursor = (r.get("response_metadata") or {}).get("next_cursor")
            if not cursor:
                break
        if not found:
            print(json.dumps({"ok": False, "error": f"user not found: {args.user}"}), file=sys.stderr)
            sys.exit(1)
        user_id = found
    # open DM channel
    r = call(client.conversations_open, users=user_id)
    channel_id = r["channel"]["id"]
    msg = call(client.chat_postMessage, channel=channel_id, text=args.text, as_user=True)
    out = {"ok": True, "channel": channel_id, "ts": msg.get("ts"), "user_id": user_id}
    try:
        pl = client.chat_getPermalink(channel=channel_id, message_ts=msg["ts"])
        out["permalink"] = pl.get("permalink")
    except SlackApiError:
        pass
    print(json.dumps(out, indent=2))


# ──────────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(prog="slack", description="Slack user-token wrapper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami", help="show authed user identity")

    p = sub.add_parser("channels", help="list channels/DMs/groups")
    p.add_argument("--type", choices=["public", "private", "im", "mpim", "all"], default="all")
    p.add_argument("--member-only", action="store_true", default=True)
    p.add_argument("--all", dest="member_only", action="store_false", help="include channels you're not a member of")
    p.add_argument("--limit", type=int, default=0, help="0 = unlimited")

    p = sub.add_parser("read", help="recent messages in a channel/DM")
    p.add_argument("channel")
    p.add_argument("--since", default="24h")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--text", action="store_true")

    p = sub.add_parser("thread", help="fetch a thread")
    p.add_argument("channel")
    p.add_argument("thread_ts")
    p.add_argument("--text", action="store_true")

    p = sub.add_parser("search", help="search.messages")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--text", action="store_true")

    p = sub.add_parser("post", help="post as Justin")
    p.add_argument("channel")
    p.add_argument("text")
    p.add_argument("--thread", help="parent ts to reply in-thread")
    p.add_argument("--broadcast", action="store_true")

    p = sub.add_parser("react", help="add a reaction")
    p.add_argument("channel")
    p.add_argument("timestamp")
    p.add_argument("emoji")

    p = sub.add_parser("permalink", help="get permalink for a message")
    p.add_argument("channel")
    p.add_argument("timestamp")

    p = sub.add_parser("user", help="lookup user profile")
    p.add_argument("user_id")

    p = sub.add_parser("dm", help="DM a user by id or @name")
    p.add_argument("user")
    p.add_argument("text")

    args = ap.parse_args()

    # load .env if SLACK_USER_TOKEN not already set (e.g. cron without env)
    if not os.environ.get("SLACK_USER_TOKEN"):
        env_path = os.path.expanduser("~/.hermes/.env")
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SLACK_USER_TOKEN=") and "=" in line:
                        os.environ["SLACK_USER_TOKEN"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

    client = get_client()
    dispatch = {
        "whoami": cmd_whoami,
        "channels": cmd_channels,
        "read": cmd_read,
        "thread": cmd_thread,
        "search": cmd_search,
        "post": cmd_post,
        "react": cmd_react,
        "permalink": cmd_permalink,
        "user": cmd_user,
        "dm": cmd_dm,
    }
    dispatch[args.cmd](args, client)


if __name__ == "__main__":
    main()
