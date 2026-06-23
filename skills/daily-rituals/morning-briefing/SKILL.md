---
name: morning-briefing
description: Use when generating or managing Justin's daily morning briefing report. Governs the structure, section ordering, and data-retrieval methods for the simplified, single-message 5AM briefing.
version: 2.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [briefing, morning, report, calendar, todoist]
    related_skills: [work-log, todoist, obsidian]
---

# 🌅 Morning Briefing

## Overview
This skill governs the automated generation of Justin's morning briefing. It is run daily as a scheduled cron job at 5:00 AM, reading cached data compiled by the 4:00 AM caching run and performing live queries for real-time calendar and task status.

## When to Use
* **Scheduled Cron Run:** Executed daily at 5:00 AM to generate the morning briefing message.
* **Manual Request:** Used when Justin explicitly asks "give me my morning briefing" or "show today's overview".

## Report Structure
The briefing is delivered as a **single, unified message** containing exactly five sections in the following strict order, followed by an interactive follow-up question.

### 1. Calendar Preview
* **Timeframe:** Show scheduled events for **today and tomorrow only**.
* **Method:** Retrieve scheduled events live across all calendar accounts to ensure accuracy:
  ```bash
  python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account all calendar list
  ```
* **Formatting:** Group by day (Today vs. Tomorrow). For each event, show:
  * Time range (e.g., `08:30 - 09:00`)
  * Event summary
  * Target calendar account in brackets (e.g., `[work]` or `[personal-main]`)
  * Bulleted notes for notable events (e.g., campers' camps, specific child details).
* **Zero-state:** If a day is empty, print *"Nothing on the calendar."*

### 2. Summary of Yesterday's Work Log
* **Method:** Locate the daily note for the previous workday under `/home/justin.guest/Developer/obsidian-vault/Daily Notes/`.
  * Note: Use `python3.12 ~/.hermes/scripts/work_day.py logs_to_summarize` to identify the correct date to summarize (e.g., summarizing Friday's log on a Monday).
* **Content:** Extract the content of the work log (under `# 📋 Work Log` or `## 🚀 Highlights & Decisions`).
* **Synthesis:** Compile a tight, 3–4 bullet point summary focusing on core accomplishments, key decisions, and blockers. Do **not** copy the full log verbatim.
* **Zero-state:** If the note or work log section is missing, note the omission and proceed.

### 3. High-Urgency Tasks and Inbox Candidates
* **Todoist Live Check:** Fetch live tasks due today or overdue.
  * *Constraint:* Exclude tasks already in the "Now" project, or completed/cancelled tasks.
* **Linear Live Check:** Fetch assigned open issues due today or marked high-priority.
  * *Constraint:* Exclude issues with statuses of type Triage, Backlog, Completed, or Canceled.
* **Inbox Candidates:** Read `inbox_candidates.action_items` from the morning cache file (`~/.hermes/morning-briefing/YYYY-MM-DD.json`).
  * *Crucial Safety Rule:* If `inbox_candidates.action_items` is empty, do **not** fall back to reading `gather_run.json`. An empty array means the inbox is genuinely clear.
* **Formatting:** Group clearly into **Todoist**, **Linear**, and **Potential Inbox Items** (if any candidates are present).

### 4. Calendar Candidates
* **Source:** Read `inbox_candidates.calendar_events` from the morning cache file (`~/.hermes/morning-briefing/YYYY-MM-DD.json`).
* **Formatting:** List each candidate showing source, time, and suggested calendar (`work` or `personal-main`).
* **Zero-state:** If empty, print *"Nothing new to add to your calendar."*

### 5. Morning Thought
* **Source:** Read the pre-selected thought from `daily_thought` in the cache file (`YYYY-MM-DD.json`).
* **Fallback Selection:** If the cache or field is missing, randomly select a markdown file containing `category: "[[Thoughts]]"`, `category: "[[Beliefs]]"`, or `category: "[[Concepts]]"` from the vault directory `/home/justin.guest/Developer/obsidian-vault/Notes/`.
* **Formatting:** Display as:
  `💡 Morning Thought — [[Notes/file_name|Title]] (Category)`
  followed by the full note content wrapped in a blockquote (`>`).

---

## Closing Question
End the briefing with this exact prompt to hand control back to Justin:
*"Would you like me to make any edits, schedule any of these candidates, or do you have any follow-up questions or requests?"*

## Common Pitfalls
1. **Including Vault Hygiene:** The Vault Hygiene section has been completely removed from the briefing report. Do not append or include it under any circumstances.
2. **Interactive Phasing:** Do not wait for acknowledgment between sections. Deliver the entire briefing as a single, well-structured message.
3. **Stale Inbox Candidates:** Verify live task/issue status rather than blindly repeating stale cache values.
4. **Incorrect Date Synthesis:** Ensure that weekends and holidays are handled correctly. Always summarize the previous *workday's* work log.

## Verification Checklist
- [ ] Briefing is delivered as a single message.
- [ ] Vault Hygiene section is completely absent.
- [ ] Sections are ordered exactly: Calendar Preview, Yesterday's Work Log, Urgency & Inbox, Calendar Candidates, Morning Thought.
- [ ] Closes with the interactive follow-up question.
