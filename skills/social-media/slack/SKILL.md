---
name: slack
description: "Operate Justin's Slack on his behalf via user-token (xoxp-) API — read channels/DMs/threads, search messages, post as Justin, react. Workspace: SignLab. Single-workspace today; designed to multi-tenant later."
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [slack, signlab, messaging, second-brain]
    related_skills: [obsidian, google-workspace]
---

# Slack (SignLab workspace, user-token mode)

## ⚠️ READ FIRST — operating posture

This Slack access is **user-token** (`xoxp-`), not a bot. That means:

- **Anything you post appears as Justin himself**, not as "Bes". There is no
  visible distinction in Slack between "Justin typed this on his phone" and
  "Bes posted this via the API on Justin's behalf." Co-workers will react
  to your posts as if Justin wrote them.
- You can read every channel, DM, and group DM Justin can read. That
  includes potentially sensitive conversations. Treat what you see as you
  would treat reading Justin's email: extract what's useful, don't quote
  verbatim to third parties.
- **Default to read-only operations.** Posting and reacting are allowed
  but require either (a) Justin explicitly asking ("post X in #foo") or
  (b) a cron/skill flow that Justin has previously approved.
- **Never post in a public channel without confirming with Justin first**
  unless the post is in a channel he's explicitly designated for
  automation (none today).

## Workspace

- **SignLab** (only workspace today)
- Auth: env var `SLACK_USER_TOKEN` (starts with `xoxp-`)
- App name in Slack: "Bes" (or similar) — Justin owns it
- Scopes installed: channels/groups/im/mpim history+read, users:read,
  search:read, files:read, reactions:read, chat:write, reactions:write

If a write op 403s with `missing_scope`, the response includes the needed
scope. Tell Justin which scope is missing rather than guessing.

## The wrapper: `slack` CLI

There is a thin Python wrapper at `scripts/slack.py` (installed onto PATH
as `slack`). Call it via the standard pattern:

```bash
~/.hermes/hermes-agent/venv/bin/python \
  ~/.hermes/skills/social-media/slack/scripts/slack.py <subcommand> [args]
```

All subcommands print JSON to stdout by default (parseable). Use `--text`
for human-readable rendering of message lists.

### Subcommands

#### `whoami`
Returns the authed user's identity. Sanity-check the token works:
```bash
slack whoami
# {"user_id": "U01ABC...", "team_id": "T01...", "team": "SignLab", "user": "justin"}
```

#### `channels [--type public|private|im|mpim|all] [--member-only] [--limit N]`
List channels. Default: `--type all --member-only` (only conversations
Justin is in — usually what you want).
```bash
slack channels --type public --member-only
# [{"id": "C01...", "name": "general", "is_member": true, "is_private": false, "num_members": 42}, ...]
```

