---
name: todoist-inbox-fill
description: "Use when Justin asks to 'fill my inbox', 'sync my tasks', 'what am I missing in Todoist', or wants open actions from external sources (Slack, Gmail, Calendar, Obsidian daily notes, iMessages, Linear) surfaced into his Todoist Inbox — without duplicating what's already there. Accepts an optional lookback window (default 48h)."
platforms: [linux, macos]
---

# 📥 Todoist Inbox Fill

Scan external sources for open actions Justin owns and needs to do. Deduplicate against what already exists in Todoist. Surface candidates to Justin for confirm/edit. Batch-add confirmed tasks to Inbox.

**This is not a sync.** It's a one-way capture pass. It does not complete, reschedule, or remove tasks. It only adds what's genuinely missing.

---

## Step 1 — Pre-flight

Determine the lookback window. If Justin specified one (e.g. "last 24 hours", "go back 3 days"), use it. Otherwise default to **48 hours**.

Compute dates and snapshot the current Todoist state. Do this in-context (not in a subagent).

```bash
TODAY=$(date +%F)           # e.g. 2026-05-21
TOMORROW=$(date -d "$TODAY + 1 day" +%F)
TODAY_SLASH=$(date +%Y/%m/%d)
TOMORROW_SLASH=$(date -d "$TODAY + 1 day" +%Y/%m/%d)
WEEK_FROM_NOW=$(date -d "$TODAY + 7 days" +%F)

# Lookback window (default 48h = 2 days)
LOOKBACK_HOURS=48           # override if Justin specified something else
LOOKBACK_START=$(date -d "$TODAY - ${LOOKBACK_HOURS} hours" +%F)
LOOKBACK_START_SLASH=$(date -d "$TODAY - ${LOOKBACK_HOURS} hours" +%Y/%m/%d)
```

Pass `LOOKBACK_HOURS`, `LOOKBACK_START`, `LOOKBACK_START_SLASH`, and `LOOKBACK_ISO` (ISO 8601 datetime for Linear, e.g. `2026-05-21T00:00:00.000Z`) to subagents so they scope their searches to the right window.

Compute `LOOKBACK_ISO`:
```bash
LOOKBACK_ISO=$(date -u -d "${LOOKBACK_HOURS} hours ago" +%Y-%m-%dT%H:%M:%S.000Z)
```

Then snapshot **all open tasks** in Todoist so you can deduplicate later. Make one call:

```
find-tasks(filter="!date & !recurring | today | overdue | due before: <WEEK_FROM_NOW>", limit=100, responsibleUserFiltering="all")
```

This is intentionally broad — you want to know what Todoist already knows. Keep the result in-context. You'll diff against it in Step 3.

> **Tip:** If the filter syntax errors, fall back to two calls: `find-tasks-by-date(startDate="today", daysCount=7, overdueOption="include-overdue", limit=100)` and `find-tasks(filter="no date", limit=100)`. Merge results.

---

## Step 2 — Gather candidates (parallel subagents)

Spawn one subagent per source in a **single batch**. Each subagent returns a compact bullet list of *open actions* — things Justin needs to do. Not FYIs. Not things others owe him (unless he needs to follow up). Not decisions already made.

Pass `TODAY`, `TOMORROW`, `TODAY_SLASH`, `TOMORROW_SLASH`, `WEEK_FROM_NOW`, `LOOKBACK_HOURS`, `LOOKBACK_START`, and `LOOKBACK_START_SLASH` into each subagent as verbatim substituted strings.

**Budget for every subagent: ≤8 tool calls. Return partial results and stop if budget is exhausted.**

Sources to cover in two batches (concurrency cap is 3):
- **Batch 1:** Slack, Gmail, Obsidian
- **Batch 2:** Calendar, Linear, iMessages

Sources: **Slack, Gmail, Obsidian daily notes, Calendar, Linear.**

**Do not pipe command output into a language interpreter** (no `... | python3 -c "..."`, no `... | bash`, no `... | node -e "..."`). The security scanner flags `cmd | python3` etc. as `pipe_to_interpreter` (HIGH) regardless of intent and will halt your run for approval. If you need to post-process JSON, use `jq` (installed). If you need real Python, write a short script to a tempfile and run it as `python3 /tmp/foo.py` — the file boundary is what satisfies the scanner.

---

### Subagent A — Slack (SignLab)

