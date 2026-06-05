---
name: bes-email-dispatch
description: Process an email that Justin forwarded to goff.justin+bes@gmail.com — parse the inline instruction (first line of body or subject prefix), turn the email into the right kind of Obsidian artifact (note, Person note update, append to existing note, ad-hoc judgment), and report back to Telegram. Read-only on Gmail.
version: 1.1.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [email, gmail, obsidian, dispatch, polling]
    related_skills: [google-workspace, obsidian, polling-cron-agent]
---

# Bes Email Dispatch

Handler skill for the email-forwarding workflow. Justin forwards an email to `goff.justin+bes@gmail.com` with a one-line instruction at the top of the body (or just a subject prefix); a Gmail filter labels it `Bes/Inbox`; a poller (`poll_bes_inbox.py`) detects it and invokes this skill once per new message ID.

This skill is **read-only on Gmail**. It never archives, marks read, or replies. The source of truth for "has Bes seen this?" is the watermark file (`~/.hermes/state/bes-inbox-watermark.json`), not Gmail label state.

## Inputs

One Gmail message ID. The poller passes it via the cron prompt; you call `scripts/load_context.py <id>` to fetch.

## Core Principle: Tweakable Dual-Action Dispatch

When Justin forwards an email, he wants one of two actions (or sometimes both) to happen based on keywords and context in his one-line instruction (`instruction` field from `load_context.py`):

1. **Add the email to his Obsidian Vault (File it)**
2. **Create a Todoist task based on the email (Task it)**

For each action, Justin will include keywords and some context on the instruction line, for example:
- *File this. I like the idea about the flux capacitor. I wonder if we could use it for the improbablity engine.*
- *Task due Friday. Gotta finish the book before the weekend.*
- *TODO due tomorrow. Check with Anya.*

If his instruction contains keywords for **both** (or if he lists them on separate lines/sentences), you must perform **both** actions!

See [references/forwarding-examples.md](references/forwarding-examples.md) for concrete mockups of instruction inputs and expected tool outputs.

### Default Behavior (Fallback)
If the instruction is empty, has no keywords, or is just "Save as a note", default to **Action 1: Add the email to his vault**.

---

## Action 1: File Email (Save to Vault)

### Trigger Keywords
- Contains: `File this`, `file this`, `file`, `save this`, `save`, `archive this`
- Or: Instruction is **empty / none** (default fallback)

### Storage Destination
- Create a new markdown note inside the **`inbox/`** directory of his vault:
  `/home/justin.guest/vault/inbox/YYYY-MM-DD-subject-slug.md`
  *(Where `YYYY-MM-DD` is the current date or forwarded email date, and `subject-slug` is a cleaned, lowercase, hyphen-separated version of the cleaned subject).*

### Note Structure & Frontmatter
All new notes must start with the `New Note` frontmatter (pre-evaluating Templater values at write time using Justin's local time (America/New_York)):

```yaml
---
id: "<YYYYMMDDHHmmss at write time, e.g. 20260520143157>"
daily_note: "[[<YYYY-MM-DD dddd at write time, e.g. 2026-05-20 Wednesday>]]"
---
```

Below the frontmatter, format the note body cleanly:
1. **Title:** Large H1 heading `# [Cleaned Subject]`
2. **Email Metadata:** Labeled key-value pairs:
   - **From:** [Original Sender Name <Email>]
   - **To:** [Recipient Email]
   - **Date:** [Original Email Date]
3. **Context Note:** If Justin provided an instruction or extra thoughts (e.g., "I like the idea about the flux capacitor..."), include them in a `## Context` section.
4. **Summary:** Add a concise markdown summary of the email's content (who sent it, what it is about).
5. **Email Content:** A `---` line or `## Email Content` header followed by the cleaned plaintext body of the forwarded email.

---

## Action 2: Create a Todoist Task

### Trigger Keywords
- Contains: `Task`, `task`, `TODO`, `todo`, `to do`, `To do`

### Task Creation Specifications
Use `mcp_todoist_add_tasks` to add a single task to Justin's Todoist **Inbox** (projectId: `"6VGcQ7r6HW5r87j9"` or `"inbox"`):

1. **Task Name (`content`):** Determine a meaningful, clear, actionable name based on the email's subject and summary. Do NOT use the raw `Fwd: ...` subject or a generic name.
2. **Task Description (`description`):** Append whatever contextual note Justin has given you to the end of the task description (e.g. `Gotta finish the book before the weekend.`).
3. **Due Date (`dueString`):** Extract any due date specified in the instruction (e.g., "due Friday", "due tomorrow", "due 6/15"). Pass this as the `dueString` parameter of the task. If no due date is mentioned, omit the `dueString` parameter.
4. **Comment on Task:** After creating the task, immediately call `mcp_todoist_add_comments` to add a comment containing a concise summary of the email, including the original sender, recipient, and date. This keeps the task neat while preserving the original context.

---

## Other Intent Shapes (Legacy Support)

If Justin explicitly uses the following phrasing, support these specific paths:
- **Person note:** *"Person note for <Name>"* or *"<Name> works at <Org>"* → Create/update `<lowercase-fullname-slug>.md` under `people/` using `New Person` frontmatter format.
- **Append to existing note:** *"Add to <note title>"* or *"Append to <note title>"* → Find the closest match and append a dated bullet point.
- **Calendar scheduling:** *"Schedule this"* or *"Add this to my calendar"* → Parse event details and call `gws_multi.py --account personal-main|work calendar create`.

---

## Process Workflow

For each message ID detected by the poller:

1. **Load context:** Run `load_context.py <MESSAGE_ID>` to get the JSON email payload.
2. **Determine intents:** Scan the `instruction` string for trigger keywords to decide if you need to:
   - File the email to Vault (`File this` / `save` / empty)
   - Create a Todoist task (`Task` / `TODO` / `to do`)
   - Or both!
3. **Execute actions:**
   - If filing: Generate and write the markdown note to `/home/justin.guest/vault/inbox/`.
   - If creating a task: Call `mcp_todoist_add_tasks` and then `mcp_todoist_add_comments` with the email summary.
   - If both: Do both operations.
4. **Report back:** Output a single concise line per email in your final response (for Telegram delivery):
   - `✅ <subject snippet> → filed to vault and created Todoist task "<task_name>"`
   - `✅ <subject snippet> → filed to vault as <filename>.md`
   - `✅ <subject snippet> → created Todoist task "<task_name>"`
   - `❌ <subject snippet> → load_context failed (is_real=false). Skipping.`

---

## Guidelines & Rules

- **Verify Writes:** After writing any note to the vault, verify the file exists and is non-empty before reporting success.
- **Avoid Loop Guards:** Skip any emails sent by Bes himself to prevent infinite loops.
- **Rate Limit:** Limit processing to at most 5 emails per cron tick. If there are more, report that the rest will be picked up next tick.
