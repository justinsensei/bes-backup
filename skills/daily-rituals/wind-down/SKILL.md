---
name: wind-down
description: "Interactive daily wrap-up: 1. Log candidates; 2. Discovered contacts; 3. Source review; 4. Vault inbox triage; 5. Work log draft/write; 6. Next day's calendar preview."
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
It runs in the late afternoon/evening when Justin is ready to close his workday, clear his head, and organize his vault for tomorrow.

## Triggers

- "Let's start my wind down"
- "let's wrap up for today"
- "wind down"
- "wrap up"

## Sequence of Phases

The wind-down session runs interactively in a strict, step-by-step sequence. Wait for Justin's confirmation or feedback at the end of each phase before proceeding.

---

### Phase 1 — Log Candidates

Present potential log candidates (active Slack conversations and noteworthy primary-category emails from the last 36-48 hours) that Justin hasn't tagged with `🧠` or forwarded to Bes, but that are highly worthy of being turned into logs in his vault.

Run the unified script live to fetch candidates:
`python3 /home/justin.guest/.hermes/scripts/fetch_source_candidates.py`

If candidates (Slack or Email) are found:
- Show them with sequential numbers across both Slack and Email candidates.
- Format:
  ```
  📋 N potential log candidates:

  **Slack Conversations**
  1. [\#channel-name] Topic or Preview — participants: Alice, Bob, Justin
  2. [\#channel-name] Topic or Preview — participants: Endre, Justin

  **Emails**
  3. [Email/<account>] Subject line — from: Sender Name (Date)
  ...

  Would you like to turn any of these conversations into logs in your vault? (e.g. "yes, 1", "save 1 and 3", or "skip")
  ```

If Justin selects any:
1. For each selected item:
   - **For Slack conversations:**
     - Synthesize a high-quality summary showing "who said what" clearly. Do NOT store verbatim Slack messages; store only summaries with retrieval metadata.
     - Write to `/home/justin.guest/vault/Logs/Slack/YYYY-MM-DD - Spaced Title.md`.
     - Structure the YAML frontmatter for Slack logs:
       ```yaml
       ---
       id: <timestamp_id> # YYYYMMDDHHmmss based on first message
       daily_note: "[[<YYYY-MM-DD Weekday>]]"
       original_url: "<permalink>"
       category: "[[Slack]]"
       channel: "<channel_name>"
       participants:
         - "Participant Name"
       ---
       ```
     - Append a link and one-sentence gist to today's daily note notepad under `## 🗒 Notepad`:
       `* [[Logs/Slack/<filename>|Slack summary]]: <One-sentence-gist>.`
     - Run the command to mark it processed:
       `python3 /home/justin.guest/.hermes/scripts/fetch_slack_brains.py --mark-processed <channel_id> <ts>`
   - **For Emails:**
     - Synthesize a high-quality summary of the email thread showing clearly what was discussed, decided, or requested. Do NOT store verbatim email text; store only summaries with retrieval metadata.
     - Write to `/home/justin.guest/vault/Logs/Emails/YYYY-MM-DD - Spaced Subject.md`.
     - Structure the YAML frontmatter for email logs:
       ```yaml
       ---
       id: <timestamp_id> # YYYYMMDDHHmmss based on first email
       daily_note: "[[<YYYY-MM-DD Weekday>]]"
       original_url: "<permalink>"
       category: "[[Emails]]"
       account: "<work | personal-main>"
       participants:
         - "Sender Name"
       ---
       ```
     - Append a link and one-sentence gist to today's daily note notepad under `## 🗒 Notepad`:
       `* [[Logs/Emails/<filename>|Email summary]]: <One-sentence-gist>.`
     - Run the command to mark it processed:
       `python3 /home/justin.guest/.hermes/scripts/fetch_source_candidates.py --mark-email-processed <thread_id>`
   - Report the log(s) successfully saved.

If no candidates are found, skip this phase entirely and proceed to Phase 2.

---

### Phase 2 — Discovered Contacts & Organizations