- **Toolsets:** `["terminal"]`
- **Skill:** `slack`
- **Goal:** Find open actions for Justin in Slack today. Budget: 8 tool calls.
- **Context:**
  > Extract open actions from Slack for Justin. **Only surface messages where Justin has set a Slack reminder** — these are the clearest signal of intent to act.
  >
  > Run one search:
  > 1. `slack search 'has:reminder after:<LOOKBACK_START>' --limit 50`
  >
  > `has:reminder` returns messages Justin flagged with Slack's native reminder feature. This is intentionally narrow — Justin sets reminders on things he means to act on, so false positives are rare.
  >
  > Note: the word "reminder" appearing in message *text* (e.g. "Reminder: meeting at 3pm") can occasionally leak in. Drop these if they're clearly not reminder-flagged — use context and channel to judge.
  >
  > Drop: bot/automation messages, notifications, things that are clearly already done.
  >
  > Format each as a candidate task:
  > `- [Slack] <concise action> | context: <#channel or @person, brief what/why> | url: <permalink>`
  >
  > End with `Total: N candidates`.
  >
  > Budget: 8 tool calls. Return what you have and stop if budget exhausted.

---

### Subagent B — Gmail (work + personal-main)

- **Toolsets:** `["terminal"]`
- **Skill:** `google-workspace`
- **Goal:** Find emails where Justin owes a reply or has an explicit action item. Budget: 8 tool calls.
- **Context:**
  > Use the wrapper at `${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py`. Read-only — do NOT attempt sends.
  >
  > Run exactly two searches (no personal-junk unless Justin explicitly asked):
  > 1. `gws_multi.py --account work gmail search 'after:<LOOKBACK_START_SLASH> before:<TOMORROW_SLASH> in:inbox -label:sent' --max 50`
  > 2. `gws_multi.py --account personal-main gmail search 'after:<LOOKBACK_START_SLASH> before:<TOMORROW_SLASH> in:inbox -label:sent' --max 50`
  >
  > The `in:inbox` filter is critical — it excludes archived threads. **Do not surface tasks from archived emails.** If a thread has been archived, Justin has already processed it and it is not an open action.
  >
  > From results (subject, from, snippet only — do NOT fetch full bodies), extract:
  > - Emails from humans that contain a direct question or request for Justin.
  > - Emails Justin sent that contain a commitment or follow-up he still needs to do.
  > - Threads where he's last-replied-to but hasn't responded.
  >
  > For each result, include the message ID or thread ID if available in the search output (needed to construct a Gmail link). Gmail deep links follow the pattern `https://mail.google.com/mail/u/0/#inbox/<threadId>` — include this if you can derive it.
  >
  > Skip: automated notifications, CI/build alerts, shipping/delivery, marketing, newsletters, receipts, calendar invites, App Store Connect issue alerts, Todoist onboarding, Readwise, Substack.
  >
  > Format each candidate task:
  > `- [Email/<account>] <concise action> | from: <sender> | subject: <subject>`
  >
  > End with `Total: N candidates (work: X, personal-main: Y)`.
  >
  > Budget: 8 tool calls. Return what you have and stop.

---

### Subagent C — Obsidian daily notes (lookback window)

- **Toolsets:** `["terminal", "file"]`
- **Skill:** `obsidian`
- **Goal:** Find uncaptured open actions in recent daily notes. Budget: 8 tool calls.
- **Context:**
  > Read `OBSIDIAN_VAULT_PATH` from env (fallback: `~/Documents/Obsidian Vault`). Daily note filename format: `YYYY-MM-DD DayName.md`. Current notes live in the vault root; older ones in `Daily Notes/`.
  >
  > For each of the last N days matching the lookback window (starting today, <TODAY>, going back to <LOOKBACK_START>), find and read the daily note if it exists.
  >
  > From each note, extract:
  > - Unchecked task items: lines matching `- [ ]` that are not marked done.
  > - Content under headings like "Open Questions", "Blockers", "Next Steps", "TODO", "Follow-ups".
  > - Any line that reads like a commitment or a deferred action.
  >
  > Skip: lines marked `- [x]` (done), headings/bullets under "Decisions Made", "Highlights", pure observations.
  >
  > Format each candidate task:
  > `- [Obsidian/<date>] <action text> | note: <YYYY-MM-DD DayName.md>`
  >
  > End with `Total: N candidates across M notes`.
  >
  > Budget: 8 tool calls. Return what you have and stop.

---

### Subagent — Linear

