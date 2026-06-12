---
name: wind-down
description: "Interactive daily wrap-up: 1. Input candidates; 2. Discovered contacts; 2b. Discovered projects; 3. Everything In Its Right Place (EIIRP) Vault Hygiene & Triage; 4. Work log draft/write; 5. Open loops; 6. Next day's calendar preview."
version: 1.3.0
author: Bes
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: [productivity, wind-down, daily-routine, work-log, inbox-triage, sources, calendar, hygiene]
    related_skills: [work-log, morning-briefing, obsidian, obsidian-hygiene, llm-wiki, todoist]
---

# 🌅 Daily Wind-Down & Wrap-Up

## Overview

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

### Phase 1 — Input Candidates

Present potential input candidates (active Slack conversations and noteworthy primary-category emails from the last 36-48 hours) that Justin hasn't tagged with `🧠` or forwarded to Bes, but that are highly worthy of being turned into inputs in his vault.

Run the unified script live to fetch candidates:
`python3 /home/justin.guest/.hermes/scripts/fetch_source_candidates.py`

If candidates (Slack or Email) are found:
- Show them with sequential numbers across both Slack and Email candidates.
- Format:
  ```
  📋 N potential input candidates:

  **Slack Conversations**
  1. [\#channel-name] Topic or Preview — participants: Alice, Bob, Justin
  2. [\#channel-name] Topic or Preview — participants: Endre, Justin

  **Emails**
  3. [Email/<account>] Subject line — from: Sender Name (Date)
  ...

  Would you like to turn any of these conversations into inputs in your vault? (e.g. "yes, 1", "save 1 and 3", or "skip")
  ```

If Justin selects any:
1. For each selected item:
   - **For Slack conversations:**
     - Synthesize a high-quality summary showing "who said what" clearly. Do NOT store verbatim Slack messages; store only summaries with retrieval metadata.
     - Write to `$OBSIDIAN_VAULT_PATH/Inputs/Slack/YYYY-MM-DD - Spaced Title.md`.
     - Structure the YAML frontmatter for Slack inputs:
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
       `* [[Inputs/Slack/<filename>|Slack summary]]: <One-sentence-gist>.`
     - Run the command to mark it processed:
       `python3 /home/justin.guest/.hermes/scripts/fetch_slack_brains.py --mark-processed <channel_id> <ts>`
   - **For Emails:**
     - Synthesize a high-quality summary of the email thread showing clearly what was discussed, decided, or requested. Do NOT store verbatim email text; store only summaries with retrieval metadata.
     - Write to `$OBSIDIAN_VAULT_PATH/Inputs/Emails/YYYY-MM-DD - Spaced Subject.md`.
     - Structure the YAML frontmatter for email inputs:
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
       `* [[Inputs/Emails/<filename>|Email summary]]: <One-sentence-gist>.`
     - Run the command to mark it processed:
       `python3 /home/justin.guest/.hermes/scripts/fetch_source_candidates.py --mark-email-processed <thread_id>`
   - Report the input(s) successfully saved.

If no candidates are found, skip this phase entirely and proceed to Phase 2.

---

### Phase 2 — Discovered Contacts & Organizations

