---
name: morning-briefing
description: "Interactive morning briefing for Justin — runs after the 7AM cron has done background work (work log change-detection, vault hygiene Tier 1, inbox gather). Walks through a multi-phase conversation: work log highlights (skipped if no changes since wind-down), Second Brain vault activity summary, calendar summary, near-term task triage, calendar inbox candidates, general inbox candidates. Load this skill whenever Justin responds to the morning greeting or asks for his morning briefing."
platforms: [linux]
related_skills: [work-log, todoist-inbox-fill, obsidian-vault-hygiene, todoist]
---

# 🌅 Morning Briefing

This skill governs the **interactive phase** of the morning briefing. The 7AM cron runs background jobs and sends a greeting; once Justin responds, load this skill and walk through the phases in order.

## Key files

- **Cache:** `~/.hermes/morning-briefing/YYYY-MM-DD.json` — written by cron, read here
- **Days off:** `~/.hermes/days-off.txt` — personal non-holiday days off
- **Work-day helper:** `python3.12 ~/.hermes/scripts/work_day.py <cmd> [date]`
- **Change detector & vault activity scan:** `python3 ~/.hermes/scripts/check_morning_changes.py`
- **Vault:** `/home/justin.guest/vault` (or `$OBSIDIAN_VAULT_PATH`)

## Entry point

The cron sends: *"Morning, Justin! Ready to start your day?"*

Justin's reply determines the flow:
- **"yes" / any affirmative** → full briefing (all phases)
- **"day off" / "taking the day off" / similar** → skip Phase 1; run Phases 2–5 with personal-only filter
- **no response within the session** → nothing; cron already ran background jobs

## Cache file schema

The 7AM cron writes `~/.hermes/morning-briefing/YYYY-MM-DD.json` with this structure:

```json
{
  "date": "YYYY-MM-DD",
  "is_work_day": true,
  "work_log_dates": ["YYYY-MM-DD"],
  "work_log_status": "ok | error | skipped",
  "vault_hygiene": {
    "tier1_status": "ok | error",
    "tier1_summary": "Moved 2 daily notes.",
    "tier2_issues": [
      "sources/note.md — missing ID",
      "meetings/other.md — malformed ID field"
    ]
  },
  "inbox_candidates": {
    "status": "ok | error | partial",
    "sources_failed": [],
    "calendar_events": [...],
    "action_items": [...]
  },
  "vault_activity": {
    "total_updated": 4,
    "type_counts": {"daily": 1, "concept": 3},
    "added_entities": {
      "person": [{"slug": "Contacts/jeev-sahoo", "title": "Jeev Sahoo"}],
      "company": [],
      "concept": []
    }
  },
  "daily_thought": {
    "path": "Notes/Thoughts on fatphobia 20260128135845.md",
    "title": "Thoughts on Fatphobia",
    "category": "Opinions / Thoughts"
  },
  "discovered_contacts": {
    "people": [
      {
        "name": "Jeev Sahoo",
        "type": "person",
        "context_file": "Logs/Meetings/2026-06-08 Product meeting.md"
      }
    ],
    "organizations": []
  }
}
```

If the cache file doesn't exist (cron failed or hasn't run yet), run the background jobs inline before proceeding. Tell Justin there'll be a brief pause.

### 🔄 Cache Recovery & Inline Execution Steps
1. **Check today's work day status:**
   `python3.12 ~/.hermes/scripts/work_day.py is_work_day`
2. **Find which dates' work logs to summarize:**
   `python3.12 ~/.hermes/scripts/work_day.py logs_to_summarize`
3. **Run the change detection script live:**
   `python3 ~/.hermes/scripts/check_morning_changes.py`
4. **Write the recovery cache file manually:**
   Construct and write the complete JSON cache to `/home/justin.guest/.hermes/morning-briefing/YYYY-MM-DD.json` containing the correct values for `date`, `is_work_day`, `work_log_dates`, `work_log_status` ("skipped" if the target date daily note is already fully populated, "ok" if generated), `vault_hygiene` (run `python3 run_tier1_hygiene.py` inline to get the tier1_summary), `vault_activity` parsed from step 3, and a randomly selected note under `daily_thought` (selected from Thoughts/Opinions, Beliefs, or Sources categories in the vault).
5. **Proceed with Phase 1 presentation:**
   Present Phase 1 highlights/status based on the newly written recovery cache.

## Phase sequence

### Phase 1 — Work log highlights

**Skip entirely if:** `is_work_day` is false OR Justin said "day off" OR `work_log_status` is `"skipped"` in the daily cache file (which means no changes have occurred in the external sources since the wind-down routine / previous work log run).

If `work_log_status` is `"skipped"`, output:
*"I skipped yesterday's work log highlights since nothing changed after your wind-down wrap-up."*
Then, move directly to **Phase 1.5**.