Use `--type im` to list DMs, `--type mpim` for group DMs. IM entries
include `user` (the other person's user ID).

#### `read <channel_id> [--since 24h|2d|2025-05-15] [--limit N] [--text]`
Fetch recent messages from a channel/DM/thread. Resolves user IDs to
display names automatically.
```bash
slack read C0123456789 --since 24h --text
# 2026-05-20 09:14  alice: heads up, the deploy is rolling
# 2026-05-20 09:16  bob:   ack
```

`--since` accepts: `Nh` / `Nd` / `Nw` (relative) or `YYYY-MM-DD` (absolute,
midnight UTC). Default: `24h`.

JSON mode (no `--text`) returns each message with `ts`, `user`, `user_name`,
`text`, `thread_ts`, `reply_count`, `reactions`.

#### `thread <channel_id> <thread_ts> [--text]`
Fetch a full thread (parent + all replies).
```bash
slack thread C0123 1716200000.123456 --text
```

#### `search <query> [--limit N] [--text]`
Use Slack's `search.messages` endpoint. Supports Slack search modifiers:
`from:@alice`, `in:#general`, `before:2025-05-01`, `after:`, `has::eyes:`,
`-from:@bot`, quoted phrases, etc.
```bash
slack search 'in:#engineering deploy after:2025-05-15' --limit 20
```

JSON mode returns hits with `permalink` (so you can cite back to Justin in
Telegram).

#### `post <channel_id> <text> [--thread <ts>] [--broadcast]`
Post a message. **Posts as Justin.** Confirm with Justin first unless the
ask is explicit.
```bash
slack post C0123 "Will follow up after the 2pm."
slack post C0123 "ack" --thread 1716200000.123456
```

`--broadcast` (only with `--thread`): also surface the thread reply to the
main channel ("Also send to channel" in the Slack UI).

Returns `{"ok": true, "ts": "1716200099.123", "channel": "C0123",
"permalink": "https://signlab.slack.com/archives/C0123/p17162..."}`.

#### `react <channel_id> <message_ts> <emoji>`
Add a reaction. `emoji` without colons (`thumbsup`, not `:thumbsup:`).
```bash
slack react C0123 1716200000.123456 eyes
```

#### `permalink <channel_id> <message_ts>`
Get a permalink for citation. Often the most useful op when answering
Justin: cite the source.

#### `user <user_id>`
Resolve a user ID to profile info (name, real_name, email if available,
title, status). Cached for the duration of the process.

#### `dm <user_id_or_name> <text>`
Convenience: opens (or finds) a DM with the user and posts. `user_id_or_name`
accepts either `U01ABC...` or `@alice` (resolved via users.list).

### Common recipes

**"Extract Brain Notes from Slack (`🧠` Emoji)"**
If Justin reacts to a message with the `🧠` (brain) emoji, use `scripts/fetch_slack_brains.py` to fetch the message and its surrounding context.
1. List all new reacted messages:
   ```bash
   python3 ${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/fetch_slack_brains.py --list-new
   ```
2. For each new item:
   - Generate a summarized Slack log in `Inputs/Slack/YYYY-MM-DD-slug.md`.
   - Do NOT append to the daily note (as the Notepad section is retired).
   - Mark the item as processed so it is never duplicated:
     ```bash
     python3 ${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/fetch_slack_brains.py --mark-processed <channel_id> <ts>
     ```

**"What did I miss in #foo today?"**
1. `slack channels --type public --member-only` to find the channel ID.
2. `slack read <id> --since 24h --text`.
3. Summarize for Justin in Telegram. If you cite specific messages, include
   the permalink so he can jump.

**"Did anyone @ me?"**
1. `slack search '@<justin_user_id>' --limit 30`. Or, more reliably:
2. Iterate Justin's member-channels, fetch recent messages, filter for
   `<@U_justin>` in text. The search endpoint sometimes misses mentions in
   private channels depending on indexing.

**"What do I have reminders set on?"**
Use `is:saved` (to find starred/saved messages) and `has:reminder` (as a fallback) in a search query — this is the supported workaround for the missing `reminders:read` scope (see Pitfalls). It returns messages Justin has saved or flagged with Slack's native reminder feature:
```bash
slack search '(has:reminder OR is:saved) after:2026-05-19' --limit 50
```
Note: the literal word "reminder" appearing in message *text* can occasionally bleed in via `has:reminder` (e.g. "Reminder: meeting at 3pm"). Use channel context to distinguish these from genuinely reminder-flagged or saved messages.

**"Reply to Alice's DM"**
1. `slack channels --type im` to find the DM channel ID for Alice's user_id.
2. `slack read <dm_id> --since 24h --text` to read context.
3. Confirm content with Justin in Telegram (paraphrase his ask).
4. `slack post <dm_id> "<message>"`.

### Find the discussion about $TOPIC
1. `slack search '$TOPIC' --limit 20`.
2. Pick the relevant thread, grab `channel` and `thread_ts` (use `ts` if no
   thread_ts).
3. `slack thread <channel> <thread_ts> --text` for full context.

## The Brain Note-Taking System (🧠)

You can capture high-quality conversation logs directly from Slack into the Obsidian vault under `Inputs/Slack/` using the emoji `🧠` or via interactive prompts in the **Morning Briefing**.

### 1. Automated Log Capture (via `🧠` reaction)
When Justin adds a `🧠` reaction to a message:
- A cron job (`Slack Brain Note Capture`) runs every 2 hours using the `fetch_slack_brains.py` helper.
- If Justin (user ID `U095LHMC4UW`) reacted with `🧠`, the script fetches the entire thread (if part of one) or an 11-message context window surrounding the message.
- It synthesizes a Markdown log inside `/home/justin.guest/Developer/obsidian-vault/Inputs/Slack/YYYY-MM-DD-slug.md` with participants, a summary of who said what, and key decisions/takeaways. Do NOT include verbatim Slack messages; store only summaries with retrieval metadata.
- It does NOT append to today's daily note (as the Notepad section is retired).
- It marks the thread processed inside `~/.hermes/processed_slack_brains.json`.

### 2. Manual Candidate Suggestions (Morning Briefing Phase 5)
If a conversation wasn't explicitly tagged, the Morning Briefing live-scans active Slack threads from the last 36 hours for note-worthy discussions:
- Runs `python3 ~/.hermes/scripts/fetch_slack_brains.py --list-candidates`.
- **Candidate filters:** Requires `>= 3` messages, `>= 2` unique human participants, Justin's active participation or mention, and **no existing `🧠` reaction** (to avoid double-processing).
- Prompts Justin with numbered candidates. If approved, it synthesizes the log, saves it as an input, and marks it processed (without updating the daily note).

### 3. Managing the System Helper
The background script lives at:
- `~/.hermes/scripts/fetch_slack_brains.py`
Its database of processed threads is at:
- `~/.hermes/processed_slack_brains.json`

To manually mark a thread as processed (for testing or debugging):
```bash
python3 ~/.hermes/scripts/fetch_slack_brains.py --mark-processed <channel_id> <parent_ts>
```

## Pitfalls
Justin uses a `🧠` (brain) emoji to flag Slack conversations that should be preserved in his vault as logs under `Inputs/Slack/`.

There is a dedicated cron job ("Slack Brain Note Capture") running every 2 hours that automates this workflow:
1. Runs `fetch_slack_brains.py` to fetch messages where Justin (`U095LHMC4UW`) added a `🧠` reaction.
2. Checks against the processed cache at `~/.hermes/processed_slack_brains.json`.
3. If new, retrieves the full conversation context (full thread replies if it's a thread; or a chronological 11-message context window around the reacted message if it's not).
4. Summarizes the discussion via the agent and writes it to `/home/justin.guest/Developer/obsidian-vault/Inputs/Slack/YYYY-MM-DD-slug.md`. Do NOT include verbatim Slack messages; store only summaries with retrieval metadata.
5. Marks the message as processed using `python3 fetch_slack_brains.py --mark-processed <channel_id> <ts>`. (Does NOT append to the daily note notepad, as that section is retired).

To run the fetcher script manually to list new reactions:
```bash
python3 ~/.hermes/scripts/fetch_slack_brains.py
```

## Pitfalls

1. **Permalinks for users not in the channel resolve to a 404 in Slack.**
   If you cite a permalink from #private-channel to a Slack viewer not in
   that channel, they'll see "Channel not found." For Justin himself this
   is fine — he can see anything he can read. Watch out if you ever
   summarize for someone else.

2. **`search.messages` excludes some recently-edited or recently-posted
   messages** due to Slack's search index lag (~minutes). For "right now"
   queries on a specific channel, use `read --since 1h` instead of search.

3. **Thread `ts` vs message `ts`**. A reply has its own `ts` AND a
   `thread_ts` pointing to the parent. To reply IN a thread, you pass the
   parent's `ts` (which IS the thread_ts). To react TO a specific reply,
   you pass the reply's own `ts`. Read both fields from JSON output before
   choosing which one to pass downstream.

4. **Direct messages are channels too** — their IDs start with `D`. The
   `channels:history` scope does NOT cover DMs; `im:history` does. If a
   `read` against a `D...` ID returns `missing_scope`, the token wasn't
   installed with `im:history`.

5. **Posting in a channel you're not a member of fails by default** even
   with `chat:write`. You'd need `chat:write.public` (deliberately not
   granted). For now: `slack channels --member-only` to see where posting
   will work.