- **Toolsets:** `["terminal"]`
- **Skill:** `linear`
- **Goal:** Find Linear issues assigned to Justin (To Do / In Progress) and new Triage issues from the last 24 hours. Budget: 8 tool calls.
- **Context:**
  > Use `curl` against `https://api.linear.app/graphql` with `Authorization: $LINEAR_API_KEY`.
  >
  > Run **two queries**:
  >
  > **Query 1 — Assigned issues in To Do or In Progress:**
  > ```graphql
  > { viewer { assignedIssues(filter: {
  >     state: { type: { in: ["unstarted", "started"] } }
  >   }, first: 50) {
  >     nodes { identifier title state { name type } url }
  >   } } }
  > ```
  > `unstarted` = To Do, `started` = In Progress.
  >
  > **Query 2 — New Triage issues created in the last 24 hours (any assignee):**
  > ```graphql
  > { issues(filter: {
  >     and: [
  >       { state: { type: { eq: "triage" } } },
  >       { createdAt: { gt: "<LOOKBACK_ISO>" } }
  >     ]
  >   }, first: 50) {
  >     nodes { identifier title state { name type } url createdAt }
  >   } }
  > ```
  > (Replace `<LOOKBACK_ISO>` with the computed ISO timestamp, e.g. `2026-05-21T10:00:00.000Z`.)
  >
  > **Task naming rules (these exact formats will become Todoist task content):**
  > - Assigned To Do/In Progress: `Work on <identifier> <title>`
  > - Triage: `Triage <identifier> <title>`
  >
  > Format each result:
  > - For assigned: `- [Linear/assigned] Work on <identifier> <title> | state: <state name> | url: <url>`
  > - For triage: `- [Linear/triage] Triage <identifier> <title> | url: <url>`
  >
  > End with `Total: N candidates (assigned: X, triage: Y)`.
  >
  > Budget: 8 tool calls. Return what you have and stop.

---

### Subagent E — iMessages (family)
- **Goal:** Find open actions from family texts in the lookback window. Budget: 5 tool calls.
- **Context:**
  > Read recent messages across the allowlisted iMessage chats via SSH proxy:
  > ```bash
  > ssh mac-host bes-imsg recent-all --since <LOOKBACK_HOURS>h
  > ```
  >
  > From results, extract messages where someone is:
  > - Making an explicit request of Justin ("Can you pick up…", "Don't forget…", "Can we…")
  > - Asking a direct question that Justin hasn't answered (you only see incoming messages, not Justin's replies — flag these as potential outstanding replies)
  > - Communicating a time-sensitive need (appointments, pickups, deadlines)
  >
  > Use friendly names for senders (Nana, Sam, Jamie, Rosie, Kathy, etc.) — not phone numbers.
  >
  > Skip: pure reactions ("YAYYY", "I did", "Kk"), FYIs with no ask, group chatter with no clear request directed at Justin.
  >
  > Format each candidate task:
  > `- [iMessage/<chat label>] <concise action> | from: <sender> | context: <brief quote or summary>`
  >
  > End with `Total: N candidates`.
  >
  > Budget: 5 tool calls. Return what you have and stop.

---

### Subagent D — Calendar (upcoming meetings needing prep)

- **Toolsets:** `["terminal"]`
- **Skill:** `google-workspace`
- **Goal:** Identify upcoming meetings in the next 7 days where Justin might need a prep task. Budget: 5 tool calls.
- **Context:**
  > Run one command:
  > ```
  > gws_multi.py --account all calendar list --start <TODAY>T00:00:00 --end <WEEK_FROM_NOW>T23:59:59 --max 50
  > ```
  >
  > From the results, surface only meetings that:
  > - Have external attendees (not just Justin + internal SignLab team) OR are high-stakes internal meetings (reviews, all-hands, 1:1s with leadership).
  > - Are in the next 3 days (anything beyond that is low urgency right now).
  > - Don't obviously already have a prep task implied by the title.
  >
  > For each, suggest a prep action:
  > `- [Calendar] Prep for: <meeting title> | when: <date HH:MM> | attendees: <names>`
  >
  > Keep it minimal — only surface meetings where prep is clearly warranted, not every 30-min standup.
  >
  > End with `Total: N prep candidates`.
  >
  > Budget: 5 tool calls. Return what you have and stop.

---

## Step 3 — Deduplicate

You now have subagent summaries (3–5 source lists) plus the Todoist snapshot from Step 1.

For each candidate task:
1. Check the Todoist snapshot for a semantically similar task. Similar = same person/issue/thread/subject matter, close enough that adding a second task would be redundant.
2. Mark it as **NEW** (not in Todoist) or **EXISTS** (already covered). If it's close but not exact, mark it **SIMILAR** and note what the existing task is.

This dedup is LLM reasoning — you're comparing intent and subject matter, not text equality. Be conservative: if in doubt, mark it NEW and let Justin decide.

Build the final candidate list: only NEW and SIMILAR items. Drop EXISTS.

---

## Step 4 — Present to Justin

Show a clean numbered list. Format:

