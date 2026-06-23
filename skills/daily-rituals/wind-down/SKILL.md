---
name: wind-down
description: "Interactive daily wrap-up: 1. Input candidates (Slack/email); 2. Discovered contacts; 3. Work log draft/write; 4. Next day's calendar preview."
version: 2.0.0
author: Bes
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: [productivity, wind-down, daily-routine, work-log, inbox-triage, sources, calendar]
    related_skills: [work-log, morning-briefing, obsidian, todoist]
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
     - Append a link and one-sentence gist to today's daily note notepad under `## 🗒 Notepad` (if this section is missing from the daily note, append it to the bottom of the file first):
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
     - Append a link and one-sentence gist to today's daily note notepad under `## 🗒 Notepad` (if this section is missing from the daily note, append it to the bottom of the file first):
       `* [[Inputs/Emails/<filename>|Email summary]]: <One-sentence-gist>.`
     - Run the command to mark it processed:
       `python3 /home/justin.guest/.hermes/scripts/fetch_source_candidates.py --mark-email-processed <thread_id>`
   - Report the input(s) successfully saved.

If no candidates are found, skip this phase entirely and proceed to Phase 2.

---

### Phase 2 — Discovered Contacts & Organizations

Present any discovered contacts or organizations (unresolved wikilinks found by the `check_vault_signals.py` script) from the signals cache file at `~/.hermes/morning-briefing/vault_signals_last_run.json` (under the `discovered_entities.people` and `discovered_entities.organizations` fields).

If no discovered contacts are found in the signals cache, skip this phase entirely and proceed to Phase 3.

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
1. Check if the contact card already exists under `/home/justin.guest/Developer/obsidian-vault/Notes/Contacts/` OR in `/home/justin.guest/Developer/obsidian-vault/Inbox/` by performing a wildcard search on the name (e.g. searching for files matching `*Name*` using the `search_files` tool with `target='files'`). This is critical because contacts are saved with their unique timestamp appended (e.g., `Notes/Contacts/Tor Barstad 20260610075543.md`).
2. If a matching file exists in either location, do NOT overwrite or truncate it (as it contains precious history/timeline entries). Instead, patch the file in its current location to insert the standard frontmatter, executive summary, and state sections at the very top, preserving any existing content (like `## Timeline` and its entries) underneath.
3. If the file does not exist in either location, create a new file in the inbox directory `/home/justin.guest/Developer/obsidian-vault/Inbox/<Name>.md` and format the contact note following these strict standards:
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

     ## Timeline
     - <Date> | Discovered — Mentioned in [[<context_file_relative_path_no_ext>|<context_file_title>]].
     ```
4. Report success and confirm creation in the inbox directory.

If no discovered contacts are found, proceed to Phase 3.

---

### Phase 3 — Work Log Draft & Alignment

Draft today's work log, align with Justin, and write it to today's daily note. This step runs towards the end of the wind-down so that any activities, contact creations, log files, or inbox triage completed during previous steps are fully incorporated, ensuring the work log captures the final state of play for the day.

1. **Calculate Dates:**
   - Determine `TARGET_DATE` as today (e.g., `2026-06-07` in local time).
   - Pre-compute timezone offsets dynamically to prevent UTC boundary leakage on calendar searches.

2. **Gather Today's Raw Activities (Fast-track):**
   - **Gather live activity from multiple direct sources:**
     - **Calendar:** Run Google Workspace calendar search with local timezone offset (e.g., `python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account all calendar list --start <YYYY-MM-DD>T00:00:00<OFFSET> --end <YYYY-MM-DD>T23:59:59<OFFSET>`).
     - **Slack:** Run two searches for messages from/to Justin (e.g., `python3 ~/.hermes/skills/social-media/slack/scripts/slack.py search 'from:@justin after:<YESTERDAY_DATE> before:<TOMORROW_DATE>' --limit 50`).
     - **Linear:** Query the Linear GraphQL API via Python's `urllib.request` using `LINEAR_API_KEY` from `~/.hermes/.env` (no "Bearer" prefix) to retrieve issues updated today where Justin is assignee, creator, or subscriber.
     - **Todoist:** Query completed tasks via native `mcp_todoist_find_completed_tasks` (omit `responsibleUser` to include unassigned personal tasks) and any due-today incomplete tasks via `mcp_todoist_find_tasks_by_date`.
     - **Vault Git:** Check git history of the vault to capture manual notes Justin added, modified, or deleted today (e.g., `git -C ~/Developer/obsidian-vault log --since="<YYYY-MM-DD> 00:00:00" --until="<YYYY-MM-DD> 23:59:59" --name-status --pretty=format:"COMMIT:%h|%an|%s"`). Filter out commits from `Bes (bes-vm)` or containing `bes` to isolate Justin's manual edits.
   - Read today's existing Obsidian daily note with `read_file` to see manual notepad entries.
   - Search the vault for any meeting/Granola notes generated today (look in `vault/Meetings/` or files containing today's date in their name).
   - Read the daily briefing cache `/home/justin.guest/.hermes/morning-briefing/<YYYY-MM-DD>.json` to check the `vault_activity` field, and run a quick terminal find command over the vault to gather any high-level vault restructuring, bulk updates, or manual categorization sweeps that took place during the day.

3. **Synthesize the Work Log Draft:**
   - Synthesize the gathered material into a set of clean, structured blocks matching the standard work log format:
     - **Preview Summary:** A highly concise, 1-2 sentence active-voice overview of the day's main focus.
     - **🗓 Schedule & Events:** Chronological bullet list of today's and tomorrow's meetings and events (shared with the Morning Briefing).
     - **✅ Work Log:** Synthesized highlights, bolded decisions (with accurate attribution), open questions/blockers, and accomplishments (completed Todoist tasks, closed Linear issues, git commits, or high-level vault changes).


4. **Present the Draft to Justin:**
   - Deliver the formatted draft in chat.
   - Ask a short, focused question to capture offline context:
     *"Here is the draft of today's work log. Anything else from today that isn't captured here (e.g., side-quests, offline discussions, IRL decisions)?"*
   - **Wait for Justin's response.**

5. **Write the Finalized Work Log:**
   - Combine Justin's feedback with the draft.
   - Find or create today's daily note in `/home/justin.guest/Developer/obsidian-vault/Daily Notes/YYYY-MM-DD Weekday.md` (create from template `/home/justin.guest/Developer/obsidian-vault/Utilities/Templates/daily_note.md` if missing, stripping Templater tags).
   - Overwrite/replace the corresponding headings (`> [!summary]`, `## 🗓 Schedule & Events` for Today's and Tomorrow's events, and `## ✅ Work Log` with subheadings `### 🚀 Highlights & Decisions` and `### 🏆 Accomplishments`) with your new synthesized content.
   - **Crucial:** Preserve the entire content of the `## 🗒 Scratchpad` section (including manual text written by Justin) and the `## 🌄 Morning Briefing` section. Never modify or delete them.
   - Append the sources attribution footer at the very bottom.

