---
name: work-log
description: Use when Justin asks to "create a work log", "log today's work", "write a work log", or otherwise wants today's work activity summarized and appended to today's daily note in the Obsidian vault. Pulls from Slack (SignLab), Linear, Gmail (work + personal-main; personal-junk only on request), Google Calendar (all 3 accounts), Todoist (completed + due-today tasks), plus the daily note and any chat brain-dump.
platforms: [linux, macos]
---

# 📋 Work Log

Summarize today's work activity and append a structured Work Log block to **today's daily note** in the Obsidian vault. Do NOT create a separate file.

The block has three sections — **Highlights / Decisions / Open Questions** — synthesized across all sources. New sources do not get their own headings; they feed the synthesis. The footer enumerates which sources were actually pulled and rough counts.

## TARGET_DATE override (for cron / morning briefing)

By default this skill logs **today**. When called from the morning briefing cron, a `TARGET_DATE` (YYYY-MM-DD) is passed in the prompt context — use that date instead of today everywhere `TODAY` / `TOMORROW` / "today's daily note" appear.

**How to detect:** the calling prompt will include a line like `TARGET_DATE: 2026-05-21` near the top. If present, substitute it for `TODAY` in every step below. The daily note you find, read, and append to is the *TARGET_DATE* note, not today's.

If no `TARGET_DATE` is present, default to today as usual. When run from cron (no interactive user), if the target daily note doesn't exist, log the error and exit gracefully — do not halt the whole briefing.

## Step 1 — Resolve vault path

Read `OBSIDIAN_VAULT_PATH` from env (typically `/home/justin.guest/vault` inside `bes-vm`). Do not hard-code. If unset, fall back to `~/Documents/Obsidian Vault`. See the `obsidian` skill for full path-handling conventions.

## Step 2 — Find the target daily note

Daily-note filename format: `YYYY-MM-DD DayName.md` (e.g. `2026-05-20 Wednesday.md`).

Justin's vault convention: **current** daily notes live in the vault root; **archived** daily notes live in `Daily Notes/`. Check the root first:

1. `<vault>/<TARGET_DATE DayName>.md` — primary
2. `<vault>/Daily Notes/<TARGET_DATE DayName>.md` — fallback

Use `search_files` with `target: "files"` to locate. If neither exists, tell Justin "The daily note for TARGET_DATE doesn't exist yet." and stop (when run from cron, log the error to the briefing cache and continue).

## Step 3 — Gather raw material (parallel, one subagent per source)

Spawn **one `delegate_task` subagent per external source** in a single batch so raw API output stays out of your context. Each subagent runs a **specific, pre-canned set of commands** — no exploration — and returns a small filtered summary (bullets, ~10–30 items max). You only see the summaries.

**Direct execution option (Fast-track):** Spawning 5 parallel subagents may hit the max concurrent children limit of 3. If you can, you can execute the commands directly in-context via `terminal()` and the native MCP tools (especially for Todoist). This bypasses subagent overhead, completes in seconds, and is extremely clean when parsed directly by the main agent.

**Speed discipline:** subagents have a soft budget of **≤8 tool calls each**. If a subagent can't finish inside that, it must return what it has and exit. Tell it so explicitly in the context block ("Budget: 8 tool calls. If you exhaust it, return partial results and stop.").

The target date (TARGET_DATE) is the cutoff for every source. Pre-compute it once and pass it to each subagent verbatim — don't let subagents re-derive it. Also pre-compute Justin's Linear user-id once (see *Pre-flight*, below) and pass it too.

### Pre-flight (do once, in-context, before spawning subagents)

```bash
# Use TARGET_DATE if passed in from cron context; otherwise default to today
TODAY=${TARGET_DATE:-$(date +%F)}       # e.g. 2026-05-20
TOMORROW=$(date -d "$TODAY + 1 day" +%F) # e.g. 2026-05-21
TODAY_SLASH=$(date +%Y/%m/%d)            # Gmail wants slashes
TOMORROW_SLASH=$(date -d "$TODAY + 1 day" +%Y/%m/%d)
```

Justin's Linear user-id can be cached. First time, look it up with `{ viewer { id name } }`. After that, store it as `LINEAR_USER_ID` in `~/.hermes/.env` (or wherever Bes keeps env vars) so future runs skip the lookup. If unknown at runtime, the Linear subagent will resolve it itself — but that costs one extra round-trip.