Present any discovered contacts or organizations (unresolved wikilinks found by the `check_vault_signals.py` script) from today's cache file (`discovered_contacts` field).

If no discovered contacts are found in the cache, skip this phase entirely and proceed to Phase 3.

Format:
```
👤 N discovered contact / organization candidates:

**People**
1. [Name] — first mentioned in [[context_file]]

**Organizations**
2. [Name] — first mentioned in [[context_file]]
...

Would you like me to create contact notes for any of these? (e.g. "yes, 1 as organization", "create 2", or "skip")
```

If Justin selects any:
1. For each selected item, create a new file in `/home/justin.guest/vault/Contacts/<Name>.md`.
2. Format the contact note following these strict standards:
   * Frontmatter:
     ```yaml
     ---
     id: <timestamp_id> # YYYYMMDDHHmmss format based on current time
     daily_note: "[[<YYYY-MM-DD Weekday>]]" # e.g. [[2026-06-09 Tuesday]]
     type: <person | organization>
     ---
     ```
   * Markdown body:
     ```markdown
     > Executive summary: Briefing for <Name>.

     ## State
     - **Role:** 
     - **Company:** 
     - **Relationship:** 

     ## Open Threads
     - 

     ---

     ## Timeline
     - <Date> | Discovered — Mentioned in [[<context_file_relative_path_no_ext>|<context_file_title>]].
     ```
3. Report success and confirm creation.

If no discovered contacts are found, proceed to Phase 3.

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
     *"Any highlights you want to turn into Todoist tasks, or shall we move to vault inbox triage?"*
   - **Wait for Justin's response.**

---

### Phase 4 — Vault Inbox Triage

Help Justin empty his Obsidian "inbox" so quick notes and scratchpads land in their correct homes.

1. **Scan the Inbox Directory:**
   - List all files inside the vault inbox directory (`/home/justin.guest/vault/inbox/`) using `search_files(path='/home/justin.guest/vault/inbox', pattern='*')`.

2. **Read & Classify Inbox Notes:**
   - For each file in the inbox, read its first few lines using `read_file`.
   - Determine its primary focus and suggest the correct target category and folder under `/home/justin.guest/vault/`:
     - **`Contacts/`** (Category: `[[People]]` or `[[Organizations]]`) — if about a person, family member, or company/institution.
     - **`Logs/Meetings/`** (Category: `[[Meetings]]`) — if a meeting sync, agenda, or discussion record.
     - **`Notes/`** (Category: `[[Thoughts]]`, `[[Beliefs]]`, `[[Memories]]`, `[[Decisions]]`, `[[Projects]]`, `[[References]]`, `[[Concepts]]`, or `[[Notes]]`) — if conceptual, ideas, principles, personal memories, decisions, project hubs, reference guides, or raw notes.

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

### Phase 5 — Work Log Draft & Alignment

Draft today's work log, align with Justin, and write it to today's daily note. This step runs towards the end of the wind-down so that any activities, contact creations, log files, or inbox triage completed during previous steps are fully incorporated, ensuring the work log captures the final state of play for the day.

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
   - Find or create today's daily note in `/home/justin.guest/vault/Daily Notes/YYYY-MM-DD Weekday.md` (create from template `/home/justin.guest/vault/Utilities/Templates/daily_note.md` if missing, stripping Templater tags).
   - Overwrite/replace the corresponding headings (`> [!summary]`, `## 📅 Schedule & Events`, `## 🚀 Highlights & Decisions`, `## 🏆 Accomplishments`) with your new synthesized content.
   - **Crucial:** Preserve the entire content of the `## 🗒 Notepad` section (including manual text written by Justin). Never modify or delete it.
   - Append the sources attribution footer at the very bottom.

---

### Phase 6 — Tomorrow's Calendar Preview & Close-out

Preview tomorrow's schedule to establish mental readiness, coordinate upcoming tasks, and close out the day.

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

3. **Close out:**
   - Ask for Justin's acknowledgment.
   - Once acknowledged, end with a quiet, minimal sign-off (e.g., *"Have a good evening, Justin. See you tomorrow."*).

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