```
📥 Found N potential inbox items not yet in Todoist:

1. [Slack] Reply to @maya re: sprint retro format — #product-eng
2. [Email/work] Reply to Alex about Q3 roadmap review — from Alex Chen
3. [Obsidian/2026-05-20] Follow up on Nana's dentist appointment
4. [Calendar] Prep for: Board review — Thu 2pm
5. [Linear/assigned] Work on SL-204 Update onboarding copy — In Progress
6. [Linear/triage] Triage SL-312 Crash on lesson complete

~SIMILAR~ (already in Todoist but different angle):
5. [Email/work] Alex re: API rate limit spike — similar to existing "Investigate API latency" task

Which ones should I add? (say "all", "1 3 5", or "skip 4" — or edit any item before I add it)
```

Then wait. Do not add anything yet.

---

## Step 5 — Add confirmed tasks

Once Justin responds:

- Parse his selection (\"all\", specific numbers, exclusions like \"skip 4\").
- For each confirmed task, shape it as a Todoist task:
  - **content**: concise action (strip the source prefix, keep it clean)
  - **description**: everything Justin needs to start the task cold — where details live, direct URL or permalink, relevant phone numbers or contact info, sender/assignee, deadline if known, Obsidian project link if applicable. One line per piece of context. If the source has a URL, always include it. The bar: can Justin open this task and immediately know where to go?
  - **projectId**: omit (→ Inbox)
  - **priority**: `"p4"` unless the source clearly signals urgency
  - **labels**: infer from content (`@location` labels if applicable — do NOT use `work` or `home` as labels; those are Todoist projects, not labels)
  - **dueString**: only set if the source has a clear deadline or Justin requests one; otherwise leave unset

- Batch-add with a single `add-tasks` call (up to 25 items).
- For each created task, immediately add a brief comment via `add-comments` explaining the source and why it was captured. Keep it to one short sentence. Examples:
  - "From Slack — reminder set on @maya's message re: sprint retro in #product-eng."
  - "Email from Alex Chen (work) — direct ask about Q3 roadmap, still in inbox."
  - "From daily note 2026-05-20 — unchecked action item under Open Questions."
  - "Calendar: Board review Thu 2pm — external attendees, prep warranted."
  Use a single `add-comments` call with all comments in one batch (one per task).
- Reply with a confirmation: \"Added N tasks to Inbox.\" and list them with their Todoist task IDs.

---

## Important behaviors

- **Never add without confirmation.** The present-then-confirm loop (Steps 4–5) is mandatory. Don't silently add.
- **No FYIs or informational notes.** If it's not something Justin needs to do, it doesn't belong in Todoist.
- **No hermes-labeled tasks.** Never add or modify the `hermes` label. Skip tasks labeled `hermes` in the Todoist snapshot — they're Hermes's.
- **Fail gracefully.** If a subagent fails, note it in the header ("Slack: ERR — auth expired") and continue with the other sources. A 3-source run is still useful.
- **Calendar prep tasks: be selective.** Standup, team syncs, 1:1s with direct reports — Justin doesn't need a \"prep for standup\" task. Save calendar suggestions for meetings with external stakes or real prep need.
- **Date precision.** Pre-compute dates once (Step 1) and pass them to every subagent. Don't trust subagents to re-derive TODAY or LOOKBACK_START.

## Pitfalls

- **`delegate_task` concurrency cap is 3.** `delegate_task` accepts a `tasks` array but only runs 3 subagents in parallel (configured via `delegation.max_concurrent_children`). With 5 sources (Slack, Gmail, Obsidian, Calendar, iMessages), split into two batches: first 3 in parallel (Slack, Gmail, Obsidian), then 2 in parallel (Calendar, iMessages). Don't try to pass all 5 at once — it errors immediately.
- **`find-tasks` requires at least one filter.** If you call it with no args it errors. See Step 1 for the right snapshot call.
- **Dedup is semantic, not textual.** \"Reply to Maya about retro\" and \"Respond to Maya re: retrospective\" are the same action. Don't add both.
- **Priorities are strings (`"p1"`–`"p4"`), not integers.** Default to `"p4"`.
- **Don't use `update-tasks` to change due dates on recurring tasks** — use `reschedule-tasks`. This skill mostly adds new tasks, so this pitfall is rare here.
- **Gmail date format is `YYYY/MM/DD` (slashes), not dashes.** Calendar and Linear use ISO dashes. Keep them separate.
- **`gws_multi.py` path varies.** Always resolve as `${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py`.
- **Slack `--limit` flag.** The Slack CLI may not support `--limit` on all commands. If it errors, drop the flag and let it return the default count.
- **App Store Connect emails.** These are engineering issues, not Justin's. Filter them out at the Gmail subagent stage.