### Subagent A — Slack (SignLab)

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `slack`
- **Goal:** `"Run two specific slack searches for <TODAY> and format the results. Budget: 8 tool calls."`
- **Context to pass (verbatim, with TODAY substituted):**
  > Run exactly these two commands (no exploration, no `slack channels`, no `slack read`):
  >
  > 1. `python3 ${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/slack.py search 'from:@justin after:<TODAY>' --limit 50` — messages Justin sent today.
  > 2. `python3 ${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/slack.py search 'to:@justin after:<TODAY>' --limit 50` — DMs / @-mentions / threads addressed to him today.
  >
  > Dedupe by permalink. Drop bot/integration messages (Zapier, GitHub bots, deploy bots) unless they have a human reaction. Drop pure social chatter Justin wasn't part of.
  >
  > Return a bullet list grouped by channel/DM, each bullet: `[#channel | @person] one-line gist (permalink)`. End with `Total: N messages across M channels/DMs.`
  >
  > Budget: 8 tool calls. If you exhaust it, return what you have and stop.

### Subagent B — Linear

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `linear`
- **Goal:** `"Run one GraphQL query for <TODAY>'s Linear activity. Budget: 8 tool calls."`
- **Context to pass (verbatim, with TODAY/TOMORROW and LINEAR_USER_ID substituted):**
  > Justin's Linear user-id is `<LINEAR_USER_ID>` (if blank, resolve once via `{ viewer { id } }` and cache to `~/.hermes/.env` as `LINEAR_USER_ID`).
  >
  > Run **one** GraphQL query that ORs assignee+creator+subscriber filters with `updatedAt` in `[<TODAY>T00:00:00Z, <TOMORROW>T00:00:00Z)`:
  >
  > ```graphql
  > { issues(filter: {
  >     and: [
  >       { updatedAt: { gte: "<TODAY>T00:00:00.000Z", lt: "<TOMORROW>T00:00:00.000Z" } },
  >       { or: [
  >         { assignee: { id: { eq: "<LINEAR_USER_ID>" } } },
  >         { creator:  { id: { eq: "<LINEAR_USER_ID>" } } },
  >         { subscribers: { id: { eq: "<LINEAR_USER_ID>" } } }
  >       ] }
  >     ]
  >   }, first: 50) {
  >     nodes { identifier title state { name type } updatedAt assignee { name } creator { name } team { key } url
  >             comments(filter: { createdAt: { gte: "<TODAY>T00:00:00.000Z" } }) { nodes { body user { name } } } }
  >   } }
  > ```
  >
  > Format as bullets like `[TEAM-123 | status] Title — what changed today (state change / comment / created).` End with `Total: N issues touched.`
  >
  > Budget: 8 tool calls. If you exhaust it, return what you have and stop.

### Subagent C — Email (work + personal-main only by default)

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `google-workspace`
- **Goal:** `"Search Gmail for <TODAY> across work + personal-main only. Budget: 8 tool calls."`
- **Context to pass (verbatim, with TODAY_SLASH/TOMORROW_SLASH substituted):**
  > Use the wrapper at `${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py`. Bes's gws token is **read-only** — do not attempt sends.
  >
  > Run **exactly two** searches (do NOT include personal-junk unless Justin explicitly asked for it — see "personal-junk opt-in" below):
  >
  > 1. `gws_multi.py --account work gmail search 'after:<TODAY_SLASH> before:<TOMORROW_SLASH>' --max 50`
  > 2. `gws_multi.py --account personal-main gmail search 'after:<TODAY_SLASH> before:<TOMORROW_SLASH>' --max 50`
  >
  > Use the search results' subject/snippet/from fields — do NOT call `gmail get` per message (too slow). If a thread looks ambiguous from snippet alone, mention it briefly rather than fetching the full body.
  >
  > Filter per account:
  > - **work**: drop pure CI/build notifications, calendar invites that already show in Calendar, automated reports unless Justin replied. Keep human-to-human threads and anything he sent.
  > - **personal-main**: keep only items that touch work, scheduling, or operator-of-his-life decisions. Drop newsletters, receipts, marketing.
  >
  > Return bullets grouped by account: `[account | from→to] one-line gist`. End with `Total: N relevant threads (work: X, personal-main: Y).`
  >
  > Budget: 8 tool calls. If you exhaust it, return what you have and stop.