Present any discovered contacts or organizations (unresolved wikilinks found by the `check_vault_signals.py` script) from today's cache file at `~/.hermes/morning-briefing/YYYY-MM-DD.json` (under the `discovered_contacts` field).

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
1. For each selected item, check if the contact file already exists in `/home/justin.guest/vault/Contacts/<Name>.md` OR in `/home/justin.guest/vault/Inbox/<Name>.md`.
2. If the file exists in either location, do NOT overwrite or truncate it (as it contains precious history/timeline entries). Instead, patch the file in its current location to insert the standard frontmatter, executive summary, and state sections at the very top, preserving any existing content (like `## Timeline` and its entries) underneath.
3. If the file does not exist in either location, create a new file in the inbox directory `/home/justin.guest/vault/Inbox/<Name>.md` and format the contact note following these strict standards:
   * Frontmatter:
     ```yaml
     ---
     id: <timestamp_id> # YYYYMMDDHHmmss format based on current time
     category: "[[People]]" # (or [[Organizations]])
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
3. Report success and confirm creation in the inbox directory.

If no discovered contacts are found, proceed to Phase 2b.

---

### Phase 2b — Discovered Projects

Project discovery runs at **wrap-up**, not morning briefing. Surface candidates from today's ingests that look like project names but have no matching `Notes/Projects/` hub.

1. Run live at wind-down start:
   ```bash
   python3 ~/.hermes/scripts/check_vault_signals.py --discover-projects
   ```
2. Also read today's unmatched candidates from `~/.hermes/state/integrate_entities_unmatched.json` (keyed by today's date).
3. Merge and dedupe both sources.

If no discovered projects are found, skip this phase and proceed to Phase 3.

Format:
```
📁 N discovered project candidates:

1. [K12 GTM] — first mentioned in [[Inbox/2026-06-10 - Decision - K12 GTM]]
2. [SignLab Classroom] — from integrate_entities_unmatched

Would you like to create project hub notes for any of these? (e.g. "yes, 1", or "skip")
```

If Justin selects any:
1. Create stub in `/home/justin.guest/vault/Inbox/<Title>.md` with project hub schema:
   ```yaml
   ---
   id: <timestamp_id>
   daily_note: "[[<YYYY-MM-DD Weekday>]]"
   category: "[[Projects]]"
   ---
   ```
   ```markdown
   > Executive summary: <One-line project purpose>.

   Status: Active

   ## State
   -

   ## Timeline
   - <Date> | Discovered — Mentioned in [[<context_file>]].

   ## Related inputs
   -
   ```
2. Clear processed entries from `integrate_entities_unmatched.json` for today's date after session.
3. Report success.

---

### Phase 3 — Everything In Its Right Place (EIIRP) Vault Hygiene & Triage

This phase implements the formal 7-phase EIIRP cycle to perform comprehensive note hygiene, frontmatter validation, and inbox triage across the entire vault. This ensures files are clean, metadata is valid, and the knowledge graph is richly linked.

Wait for Justin's confirmation or feedback at the end of the EIIRP report (Step 7) before executing any folder movements or renaming notes.

1. **Step 1: Inventory (Scan & List)**
   - Scan the vault inbox directory (`/home/justin.guest/vault/Inbox/`) using `search_files(path='/home/justin.guest/vault/inbox', pattern='*')`.
   - Identify any other files modified or created in the vault within the last 24 hours (excluding automated/system logs unless they need structural triage).

2. **Step 2: Taxonomy (Classification & Routing)**
   - Classify all inventoried notes based on content analysis and map them to their correct Obsidian folder routes:
     - **`Contacts/`** (Category: `[[People]]` or `[[Organizations]]`):
       - *Crucial Rule:* Any brand-new contact note created by Bes must land in `/home/justin.guest/vault/Inbox/`. Existing contacts already under `Contacts/` are updated in place and must *never* be relocated.
     - **`Inputs/Meetings/`** (Category: `[[Meetings]]`):
       - Meeting syncs, agendas, Granola summaries.
     - **`Inputs/Readings/`** (Category: `[[Readings]]`):
       - Raw reading imports (immutable).
     - **`Notes/`** with **`[[Sources]]`**:
       - Compiled bibliographical records (integrate-full, not raw imports).
     - **`Notes/`** (maturity tiers):
       - Thoughts, concepts, beliefs, memories, decisions, projects:
         - **`Notes/Thoughts`** (Category: `[[Thoughts]]`) — reflections, raw thoughts, ideas, and opinions.
         - **`Notes/Concepts`** (Category: `[[Concepts]]`) — models, theories, definitions, or educational concepts (others' thinking).
         - **`Notes/References`** (Category: `[[References]]`) — patterns, structured guides, technical reference sheets (note: Justin uses Apple Notes as a "filing cabinet" for references, but continues using Obsidian for general note-taking/referencing).
         - **`Notes/Beliefs`** (Category: `[[Beliefs]]`) — philosophies and core values (axioms).
         - **`Notes/Memories`** (Category: `[[Memories]]`) — personal memories or historical highlights.
         - **`Notes/Decisions`** (Category: `[[Decisions]]`) — specific personal or project-related choices.
         - **`Notes/Projects`** (Category: `[[Projects]]`) — active project hubs and dashboard files.

3. **Step 3: Schema Check (Frontmatter Validation)**
   - Validate the YAML frontmatter headers of all new or modified notes.
   - Enforce the following criteria:
     - **Identifiers:** Every note must contain a 14-digit unique timestamp identifier (`id: YYYYMMDDHHmmss` format) in its frontmatter.
     - **Daily Note Link:** Ensure `daily_note: "[[<YYYY-MM-DD Weekday>]]"` is present and correctly matches the note's creation date.
     - **Category:** Confirm the correct `category` matches the note's taxonomy (e.g. `category: "[[Thoughts]]"`).
     - **Frontmatter Safety:**
       - Ensure a closing `---` divider is present and sits on its own line after the properties block to avoid unclosed properties blocks.
       - Verify that adding/updating properties doesn't result in "dangling closing dividers" or merged text (e.g., `daily_note: '...'---` is invalid).
       - Ensure timeline removal or legacy cleanup patterns do not accidentally match and destroy the frontmatter closing divider.

4. **Step 4: File & Filing (Execution & Triage)**
   - Run the automated vault hygiene routines to auto-reconcile, move, and link files.
   - **Run the automated script:**
     ```bash
     python3 ~/.hermes/scripts/vault_hygiene.py
     ```
     - This script automatically relocates misplaced daily notes to `Daily Notes/`, converts legacy inline tags (like `#people` or `#meeting`) to category YAML metadata, and runs the auto-linker to convert plain-text mentions of known contacts and projects into proper wikilinks.
   - For all other inbox notes requiring human judgment, compile your recommended movements and renames into the final report.