**If `is_work_day` is true and `work_log_status` is NOT `"skipped"`:**

1. Load `work_log_dates` from cache (computed by cron using `work_day.py logs_to_summarize`)
2. For each date in `work_log_dates`, read the `# 📋 Work Log` section from the daily note in vault
3. Synthesize highlights across all dates into a single brief summary

**Format:**
```
📋 Work log — [Day, Mon DD] (or "Fri–Mon" for multi-day spans)

• [2–4 bullet highlights — most important things that happened]
• Decisions: [1–2 if any, otherwise omit]
• Still open: [1–2 blockers/open questions, if any]
```

Keep it scannable. 4–6 bullets max. If multiple days, don't repeat obvious context — synthesize across them. Don't recite every meeting; surface the consequential ones.

If no work log entries exist for the dates (notes missing or no Work Log section), say so briefly and move on. Don't block on it.

**If the user asks you to generate the missing daily note / work log:**
- Gather yesterday's raw materials from Slack, Linear, GWS, and Todoist (using `/home/justin.guest/bes-backup/skills/note-taking/work-log/references/direct_execution.py` or parallel subagents).
- Scan for any other notes written on that date in the vault (e.g. `Notebook/Kennywood Day...` or other files with matching timestamp/daily_note fields) to capture personal context.
- Synthesize them into a complete daily note and work log following the `work-log` skill and the `<vault>/Templates/Daily Note.md` template.
- Write the daily note to the vault archive (`Daily Notes/YYYY-MM-DD DayName.md`).
- Update the morning briefing cache file (`~/.hermes/morning-briefing/YYYY-MM-DD.json`) to set `work_log_status: "ok"`, remove the `work_log_error`, and clear `vault_hygiene` issues if resolved.
- Present the synthesized work log highlights and proceed to Phase 1.5.

After presenting, **wait for acknowledgment or a question** before moving to Phase 1.5. Don't immediately dump everything at once.

---

### Phase 1.5 — Second Brain activity summary

Read the `vault_activity` section from the daily cache file (`~/.hermes/morning-briefing/YYYY-MM-DD.json`).

If the cache file or `"vault_activity"` section is missing or has status `"error"`, run the scan script live to retrieve the summary:
`python3 ~/.hermes/scripts/check_morning_changes.py`

**Format:**
```
🧠 Second Brain — Activity since yesterday morning

• Updated: [N pages across M types, e.g., "1 note, 3 concepts"]

Newly Added:
• People: [List of [[Contacts/slug|Title]] or "None"]
• Companies: [List of [[Contacts/slug|Title]] or "None"]
• Concepts: [List of [[Notes/slug|Title]] or "None"]
```

Keep it concise and beautifully formatted with Wiki-links. If nothing was updated or added, output: *"No second brain updates since yesterday."*

After presenting, **wait for acknowledgment or a question** before moving to Phase 2.

---

### Phase 2 — Calendar summary

Pull today's calendar and look ahead 7 days for anything major. Since the background cache file only stores *candidates* (events not yet on the calendar), you must fetch the actual scheduled events live.

**Sources:** Fetch live from Google Workspace across all accounts (or personal accounts only on non-work days):
- Work and personal: `python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account all calendar list`
- Personal only (weekends/days off): `python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account personal-main,personal-junk calendar list`

**Format:**
```
📅 Today — [Day, Mon DD]

• HH:MM  Event name (attendees if external)
• HH:MM  Event name
[if nothing: "Nothing on the calendar today."]

Coming up this week:
• [Day] Event name — [why it's notable: external attendees / prep needed / important]
[only surface 2–3 notable items, not every standup]
```

**On non-work days (or "day off"):** show personal calendar events only. Skip work account events.

After presenting, wait for acknowledgment before Phase 3.

---

### Phase 3 — Near-term task triage

Query Todoist for tasks with due dates or deadlines in the next 3 days (inclusive of today).

**Rule:** Skip any tasks that are already in the "Now" project, or completed/cancelled tasks.
Only present this if there are matching tasks. If none, skip directly to the next phase.

**Format:**
```
📌 N tasks due or with deadlines in the next 3 days:

1. [Project] Task name (due: Date/Time | deadline: Date)
...

Would you like to move any of these to "Now"?
```

Once Justin selects tasks, move them to the "Now" project.

After presenting and handling any movements, wait for acknowledgment before Phase 4.

---

### Phase 4 — Calendar inbox candidates

Present the calendar event candidates from `inbox_candidates.calendar_events`.

Suggest a target calendar (`work` or `personal-main`) for each candidate based on its source and content (e.g., family/school/personal tasks default to `personal-main`, while SignLab/professional ones default to `work`).