**personal-junk opt-in:** the third Gmail account (`personal-junk`) is the newsletter/marketing inbox. Skip it by default. Only include a Subagent C2 (identical shape, `--account personal-junk`, even harsher filters: surface only if a real human DM-style email slipped in) if Justin says something like *"include personal-junk"* / *"check junk too"* when asking for the work log.

### Subagent D — Calendar (all 3 Google accounts via gws_multi)

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `google-workspace`
- **Goal:** `"List today's calendar events across all 3 accounts in one call. Budget: 5 tool calls."`
- **Context to pass (verbatim, with TODAY substituted):**
  > Run **one** command:
  >
  > ```
  > gws_multi.py --account all calendar list --start <TODAY>T00:00:00 --end <TOMORROW>T00:00:00 --max 50
  > ```
  >
  > Output chronological bullets: `HH:MM–HH:MM [account] Title — attendees (if any) — location/link (if any).` Flag each event as happened / cancelled-or-declined / upcoming-later-today based on the current time. End with `Total: N events.`
  >
  > Budget: 5 tool calls. If you exhaust it, return what you have and stop.

### Subagent E — Todoist

- **Toolsets:** `[]` (uses built-in MCP todoist tools)
- **Goal:** `"Pull today's Todoist activity for the work log. Budget: 8 tool calls."`
- **Context to pass (verbatim, with TODAY substituted):**
  > Use the Todoist MCP tools. Retrieve two things:
  >
  > 1. **Completed today:** call `mcp_todoist_find_completed_tasks` with `since: <TODAY>`, `until: <TODAY>`, `getBy: "completion"`, `responsibleUser: "me"`. Return all completed tasks.
  > 2. **Due today (incomplete):** call `mcp_todoist_find_tasks_by_date` with `startDate: <TODAY>`, `overdueOption: "exclude-overdue"`, `responsibleUserFiltering: "unassignedOrMe"`, `limit: 50`. Return tasks not yet completed.
  >
  > Format:
  > - Completed: bullets like `✓ [Project] Task name`
  > - Due/incomplete: bullets like `○ [Project] Task name`
  >
  > End with `Total: N completed, M still open today.`
  >
  > Budget: 8 tool calls. If you exhaust it, return what you have and stop.

**What this feeds:** completed tasks → "Today's Highlights"; incomplete due-today tasks → "Open Questions / Blockers."

### Subagent F (optional) — recent git activity

Skip unless Justin specifically mentions code work. If you do run it: scope to repos under `~/clio-backup`, `~/bes-backup`, `~/hermes-agent` (if present), and any project repo Justin mentioned in the daily note. Use `git log --author --since=midnight --pretty` per repo. Return commits as bullets `[repo] sha — subject`. Budget: 8 tool calls.

### After subagents return

You now have 3–5 small summaries. Also do these **in-context** reads/searches — they're cheap:

1. **Read today's daily note** with `read_file`. Scan for decisions, completions, blockers, links, meeting notes Justin wrote himself today.
2. **Scan for meeting/Granola notes:** Use `search_files` with `target: "files"` to look for files in the vault containing `<TARGET_DATE>` in their name (e.g. under `Granola/`). These notes (like Granola meeting summaries) often contain incredibly rich summaries of design discussions, product decisions, and future plans that won't show up in automated sources.
3. **Ask Justin in chat** what else he worked on that isn't in any source yet (skip if running in a non-interactive cron job). Short prompt: *"Anything from today not captured in Slack/Linear/email/calendar/daily-note? Side-quests, conversations IRL, decisions in your head?"* If he says "nothing," move on.

If a subagent fails (auth expired, network, hit budget, etc.), include the failure in the footer (`Slack: ERR — token expired` or `Linear: PARTIAL — hit budget`) rather than silently dropping the source. Then continue with what you have.

## Step 4 — Synthesize three sections