6. **Step 6: Verification (Link & Orphan Audit)**
   - Verify that all internal and external wikilinks inside the newly created or modified notes are valid and not broken. **Important:** Ignore any broken link errors originating from files within the `/Inputs/` directory or any of its sub-folders.
   - Scan for orphaned files created today (i.e. notes with zero incoming or outgoing links) and propose relevant connections to existing daily notes or project hubs.

7. **Step 7: Report (Unified Status Summary)**
   - Generate a beautifully formatted, unified status summary of the 7-phase EIIRP run.
   - Present this report to Justin in Telegram. It must summarize:
     - **Inventory:** Notes analyzed today.
     - **Taxonomy & Schema:** Recommended destination subfolders, categories, and frontmatter validation results.
     - **File & Filing:** Misplaced notes relocated by `vault_hygiene.py` and suggested manual inbox triage routes.
     - **Audit & Verification:** Reconnection/audit results, broken links, and orphaned notes.
     - *Format example:*
       ```
       📥 EIIRP Vault Hygiene & Triage Report:

       1. **Inventory**: 3 new files found in Inbox/ and 2 modified today.
       2. **Taxonomy & Schema**:
          - `20260610090000.md` → Suggest `Notes/Thoughts` (Category: `[[Thoughts]]`). Frontmatter: Valid.
          - `New Contact.md` → Suggest `Inbox/` (Category: `[[People]]`). Frontmatter: Missing daily_note link, will heal.
       3. **File & Filing**:
          - Misplaced daily note `2026-06-09 Tuesday.md` moved from Inbox/ to `Daily Notes/` via `vault_hygiene.py`.
       4. **Audit & Verification**:
          - Broken link detected in `20260610090000.md` pointing to non-existent `[[Project Alpha]]`.
          - All other links valid. No orphaned notes.

       Shall I execute these inbox movements and heal the frontmatter as suggested, or would you like to route them differently?
       ```
   - **Wait for Justin's response and explicit approval before moving any inbox files or applying manual frontmatter edits.**