6. **Display name vs username vs real name.** `user.name` is the legacy
   username (often the email prefix); `user.profile.display_name` is what
   appears in the UI; `user.profile.real_name` is the full name. The
   wrapper prefers `display_name` > `real_name` > `name` when rendering.

7. **Rate limits**. User tokens are on Tier 2-3 rate limits (~20-50
   requests/minute depending on method). For "scan everything Justin is
   in", batch and add a small `time.sleep(1)` between channel reads.

8. **`reminders:read` scope is not installed.** Calling `reminders.list`
   via the Slack SDK will fail with `missing_scope`. The installed token
   does not have this scope. Use `is:saved` (for saved/starred messages) and `has:reminder` in a search query as a
   workaround (see "What do I have reminders set on?" in Common recipes).
   To get the real scope, Justin would need to re-authorize the Slack app
   with `reminders:read` added.

## Adding a second workspace later

When/if Justin adds Nous Research or another workspace, the design path is:
1. Create a second Slack app in that workspace, get a second `xoxp-` token.
2. Add `SLACK_USER_TOKEN_NOUS=xoxp-...` to `.env` (one env var per
   workspace, distinguished by suffix).
3. Patch `scripts/slack.py` to accept `--workspace signlab|nous` and route
   to the corresponding env var. Default workspace = SignLab.
4. Update this SKILL.md with the workspace list.

Pattern mirrors `gws_multi.py` in the google-workspace skill.

## Where things live

- **Token**: `~/.hermes/.env` → `SLACK_USER_TOKEN`
- **Wrapper script**: `~/.hermes/skills/social-media/slack/scripts/slack.py`
- **Reaction note capture script**: `~/.hermes/scripts/fetch_slack_brains.py`
- **Reaction note processed cache**: `~/.hermes/processed_slack_brains.json`
- **Convenience symlink** (optional): `~/.local/bin/slack` → wrapper
- **Python deps**: `slack_sdk` installed in `~/.hermes/hermes-agent/venv`
- **Workspace home**: signlab.slack.com