Produce a Work Log block with three section headings. Omit any section that has no real content (don't include an empty heading).

### `### Today's Highlights`
The most important things that happened — shipped work, key conversations, decisions reached, code written, problems solved. Pull from all sources. Be specific: name the people, channels, projects, outcomes. Past tense. 6–12 bullets typically; fewer is fine if it was a quiet day. Cite the source inline only when it adds clarity, e.g. *"Resolved blocker with Maya on render pipeline (#product-leads thread)."*

### `### Decisions Made`
Consequential decisions only. For each, bold the decision itself; include owner if not obvious. Skip if no real decisions were made — don't promote tasks or observations into "decisions." A Linear status change is not a decision; a Slack thread where a tradeoff was settled IS.

### `### Open Questions / Blockers`
Unresolved questions, pending actions, known blockers as of end-of-day. Includes asks Justin owes a reply to (from Slack/email), Linear issues stalled waiting on someone, calendar conflicts upcoming. Skip if none.

Writing style: concise, specific, past tense for highlights. Match the voice of prior work logs if Justin has any (grep for `## 💼 Work Log` in the daily-notes archive to find examples).

## Step 5 — Append to the daily note

Use `patch` (anchored append) or `write_file` (whole-note rewrite). Append this block at the **end** of the note, preserving everything above:

```
# 📋 Work Log

### Today's Highlights
[bullets]

### Decisions Made
[bullets]

### Open Questions / Blockers
[bullets]

---
*Sources: Slack (12 msgs / 4 channels) | Linear (5 issues) | Gmail work (8 threads), personal-main (1) | Calendar (4 events / 3 accts) | Todoist (N completed, M open) | daily note + chat.*
```

Use the **actual counts** from the subagent summaries. If a source was unavailable, mark it `ERR` with a short reason. Always include `daily note + chat` at the end.

Do NOT add a separate frontmatter block. Do NOT modify anything else in the file.

## Step 6 — Don't commit

Justin's `bes-vault-sync` watcher auto-commits and pushes the vault to `obsidian-vault` on GitHub within seconds of any write. Do NOT manually `git add` or `git commit` — it races the watcher and creates spurious commits.

## Important behaviors

- **No duplicate Work Log blocks.** If the daily note already contains `# 📋 Work Log`, **overwrite** it — replace everything from that heading to the end of the file with the newly synthesized block. Do NOT append a second one, and do NOT ask for confirmation when running autonomously (e.g. from a cron job). Only prompt Justin interactively if he is present in chat and the run was triggered manually.
- **Omit empty sections.** A Work Log with only Highlights is better than one with empty "Decisions Made" / "Open Questions" headings.
- **No file creation.** The only write operation is appending to the existing daily note.
- **Skip cleanup of the daily note.** Don't reformat or tidy what Justin already wrote — the Work Log block is additive.
- **Privacy posture.** Slack DMs and personal email can be sensitive. The subagent filter steps exist for a reason — keep the synthesis at the "what Justin did / decided / owes" level, not verbatim quotes. If something looks too private to land in a vault that auto-pushes to GitHub (even a private repo), ask Justin before including it.
- **Date precision.** "Today" means today in the vault's timezone, not UTC. Pre-compute the date once at Step 3 and pass it to every subagent. Don't trust subagents to re-derive it.
- **Source failures are non-fatal.** If Slack auth expired or Linear is down, log it in the footer and continue. A 3-source work log is still useful.

## Pitfalls

- **Slack channel names in Obsidian must be escaped.** A bare `#channel-name` in a note will be interpreted as an Obsidian tag. Always write `\#channel-name` (backslash prefix) so it renders as plain text.

- **`slack.py` and `gws_multi.py` paths vary by Hermes home.** Always resolve them using absolute paths referencing `${HERMES_HOME:-$HOME/.hermes}` (e.g. `${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/slack.py` and `${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py`) — do not hardcode `/home/justin.guest/...` and do not rely on bare `slack` in subagent `$PATH`.
- **Gmail date format is `YYYY/MM/DD` with slashes**, not dashes. Calendar event listings use ISO. Don't mix them up.
- **`slack` CLI defaults to read-only-ish use.** Never let a subagent post to a channel — the work-log gather is read-only by definition.
- **`slack` script path varies by environment.** Always run the Slack tool using `python3 ${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/slack.py search ...` to avoid `command not found` errors in subagent environments where standard PATH alias/configurations are not loaded.
- **Calendar "all-day events" can be timezone-shifted by one day** depending on how they were created. If something looks off-by-one, double-check the event's raw start/end before flagging it as a discrepancy.
- **Linear API key auth header has NO "Bearer" prefix** — see the linear skill if a subagent hits 401s.
- **Do NOT use custom python scripts to fetch Todoist data via direct REST API calls in subagents.** The sync v9 and REST v2 endpoints are deprecated (yielding HTTP 410 / 404). Subagent E must use the registered `mcp_todoist_*` tools directly. If a background script or custom tool must hit Todoist directly, use the correct current v1 path `https://api.todoist.com/api/v1/` and POST to `/api/v1/sync`.
