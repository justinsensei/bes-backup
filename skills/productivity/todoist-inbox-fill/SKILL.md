---
name: todoist-inbox-fill
description: "Use when Justin asks to 'fill my inbox', 'sync my tasks', 'what am I missing in Todoist', or wants open actions from external sources (Slack, Gmail, Calendar, Obsidian daily notes, Linear) surfaced into his Todoist Inbox — without duplicating what's already there. Also detects potential calendar events and surfaces them as Google Calendar event candidates to schedule directly on his behalf. Accepts an optional lookback window (default 48h)."
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

Then snapshot **all open tasks** in Todoist so you can deduplicate later. Call both:
1. `find-tasks-by-date(startDate="today", daysCount=7, overdueOption="include-overdue", limit=100)`
2. `find-tasks(filter="no date", limit=100)`

Merge results and keep them in-context. You'll diff against this snapshot in Step 3. This two-call method is robust and completely avoids HTTP 400 errors caused by complex Todoist search query syntax.

---

## Step 2 — Gather candidates (parallel subagents)

Spawn one subagent per source in a **single batch**. Each subagent returns a compact bullet list of *open actions* — things Justin needs to do. Not FYIs. Not things others owe him (unless he needs to follow up). Not decisions already made.

Pass `TODAY`, `TOMORROW`, `TODAY_SLASH`, `TOMORROW_SLASH`, `WEEK_FROM_NOW`, `LOOKBACK_HOURS`, `LOOKBACK_START`, and `LOOKBACK_START_SLASH` into each subagent as verbatim substituted strings.

**Budget for every subagent: ≤8 tool calls. Return partial results and stop if budget is exhausted.**

Sources to cover in two/three batches (concurrency cap is 3):
- **Batch 1:** Slack, Gmail, Obsidian daily notes
- **Batch 2:** Calendar, Linear, Granola meeting notes

Sources: **Slack, Gmail, Obsidian daily notes, Calendar, Linear, Granola.**

**Do not pipe command output into a language interpreter** (no `... | python3 -c "..."`, no `... | bash`, no `... | node -e "..."`). The security scanner flags `cmd | python3` etc. as `pipe_to_interpreter` (HIGH) regardless of intent and will halt your run for approval. If you need to post-process JSON, use `jq` (installed). If you need real Python, write a short script to a tempfile and run it as `python3 /tmp/foo.py` — the file boundary is what satisfies the scanner.

---

### Subagent A — Slack (SignLab)