Format:
```
📅 N potential calendar events not yet on your calendar:

1. [Source] Event | when: date/time | calendar: work | context: where found
2. [Source] Event | when: date/time | calendar: personal-main | context: where found
...

Which ones should I add directly to your Google Calendar?
```

If `calendar_events` is empty, say "Nothing new to add to your calendar." and skip to Phase 4.5.

Once Justin confirms selections:
- Schedule/create the events directly on the respective Google Calendar accounts (`work` or `personal-main`) using the calendar write capabilities (`gws_multi.py --account <name> calendar create --summary "..." --start "..." --end "..." --attendees "..." --description "..."`).
- Only create a Todoist "Add to calendar:" task as an exceptional fallback if Justin specifically requests it or if the event timing/date is too ambiguous to schedule directly.
- Report the scheduling confirmation with event details and links, then move to Phase 4.5.

**On non-work days / day off:** still run this phase but filter to personal events only (skip work Slack, work email sources).

---

### Phase 4.5 — Source note candidates

Present potential source note candidates (active Slack conversations and noteworthy primary-category emails from the last 36-48 hours) that Justin hasn't tagged with `🧠` or forwarded to Bes, but that are highly worthy of being turned into notes in his vault.

Run the unified script live to fetch candidates:
`python3 /home/justin.guest/.hermes/scripts/fetch_source_candidates.py`

If candidates (Slack or Email) are found:
- Show them with sequential numbers across both Slack and Email candidates.
- Format:
  ```
  🧠 N potential source notes:

  **Slack Conversations**
  1. [\#channel-name] Topic or Preview — participants: Alice, Bob, Justin
  2. [\#channel-name] Topic or Preview — participants: Endre, Justin

  **Emails**
  3. [Email/<account>] Subject line — from: Sender Name (Date)
  ...

  Would you like to turn any of these conversations into notes in your vault? (e.g. "yes, 1", "save 1 and 3", or "skip")
  ```

If Justin selects any:
1. For each selected item:
   - **For Slack conversations:**
     - Synthesize a high-quality summary showing "who said what" clearly.
     - Use the standard Obsidian note layout for Slack notes (write to `/home/justin.guest/vault/sources/slack/YYYY-MM-DD-slug.md`).
     - Structure the YAML frontmatter for Slack notes:
       ```yaml
       ---
       id: <timestamp_id> # YYYYMMDDHHmmss based on first message
       daily_note: "[[<YYYY-MM-DD-weekday>]]"
       original_url: "<permalink>"
       source: "slack"
       channel: "<channel_name>"
       participants:
         - "Participant Name"
       ---
       ```
     - Append a link and one-sentence gist to today's daily note notepad under `## 🗒 Notepad`:
       `* [[sources/slack/<filename>|Title]]: <One-sentence-gist>.`
     - Run the command to mark it processed:
       `python3 /home/justin.guest/.hermes/scripts/fetch_slack_brains.py --mark-processed <channel_id> <ts>`
   - **For Emails:**
     - Synthesize a high-quality summary of the email thread showing clearly what was discussed, decided, or requested.
     - Use a similar structured layout for Email notes (write to `/home/justin.guest/vault/sources/email/YYYY-MM-DD-slug.md`).
     - Structure the YAML frontmatter for email notes:
       ```yaml
       ---
       id: <timestamp_id> # YYYYMMDDHHmmss based on first email
       daily_note: "[[<YYYY-MM-DD-weekday>]]"
       original_url: "<permalink>"
       source: "email"
       account: "<work | personal-main>"
       participants:
         - "Sender Name"
       ---
       ```
     - Append a link and one-sentence gist to today's daily note notepad under `## 🗒 Notepad`:
       `* [[sources/email/<filename>|Email discussion]]: <One-sentence-gist>.`
     - Run the command to mark it processed:
       `python3 /home/justin.guest/.hermes/scripts/fetch_source_candidates.py --mark-email-processed <thread_id>`
   - Report the note(s) successfully saved.

If no candidates are found, skip this phase entirely and proceed to Phase 4.7.

---

### Phase 4.7 — Discovered Contacts & Organizations

Present any discovered contacts or organizations (unresolved wikilinks found by the `check_vault_signals.py` script) from today's cache file (`discovered_contacts` field).

If no discovered contacts are found in the cache, skip this phase entirely and proceed to Phase 5.

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
     daily_note: "[[<YYYY-MM-DD-weekday>]]" # e.g. [[2026-06-09-tuesday]]
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

---

### Phase 5 — Inbox candidates

Present the action-item candidates from `inbox_candidates.action_items`.

Use the format from `todoist-inbox-fill` Step 4 Section B — semantically batched groups:
```
📥 N potential inbox items:

**[Group label]**
1. [Source] Task description
2. [Source] Task description

**[Group label]**
3. ...

Which ones should I add?
```