---

### Phase 4 — Work Log Draft & Alignment

Draft today's work log, align with Justin, and write it to today's daily note. This step runs towards the end of the wind-down so that any activities, contact creations, log files, or inbox triage completed during previous steps are fully incorporated, ensuring the work log captures the final state of play for the day.

1. **Calculate Dates:**
   - Determine `TARGET_DATE` as today (e.g., `2026-06-07` in local time).
   - Pre-compute timezone offsets dynamically to prevent UTC boundary leakage on calendar searches.

2. **Gather Today's Raw Activities (Fast-track):**
   - Run `/home/justin.guest/.hermes/skills/note-taking/work-log/references/direct_execution.py` via `terminal` (with `export TARGET_DATE=<YYYY-MM-DD>`) or `execute_code` (setting `os.environ['TARGET_DATE'] = today_date`) to pull Slack, Linear, and Google Workspace calendar/email data in seconds. Using `terminal` is the preferred bulletproof pattern since `execute_code` can be restricted by environment-level approval settings.
   - Query Todoist live for completed tasks today (`mcp_todoist_find_completed_tasks` with `since: <TODAY>`, `until: <TODAY>`, `getBy: "completion"`) and incomplete tasks due today (`mcp_todoist_find_tasks_by_date` with `startDate: <TODAY>`).
   - Read today's existing Obsidian daily note with `read_file` to see manual notepad entries.
   - Search the vault for any meeting/Granola notes generated today (look in `vault/Meetings/` or files containing today's date in their name).
   - Read the daily briefing cache `/home/justin.guest/.hermes/morning-briefing/<YYYY-MM-DD>.json` to check the `vault_activity` field, and run a quick terminal find command over the vault to gather any high-level vault restructuring, bulk updates, or manual categorization sweeps that took place during the day.

3. **Synthesize the Work Log Draft:**
   - Synthesize the gathered material into a set of clean, structured blocks matching the standard work log format:
     - **Preview Summary:** A highly concise, 1-2 sentence active-voice overview of the day's main focus.
     - **📅 Schedule & Events:** Chronological bullet list of meetings and events.
     - **🚀 Highlights & Decisions:** Synthesized highlights, bolded decisions (with accurate attribution), and open questions/blockers.
     - **🏆 Accomplishments:** Completed Todoist tasks, closed Linear issues, git commits, or high-level vault changes (major file movements, bulk hygiene updates, or structural cleanups).

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

### Phase 5 — Open Loops

This phase reviews the central `Open Loops.md` file, gathers context to help close loops, and captures any new open loops that have emerged.

1.  **Review Existing Open Loops:**
    - Read the contents of `/home/justin.guest/vault/Open Loops.md`. The file is a simple bulleted list.
    - For each open loop (each line starting with `- `), gather relevant context that might indicate the loop can be closed. This includes:
        - Recently completed Todoist tasks.
        - Recently created or modified vault notes with similar keywords.
        - Recent calendar events.
        - Relevant Slack or email conversations.

2.  **Present for Closure Review:**
    - Present each open loop along with the context you've gathered.
    - Format:
      ```
      🌀 Open Loops Review:

      1. `- Follow up with [[Alice]] about the [[Project X]] deadline`
         - **Context:** You completed the Todoist task "Draft Project X timeline" yesterday. A new document `Notes/Project X Timeline Q3.md` was also created.
      2. `- Plan birthday party`
         - **Context:** A calendar event "Nana's Birthday Dinner" was created for this Saturday.

      Which of these loops are now closed and can be removed? (e.g. "1 and 2", "remove 1", or "none")
      ```
    - **Wait for Justin's response.**

3.  **Capture New Open Loops:**
    - After processing closures, ask a simple, open-ended question to capture new loops.
      *"Any new open loops on your mind to add to the list?"*
    - **Wait for Justin's response.**

4.  **Update the Master File:**
    - Atomically update the `/home/justin.guest/vault/Open Loops.md` file:
      - Remove the lines for loops Justin confirmed are closed.
      - Append any new loops he provided as simple bullets (`- ...`).
    - Report success, showing the final state of the file or a summary of changes.

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

- **Noisy Project Suggestions:** The project discovery phase can be noisy and suggest non-project entities. Use judgment and confirm with Justin before creating new project notes.
- **Preserve the Notepad:** Always load today's daily note first, find the `## 🗒 Notepad` section, and keep its contents completely intact.
- **Inputs Terminology:** Always refer to Slack threads, emails, and other primary-category sources as "inputs" rather than "logs" in both conversations and note frontmatter, as per the updated vault schema.
- **Accurate Attribution:** When drafting highlights and decisions from emails or meeting notes, ensure decisions are attributed to the correct person (e.g., Anya, Nana, teachers, etc.) rather than assuming Justin made them.
- **Escape Slack Channels:** Always write `#channel-name` as `\#channel-name` inside the daily note so Obsidian doesn't parse it as a tag.
- **Dynamic Timezone Offset:** When fetching calendar events, always calculate and append the local timezone offset (e.g. `-04:00` or `-05:00`) to `--start` and `--end` to prevent boundary events from leaking from yesterday or tomorrow.
- **Git Commit Warning:** Do not manually `git add` or `git commit` any vault edits. The `bes-vault-sync` watcher will handle it immediately.
- **Todoist Task Creation Rule:** When creating any Todoist task, always add a one-sentence comment immediately after — source + why it became a task.
- **Todoist Filter Preference:** Do not present tasks using native Todoist sidebar views (Today, Inbox, etc.), as Justin finds them cluttered. Emphasize saved filter views.
- **Frontmatter Safety & Infinite Loops:** Avoid extracting body content in a way that includes leading newlines, preventing infinite overwrite loops during hygiene tasks. Always `.lstrip()` body content immediately upon extraction.
- **Dangling Closing Dividers:** Ensure any automated or manual procedure that adds or updates properties writes back the closing divider (`---`) on a *fresh line*. Writing it without an intervening newline will append it directly to the end of the last property string (e.g., `daily_note: '...'---`), which corrupts properties.
- **Non-Unique Aliases Guard:** Always skip auto-linking any alias that is non-unique (shared by more than one distinct contact path) to avoid incorrect connections in the vault.
- **Timelines Deactivation (manual wind-down):** Do not manually append `## Timeline` bullets to contact cards during wind-down; rely on Obsidian's native Backlinks panel instead. **`integrate-entities`** is the sanctioned automated append path for both contacts and projects at ingest time — cron and meeting reconcile use it.
- **Open Loops File:** Do not modify the `/home/justin.guest/vault/Open Loops.md` file directly. All changes must be presented to and approved by Justin during the interactive review.

## Verification Checklist

- [ ] All 6 phases completed in strict interactive sequence.
- [ ] Today's Notepad section in the daily note preserved completely intact without modification or truncation.
- [ ] Frontmatter properties (`id`, `daily_note`, `category`) checked and validated for all triaged notes.
- [ ] Misplaced daily notes and logs successfully reorganized using `vault_hygiene.py`.
- [ ] Discovered contacts drafted in the inbox, and existing contact cards updated in place without relocation.
- [ ] Work log draft synthesized with accurate attribution of decisions, and written to today's daily note.
- [ ] Tomorrow's schedule fetched and presented with timezone-aware calendar offsets.