---

### Phase 4 — Tomorrow's Calendar Preview & Close-out

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

- **No Project Discovery in Wind-Down:** Never attempt to run live project discovery or suggest project note creations during the wind-down session. Project suggestions are too noisy for this workflow; instead, project entity matching and timeline appends are handled exclusively via the automated ingest pipelines (`integrate-entities`).
- **Preserve the Scratchpad:** Always load today's daily note first, find the `## 🗒 Scratchpad` section, and keep its contents completely intact. If the section doesn't exist, create it under `## 🗒 Scratchpad` instead of overwriting any other sections.
- **Inputs Terminology:** Always refer to Slack threads, emails, and other primary-category sources as "inputs" rather than "logs" in both conversations and note frontmatter, as per the updated vault schema.
- **Accurate Attribution:** When drafting highlights and decisions from emails or meeting notes, ensure decisions are attributed to the correct person (e.g., Anya, Nana, teachers, etc.) rather than assuming Justin made them.
- **Accurate Assumption/Feasibility Status:** Be extremely precise about what has actually been validated versus what remains an open question when drafting research findings. Always bound claims strictly to the scope of what was directly tested.
- **Escape Slack Channels:** Always write `#channel-name` as `\#channel-name` inside the daily note so Obsidian doesn't parse it as a tag.
- **Dynamic Timezone Offset:** When fetching calendar events, always calculate and append the local timezone offset (e.g. `-04:00` or `-05:00`) to `--start` and `--end` to prevent boundary events from leaking from yesterday or tomorrow.
- **Git Commit Warning:** Do not manually `git add` or `git commit` any vault edits. The `bes-vault-sync` watcher will handle it immediately.
- **Todoist Task Creation Rule:** When creating any Todoist task, always add a one-sentence comment immediately after — source + why it became a task.
- **Todoist Filter Preference:** Do not present tasks using native Todoist sidebar views (Today, Inbox, etc.), as Justin finds them cluttered. Emphasize saved filter views.
- **Frontmatter Safety & Infinite Loops:** Avoid extracting body content in a way that includes leading newlines, preventing infinite overwrite loops during hygiene tasks. Always `.lstrip()` body content immediately upon extraction.
- **Dangling Closing Dividers:** Ensure any automated or manual procedure that adds or updates properties writes back the closing divider (`---`) on a *fresh line*. Writing it without an intervening newline will append it directly to the end of the last property string (e.g., `daily_note: '...'---`), which corrupts properties.
- **Non-Unique Aliases Guard:** Always skip auto-linking any alias that is non-unique (shared by more than one distinct contact path) to avoid incorrect connections in the vault.
- **Timelines Deactivation (manual wind-down):** Do not manually append `## Timeline` bullets to contact cards during wind-down; rely on Obsidian's native Backlinks panel instead. **`integrate-entities`** is the sanctioned automated append path for both contacts and projects at ingest time — cron and meeting reconcile use it.

## Verification Checklist

- [ ] All 4 phases completed in strict interactive sequence.
- [ ] Today's Notepad section in the daily note preserved completely intact without modification or truncation.
- [ ] Discovered contacts drafted in the inbox, and existing contact cards updated in place without relocation.
- [ ] Work log draft synthesized with accurate attribution of decisions, and written to today's daily note.
- [ ] Tomorrow's schedule fetched and presented with timezone-aware calendar offsets.