If `action_items` is empty, say "Inbox looks clear." 

Once Justin confirms → batch-add to Todoist Inbox with comments.

**On non-work days / day off:** filter out work-sourced tasks (Linear, work email, work Slack). Keep home/family/personal ones.

---

### Phase 6 — Daily Thought

Present a random note (the Daily Thought) from the Thoughts (Opinions), Beliefs, or Sources categories. This should ideally be loaded from the cache file's `"daily_thought"` field. If the cache is missing this field, select a random `.md` file with `category: "[[Thoughts]]"`, `category: "[[Beliefs]]"`, or `category: "[[Sources]]"` from the vault, and display its title, category, and full content.

Make sure it is clear which category the Daily Thought comes from (e.g., Opinions/Thoughts, Beliefs, or Sources).

**Format:**
```
💡 Daily Thought — [[<relative_path_no_extension>|Title]] (<Category>)

[Full content of the note - keeping it markdown-formatted]

---
Would you like to make any edits to this note, or are we set for today?
```

If Justin requests an edit to the note, use the `patch` or `write_file` tool to apply his changes, and confirm.

After Phase 6 is complete, proceed to the "After all phases" wrap-up.

---

### After all phases

If vault hygiene Tier 2 issues exist in the cache, append a brief report at the end:

```
🗂 Vault hygiene — N items to look at when you have a moment:
• sources/some-note.md — missing ID
• ...
```

Don't block on this or ask for immediate action. It's informational.

Then close out: *"That's everything. Have a good [day/weekend/Monday]."* (Match the day.)

---

## Work-day detection quick reference

```bash
# Is today a work day?
python3.12 ~/.hermes/scripts/work_day.py is_work_day

# Which dates' work logs to summarize today?
python3.12 ~/.hermes/scripts/work_day.py logs_to_summarize

# Previous work day
python3.12 ~/.hermes/scripts/work_day.py prev_work_day
```

US federal holidays auto-detected. Personal days off in `~/.hermes/days-off.txt` (one YYYY-MM-DD per line, # comments ok).

---

## Tone and pacing

- One phase per message. Don't dump everything at once.
- Wait for acknowledgment between phases. Justin may want to ask a question or act on something before moving on.
- Keep each phase message short. The briefing should feel like a quick check-in, not a wall of text.
- Match energy to day: Monday morning gets a slightly warmer opener; Friday gets a brief "anything to wrap up this week?" at the end if there are open blockers.
- On weekends / days off: lighter, shorter, personal focus only.

---

## Pitfalls

- **Child name or grade misattribution.** Do not guess or assume which child a school event (like a graduation, potluck, or class celebration) belongs to. Always verify school grades and ages against the user profile (e.g., Jamie is in 5th grade/G5, Sam is in 6th grade/G6) before writing descriptions or adding summaries.
- **Decision misattribution.** When summarizing work logs or calendar updates, do not attribute decisions made by others (colleagues, family members, teachers) to Justin. Always explicitly credit the actual decision-maker.
- **Don't re-run background jobs if the cache is fresh.** Check the cache first. Only re-run if the file is missing or >4h old.
- **Work log section header is `# 📋 Work Log`** in the daily note. If it's absent, the note may not have been logged yet — say so, don't silently skip.
- **Multiple work-log dates:** synthesize, don't concatenate. Justin doesn't want to read Friday's full log on Monday — he wants the 3-line version.
- **Calendar dedup is against the full 30-day snapshot** already in the cache. Don't re-fetch unless you need to.
- **"Day off" filter applies per-phase.** Check it before each phase, not just once at the top.
- **Vault hygiene is never blocking.** Always put it last, always frame it as "when you have a moment."
- **Concept of the Day vs Daily Thought.** Since the migration away from gbrain, concepts no longer exist as a standalone category directory in the vault. Always select the "Daily Thought" from the superset of Thoughts, Beliefs, or Sources categories, and represent the Thoughts category as "Opinions / Thoughts" to align with the user's preference.
- **Do not read the `.env` credential file directly.** The agent running under cron cannot read `${HERMES_HOME:-$HOME/.hermes}/.env` using direct file tools (like `read_file`) due to defense-in-depth safety blocks. Always run terminal commands with `.env` sourced in the shell context (`source ${HERMES_HOME:-$HOME/.hermes}/.env && python3 ...`) or rely on the host environment, rather than attempting to read/parse the credential file.
- **Concept of the Day directory has changed.** Following the migration away from gbrain, concept files are located in `/home/justin.guest/vault/Notes/` instead of `/home/justin.guest/vault/concepts/`. Identify them by searching for markdown files containing `type: concept` or `type: "concept"` in their frontmatter, and completely avoid querying any deprecated `concepts/` directory.