- **Toolsets:** `["terminal"]`
- **Skill:** `slack`
- **Goal:** Find open actions for Justin in Slack today. Budget: 8 tool calls.
- **Context:**
  > Extract open actions from Slack for Justin. **Only surface messages where Justin has saved the message or set a Slack reminder** — these are the clearest signal of intent to act.
  >
  > Run one search:
  > 1. `python3 ${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/slack.py search '(has:reminder OR is:saved) after:<LOOKBACK_START>' --limit 50`
  >
  > `is:saved` matches messages Justin has explicitly added to his "Saved items" (formerly starred messages) list. `has:reminder` matches reminders. Together, these represent "saved Slack reminders/messages" Justin means to act on.
  >
  > Note: the word "reminder" appearing in message *text* (e.g. "Reminder: meeting at 3pm") can occasionally leak in via `has:reminder`. Drop these if they're clearly not reminder-flagged or saved — use context and channel to judge.
  >
  > **Command safety:** Do NOT pipe `slack.py` output into a language interpreter (`| python3 -c`, `| bash`, `| node -e`). The security scanner blocks these as `pipe_to_interpreter` (HIGH) and your run will halt for approval. If you need to inspect or reshape the JSON, use `jq`. Example:
  > ```bash
  > python3 ${HERMES_HOME:-$HOME/.hermes}/skills/social-media/slack/scripts/slack.py search '(has:reminder OR is:saved) after:<LOOKBACK_START>' --limit 50 \
  >   | jq -r '.[] | "\(.channel_name) | \(.username) | \(.permalink) | \(.text[:200])"'
  > ```
  >   | jq -r '.[] | "\\(.channel_name) | \\(.username) | \\(.permalink) | \\(.text[:200])"'
  > ```
  > For non-trivial Python, write to a tempfile and run as `python3 /tmp/foo.py` — the file boundary is what satisfies the scanner.
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
  > **Command safety:** Do NOT pipe `gws_multi.py` output into a language interpreter (`| python3 -c`, `| bash`, `| node -e`). The scanner blocks these. Use `jq` for JSON, or write a Python helper to `/tmp/foo.py` and run as `python3 /tmp/foo.py`.
  >
  > Format each candidate task:
  > `- [Email/<account>] <concise action> | from: <sender> | subject: <subject>`
  >
  > End with `Total: N candidates (work: X, personal-main: Y)`.
  >
  > Budget: 8 tool calls. Return what you have and stop.

---

### Subagent G — Granola meeting notes (Next Steps for Justin)

- **Toolsets:** `["terminal", "file"]`
- **Skill:** `obsidian`
- **Goal:** Find Next Steps assigned to Justin in recent Granola meeting notes. Budget: 8 tool calls.
- **Context:**
  > Vault path: resolve from env `OBSIDIAN_VAULT_PATH` (fallback: `~/Documents/Obsidian Vault`). Granola notes live under `<vault>/Granola/`, organized by month folders (`YYYY-MM/`). Each note filename starts with the meeting date (`YYYY-MM-DD`).
  >
  > Identify which month folders to search based on the lookback window (`<LOOKBACK_START>` to `<TODAY>`). Typically just the current month, but if the lookback crosses a month boundary, include both.
  >
  > For each `.md` file in the relevant folder(s) whose date prefix falls within the lookback window:
  > 1. Read the file.
  > 2. Find the `### Next Steps` section.
  > 3. Extract only lines that begin with `- Justin:` (case-insensitive). These are the action items assigned to Justin.
  > 4. Skip all other lines (other people's action items, bullets under other sections).
  >
  > **Command safety:** Use `search_files` and `read_file` from the file toolset — do NOT use `grep` piped to `python3 -c` or similar (scanner blocks `pipe_to_interpreter`). Use `jq` if reshaping JSON.
  >
  > Format each candidate task:
  > `- [Granola/<YYYY-MM-DD>] <action text (strip the "Justin: " prefix)> | meeting: <note title> | file: <relative path>`
  >
  > End with `Total: N candidates across M meeting notes`.
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
  > From each note, extract **only**:
  > - Unchecked task items: lines matching `- [ ]` that are not marked done.
  > - Lines containing explicit first-person commitment phrases: "I need to", "I need to remember", "I have to", "I should", "I must", "don't forget", "follow up on", "remind me".
  >
  > Do NOT infer tasks from section headings, bullet points under "Open Questions" or "Blockers", or general observations. Only literal `- [ ]` items and lines with the above explicit keywords qualify.
  >
  > Skip: `- [x]` lines, headings, pure notes, observations, decisions, highlights.
  >
  > **Command safety:** Use the `file` toolset and `search_files` to read notes — do NOT pipe shell output into `python3 -c` / `bash` / `node -e` (scanner blocks `pipe_to_interpreter`).
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
- **Goal:** Find Linear issues assigned to Justin (To Do / In Progress) and new Triage issues from within the lookback window. Budget: 8 tool calls.
- **Context:**
  > Use `curl` against `https://api.linear.app/graphql` with `Authorization: $LINEAR_API_KEY`.
  >
  > Run **two queries**:
  >
  > **Query 1 — Assigned issues in To Do, In Progress, or Monitoring:**
  > ```graphql
  > { viewer { assignedIssues(filter: {
  >     or: [
  >       { state: { type: { in: ["unstarted", "started"] } } },
  >       { state: { name: { eq: "Monitoring" } } }
  >     ]
  >   }, first: 50) {
  >     nodes { identifier title state { name type } url }
  >   } } }
  > ```
  > `unstarted` = To Do, `started` = In Progress, `Monitoring` = custom state (matched by name).
  >
  > **Query 2 — New Triage issues created within the lookback window (any assignee):**
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
  > - Assigned Monitoring: `Check in on <identifier> <title>`
  > - Triage: `Triage <identifier> <title>`
  >
  > **Command safety:** Parse the curl JSON response with `jq`, never with `| python3 -c` or `| node -e` (scanner blocks `pipe_to_interpreter`). Example:
  > ```bash
  > curl -s -H "Authorization: $LINEAR_API_KEY" -H "Content-Type: application/json" \\
  >   -d '{"query":"..."}' https://api.linear.app/graphql \\
  >   | jq -r '.data.viewer.assignedIssues.nodes[] | "\\(.identifier) | \\(.title) | \\(.state.name) | \\(.url)"'
  > ```
  >
  > Format each result:
  > - For assigned: `- [Linear/assigned] Work on <identifier> <title> | url: <url>`
  > - For triage: `- [Linear/triage] Triage <identifier> <title> | url: <url>`
  >
  > End with `Total: N candidates (assigned: X, triage: Y)`.
  >
  > Budget: 8 tool calls. Return what you have and stop.

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
  > **Command safety:** Use `jq` to filter/reshape `gws_multi.py` JSON output. Do not pipe to `python3 -c` / `bash` / `node -e`.
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

## Step 2b — Calendar event detection (separate pass)

This pass scans the same sources for *potential calendar events* — future commitments that aren't already on Justin's Google Calendar. Results are presented separately from general Todoist inbox candidates (see Step 4).

**What counts as a potential calendar event (cast wide):**
- Any specific future date + time mentioned in context (meetings, calls, appointments, deadlines with a time component)
- Phrases like "let's sync Thursday", "can we meet next week", "I'll call you at 3", "dinner Friday", "flight on the 15th"
- iMessage/Slack scheduling exchanges (even informal ones)
- Obsidian notes with a date reference that looks like a future commitment
- Email invites that didn't come with a calendar invite attachment
- When in doubt, surface it — Justin will decide what belongs on his calendar

**What to skip:**
- Events already on the calendar (checked below)
- Pure deadlines with no time component (those become regular Todoist tasks)
- Recurring standing meetings already on the calendar
- Past dates

### Pre-flight: snapshot calendar for dedup

Before spawning calendar-detection subagents, pull Justin's calendar for the next 30 days across all 3 accounts:

```bash
gws_multi.py --account all calendar list \
  --start <TODAY>T00:00:00 \
  --end <30_DAYS_OUT>T23:59:59 \
  --max 100
```

Keep this in-context as `CALENDAR_SNAPSHOT`. You'll use it to dedup candidates.

Compute `30_DAYS_OUT`:
```bash
THIRTY_DAYS_OUT=$(date -d "$TODAY + 30 days" +%F)
```

### Calendar-detection subagents

Run alongside Batch 1/2/3 of the regular inbox gather — they share the same sources but look for different signals. The same subagents can return both action-item candidates AND calendar-event candidates in a single run; just ask them to produce two labeled sections in their output:

**Section 1: `## Action items`** — regular Todoist tasks (as before)
**Section 2: `## Potential calendar events`** — future commitments spotted while scanning

Update each existing subagent's context to include:

> Also scan for **potential calendar events**: any specific future date + time mentioned, scheduling language ("let's sync", "meet me at", "dinner", "call", "flight", "appointment"), or implied commitments with a time component. Cast wide — surface anything that looks like it might belong on a calendar, even informal scheduling. List these under a separate `## Potential calendar events` section.
>
> Format each calendar candidate:
> `- [Source] <concise event description> | when: <date/time as mentioned> | context: <brief where/with whom>`

### Calendar dedup

After subagents return, filter the calendar candidates against `CALENDAR_SNAPSHOT`:
- If an event with the same date, time, and rough description already exists → mark EXISTS, drop it
- If something similar exists but details differ → mark SIMILAR, keep with a note
- Everything else → NEW

### Calendar candidates output format

Present calendar candidates in a dedicated section (Step 4 output), separate from regular inbox candidates. Suggest a target calendar account (`work` or `personal-main`) for each candidate based on context.

```
📅 Found N potential calendar events not yet on your calendar:

1. [Slack] Sync with Maya re: sprint planning | when: Thursday 2pm | calendar: work | context: #product-eng
2. [Email/work] Call with Alex | when: next Monday 10am | calendar: work | context: email from Alex Chen
3. [iMessage/Nana] Dentist appointment (Jamie) | when: June 3rd | calendar: personal-main | context: Nana's text
```

When Justin confirms, schedule/create the events directly on the respective Google Calendar accounts (`work` or `personal-main`) using the calendar write capabilities:
`gws_multi.py --account <name> calendar create --summary "<Summary>" --start "<Start>" --end "<End>" --location "<Location>" --description "<Description>"`

Only create a Todoist "Add to calendar:" task as an exceptional fallback if Justin specifically requests it or if the event timing/date is too ambiguous to schedule directly.

---

## Step 3 — Deduplicate

You now have subagent summaries (3–5 source lists) plus the Todoist snapshot from Step 1.

For each candidate task:
1. Check the Todoist snapshot for a semantically similar task. Similar = same person/issue/thread/subject matter, close enough that adding a second task would be redundant.
2. For Linear issues, check if an existing Todoist task's title, description, or content links/references the same Linear issue identifier (e.g., `PROD-533` or `CLAW-31`). If a match is found, mark it **EXISTS** and filter it out. Do not suggest a new task for any Linear issue already tracked in Todoist in any form.
3. Mark it as **NEW** (not in Todoist) or **EXISTS** (already covered). If it's close but not exact, mark it **SIMILAR** and note what the existing task is.

This dedup is LLM reasoning — you're comparing intent and subject matter, not text equality. Be conservative: if in doubt, mark it NEW and let Justin decide.

Build the final candidate list: only NEW and SIMILAR items. Drop EXISTS.

---

## Step 4 — Present to Justin

Show two sections. Within the inbox section, group candidates by semantic theme (same project, same person, same context). Don't number across groups — number within each group.

**When called from morning briefing:** present calendar candidates first (Phase 3 of briefing), then inbox candidates (Phase 4). The briefing skill controls the turn order; this skill just provides the formatted output for each section.

**When called standalone:** present both sections in one message.

### Section A — Calendar events

```
📅 N potential calendar events not yet on your calendar:

1. [Slack] Sync with Maya re: sprint planning | when: Thu 2pm | calendar: work | context: #product-eng
2. [iMessage/Nana] Jamie's dentist | when: June 3rd | calendar: personal-main | context: Nana's text Tue
3. [Email/work] Call with Alex | when: next Mon 10am | calendar: work | context: email from Alex Chen

Which ones should I add directly to your Google Calendar? (say "all", "1 3", or "skip 2")
```

### Section B — Inbox tasks, batched by theme

Group semantically related items under a bolded label. Number items continuously across groups.

```
📥 N potential inbox items not yet in Todoist:

**Replies owed**
1. [Slack] Reply to @maya re: sprint retro format — #product-eng
2. [Email/work] Reply to Alex about Q3 roadmap review

**Linear**
3. [Linear/assigned] Work on SL-204 Update onboarding copy
4. [Linear/triage] Triage SL-312 Crash on lesson complete

**Home / family**
5. [Obsidian/2026-05-20] Follow up on Nana's dentist appointment

~SIMILAR~ (already in Todoist but different angle):
6. [Email/work] Alex re: API rate limit spike — similar to existing "Investigate API latency" task

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
- **Calendar prep tasks: be selective.** Justin generally does *not* want generic meeting prep tasks suggested. Skip standups, regular team syncs, internal 1:1s, leadership syncs, and short chat blocks. Only suggest prep tasks for high-stakes meetings with external clients/partners where explicit preparation is clearly warranted.
- **Date precision.** Pre-compute dates once (Step 1) and pass them to every subagent. Don't trust subagents to re-derive TODAY or LOOKBACK_START.

## Pitfalls

- **Granola notes are in `<vault>/Granola/YYYY-MM/` month subfolders.** Filenames start with `YYYY-MM-DD`. Only lines beginning `- Justin:` (case-insensitive) under the `### Next Steps` section are action items for Justin. Everything else is noise.
- **`delegate_task` concurrency cap is 3.** With 6 sources (Slack, Gmail, Obsidian, Calendar, Linear, Granola), split into two or three batches: Batch 1 (Slack, Gmail, Obsidian), Batch 2 (Calendar, Linear, Granola). Don't try to pass more than 3 at once — it errors immediately.
- **Linear task naming is fixed.** Do not invent task titles for Linear items. Use exactly `Work on <ID> <name>` for assigned issues and `Triage <ID> <name>` for triage issues. Strip these from the source prefix when adding to Todoist — the content field should be the bare task name, not `[Linear/assigned] Work on…`.
- **`find-tasks` requires at least one filter.** If you call it with no args it errors. See Step 1 for the right snapshot call.
- **Dedup is semantic, not textual.** \"Reply to Maya about retro\" and \"Respond to Maya re: retrospective\" are the same action. Don't add both.
- **Priorities are strings (`"p1"`–`"p4"`), not integers.** Default to `"p4"`.
- **Don't use `update-tasks` to change due dates on recurring tasks** — use `reschedule-tasks`. This skill mostly adds new tasks, so this pitfall is rare here.
- **Gmail date format is `YYYY/MM/DD` (slashes), not dashes.** Calendar and Linear use ISO dashes. Keep them separate.
- **`gws_multi.py` path varies.** Always resolve as `${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py`.
- **Slack `--limit` flag.** The Slack CLI may not support `--limit` on all commands. If it errors, drop the flag and let it return the default count.
- **App Store Connect emails.** These are engineering issues, not Justin's. Filter them out at the Gmail subagent stage.
- **Never call the Todoist REST API directly (`api.todoist.com`) in custom scripts or subagents.** The sync v9 and REST v2 endpoints are deprecated (HTTP 410 / 404). Always use the native `mcp_todoist_*` tools. If a script inside `execute_code` or a background task absolutely must make raw HTTP requests, use the correct v1 path `https://api.todoist.com/api/v1/` (e.g. `/api/v1/tasks` or `/api/v1/sync` as a POST request) and include the `TODOIST_API_KEY` header.

## References
- See [references/exclusions.md](references/exclusions.md) for detailed rules on source and state-based candidate filtering.
