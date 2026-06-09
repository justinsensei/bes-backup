---
name: wind-down
description: "Interactive daily wrap-up: 1. Work log draft/write; 2. Vault inbox triage; 3. Source review; 4. Next day's calendar preview."
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [productivity, wind-down, daily-routine, work-log, inbox-triage, sources, calendar]
    related_skills: [work-log, morning-briefing, obsidian, todoist]
---

# 🌅 Daily Wind-Down & Wrap-Up

This skill governs the **interactive daily wind-down and wrap-up session** for Justin.
It runs in the late afternoon/evening when Justin is ready to close his workday, clear his head, and organize his second brain for tomorrow.

## Triggers

- "Let's start my wind down"
- "let's wrap up for today"
- "wind down"
- "wrap up"

## Sequence of Phases

The wind-down session runs interactively in a strict, step-by-step sequence. Wait for Justin's confirmation or feedback at the end of each phase before proceeding.

---

### Phase 1 — Work Log Draft & Alignment

Draft today's work log, align with Justin, and write it to today's daily note.

1. **Calculate Dates:**
   - Determine `TARGET_DATE` as today (e.g., `2026-06-07` in local time).
   - Pre-compute timezone offsets dynamically to prevent UTC boundary leakage on calendar searches.

2. **Gather Today's Raw Activities (Fast-track):**
   - Run `/home/justin.guest/.hermes/skills/note-taking/work-log/references/direct_execution.py` via `terminal` (with `export TARGET_DATE=<YYYY-MM-DD>`) or `execute_code` (setting `os.environ['TARGET_DATE'] = today_date`) to pull Slack, Linear, and Google Workspace calendar/email data in seconds. Using `terminal` is the preferred bulletproof pattern since `execute_code` can be restricted by environment-level approval settings.
   - Query Todoist live for completed tasks today (`mcp_todoist_find_completed_tasks` with `since: <TODAY>`, `until: <TODAY>`, `getBy: "completion"`) and incomplete tasks due today (`mcp_todoist_find_tasks_by_date` with `startDate: <TODAY>`).
   - Read today's existing Obsidian daily note with `read_file` to see manual notepad entries.
   - Search the vault for any meeting/Granola notes generated today (look in `vault/meetings/` or files containing today's date in their name).

3. **Synthesize the Work Log Draft:**
   - Synthesize the gathered material into a set of clean, structured blocks matching the standard work log format:
     - **Preview Summary:** A highly concise, 1-2 sentence active-voice overview of the day's main focus.
     - **📅 Schedule & Events:** Chronological bullet list of meetings and events.
     - **🚀 Highlights & Decisions:** Synthesized highlights, bolded decisions (with accurate attribution), and open questions/blockers.
     - **🏆 Accomplishments:** Completed Todoist tasks, closed Linear issues, or git commits.

4. **Present the Draft to Justin:**
   - Deliver the formatted draft in chat.
   - Ask a short, focused question to capture offline context:
     *"Here is the draft of today's work log. Anything else from today that isn't captured here (e.g., side-quests, offline discussions, IRL decisions)?"*
   - **Wait for Justin's response.**

5. **Write the Finalized Work Log:**
   - Combine Justin's feedback with the draft.
   - Find or create today's daily note in `<vault>/daily/<YYYY-MM-DD-weekday>.md` (create from template `<vault>/utilities/templates/daily_note.md` if missing, stripping Templater tags).
   - Overwrite/replace the corresponding headings (`> [!summary]`, `## 📅 Schedule & Events`, `## 🚀 Highlights & Decisions`, `## 🏆 Accomplishments`) with your new synthesized content.
   - **Crucial:** Preserve the entire content of the `## 🗒 Notepad` section (including manual text written by Justin). Never modify or delete it.
   - Append the sources attribution footer at the very bottom.

---

### Phase 2 — Vault Inbox Triage

Help Justin empty his Obsidian "inbox" so quick notes and scratchpads land in their correct homes.

1. **Scan the Inbox Directory:**
   - List all files inside the vault inbox directory (`/home/justin.guest/vault/inbox/`) using `search_files(path='/home/justin.guest/vault/inbox', pattern='*')`.

2. **Read & Classify Inbox Notes:**
   - For each file in the inbox, read its first few lines using `read_file`.
   - Determine its primary focus and suggest the correct target category and folder under `/home/justin.guest/vault/`:
     - **`Contacts/`** (Category: `[[People]]` or `[[Organizations]]`) — if about a person, family member, or company/institution.
     - **`Logs/Meetings/`** (Category: `[[Meetings]]`) — if a meeting sync, agenda, or discussion record.
     - **`Notes/`** (Category: `[[Thoughts]]`, `[[Beliefs]]`, `[[Memory]]`, `[[Decisions]]`, `[[Projects]]`, `[[References]]`, `[[Sources]]`, or `[[Notes]]`) — if conceptual, ideas, principles, personal memories, decisions, project hubs, reference guides, or raw notes.

3. **Present Triage Options to Justin:**
   - List the inbox notes and your suggested folder movements in a clean, numbered list:
     ```
     📥 N items in your vault inbox:
     1. `Nana pride 20260607093335.md` → move to `Contacts/` (Category: `[[People]]`) (Notes on Nana and Pride event)
     2. `Jamie lawn 20260607093304.md` → move to `Contacts/` (Category: `[[People]]`) (Notes on Jamie mowing the lawn)
     3. `20260605162856.md` → move to `Notes/` (Category: `[[Thoughts]]`) (Quick thought on...)
     ...
     Shall I move these as suggested, or would you like to route them differently?
     ```
   - **Wait for Justin's response.**

4. **Execute the Movements:**
   - Move the confirmed files to their target directories (creating directories if needed).
   - If a file is renamed to fit a naming convention, let Justin know.
   - If any bidirectional links or mentions exist, make sure they remain valid.

---

### Phase 3 — Source Review

Review persistent reference sources, articles, or transcripts added or updated today.

1. **Find Today's Sources:**
   - Scan `/home/justin.guest/vault/sources/` for files modified in the last 24 hours (using `find ~/vault/sources -mtime -1 -type f` or `search_files`).
   - Check if any new source files contain `daily_note: "[[<TODAY_DATE> ...]]"` in their frontmatter.

2. **Summarize Today's Sources:**
   - If new sources are found, read their summaries/highlights using `read_file`.
   - Present a highly concise summary of each new source (title, author, original URL, and 2-3 key takeaways or notable highlights).
   - If no new sources were added today, state: *"No new sources added today."*

3. **Present & Check Action Items:**
   - Ask if Justin has any thoughts on these sources or wants to capture any action items from them into Todoist:
     *"Any highlights you want to turn into Todoist tasks, or shall we move to tomorrow's calendar?"*
   - **Wait for Justin's response.**

---

### Phase 4 — Tomorrow's Calendar Preview

Preview tomorrow's schedule to establish mental readiness and coordinate upcoming tasks.

1. **Fetch Tomorrow's Schedule:**
   - Calculate tomorrow's local date.
   - Fetch events across all accounts (work and personal) using `gws_multi.py` with correct dynamic timezone offset:
     ```bash
     python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account all calendar list --start <TOMORROW>T00:00:00<OFFSET> --end <TOMORROW>T23:59:59<OFFSET> --max 50
     ```

2. **Present Tomorrow's Preview:**
   - Output a clean, chronological bullet list:
     `- **HH:MM - HH:MM** Event Title [Account/Context]`
   - Call out noteworthy patterns:
     - Back-to-back blocks or intense scheduling.
     - High-prep meetings or external attendees.
     - First event of the day (so he knows when his morning starts).
   - **Wait for Justin's acknowledgment.**

---

### Phase 5 — Kick off Gbrain Dream Cycle

The final phase starts the automated overnight consolidation, keeping the "second brain" sharp.

1. **Launch the Dream Cycle:**
   - Inform Justin that you are kicking off the overnight maintenance run.
   - Run the nightly dream cycle shell script in the background:
     ```bash
     bash ~/.hermes/scripts/dream_cycle.sh &
     ```
   - Confirm to Justin:
     *"Overnight dream cycle is kicked off. It will run through entity sweeps, citation audits, and cross-session memory consolidation while you sleep."*

2. **Close out:**
   - End with a quiet, minimal sign-off (e.g., *"Have a good evening, Justin. See you tomorrow."*).

---

## Tone and Pacing

- Keep explanations minimal. Do not use filler or hedging theater.
- One phase per message. Do not dump the entire session at once.
- Wait for Justin's explicit go-ahead or text response between phases.

## Pitfalls & Defensive Rules

- **Preserve the Notepad:** Always load today's daily note first, find the `## 🗒 Notepad` section, and keep its contents completely intact.
- **Accurate Attribution:** When drafting highlights and decisions from emails or meeting notes, ensure decisions are attributed to the correct person (e.g., Anya, Nana, teachers, etc.) rather than assuming Justin made them.
- **Escape Slack Channels:** Always write `#channel-name` as `\#channel-name` inside the daily note so Obsidian doesn't parse it as a tag.
- **Dynamic Timezone Offset:** When fetching calendar events, always calculate and append the local timezone offset (e.g. `-04:00` or `-05:00`) to `--start` and `--end` to prevent boundary events from leaking from yesterday or tomorrow.
- **Git Commit Warning:** Do not manually `git add` or `git commit` any vault edits. The `bes-vault-sync` watcher will handle it immediately.
