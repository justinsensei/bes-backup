---
name: bes-email-dispatch
description: Process an email that Justin forwarded to goff.justin+bes@gmail.com — parse the inline instruction (first line of body or subject prefix), turn the email into the right kind of Obsidian artifact (note, Person note update, append to existing note, ad-hoc judgment), and report back to Telegram. Read-only on Gmail.
version: 1.2.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [email, gmail, obsidian, dispatch, polling]
    related_skills: [google-workspace, obsidian, llm-wiki, polling-cron-agent]
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

## Action 1: File Email (Save to Vault Inbox)

### Trigger Keywords
- Contains: `File this`, `file this`, `file`, `save this`, `save`, `archive this`
- Or: Instruction is **empty / none** (default fallback, files to `inbox/`)

### Storage Destination
- Create a new markdown note inside the **`inbox/`** directory of his vault:
  `/home/justin.guest/vault/inbox/YYYY-MM-DD-subject-slug.md`
  *(Where `YYYY-MM-DD` is the current date or forwarded email date, and `subject-slug` is a cleaned, lowercase, hyphen-separated version of the cleaned subject).*

### Note Structure & Frontmatter
All new notes must start with the `New Note` frontmatter (pre-evaluating Templater values at write time using Justin's local time (America/New_York)):

```yaml
---
id: "<YYYYMMDDHHmmss at write time, e.g. 20260520143157>"
daily_note: "[[<YYYY-MM-DD Weekday>|YYYY-MM-DD Weekday]]"
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

## Action 1b: Log Email (Save to Inputs/Emails/)

### Trigger Keywords
- Contains: `log this`, `log email`, `log thread`, `save as email log`, `log`

### Storage Destination
- Create a new markdown note inside **`Inputs/Emails/`** (`$OBSIDIAN_VAULT_PATH/Inputs/Emails/YYYY-MM-DD - Spaced Subject.md`)
  *(Where `YYYY-MM-DD` is the current date, and `Spaced Subject` is a cleaned, capitalized, spaced version of the subject).*

### Note Structure & Frontmatter
All new email log notes must start with this frontmatter format:

```yaml
---
id: "<YYYYMMDDHHmmss at write time>"
daily_note: "[[<YYYY-MM-DD Weekday>|YYYY-MM-DD Weekday]]"
category: "[[Emails]]"
type: email
original_url: "<Gmail message search link, e.g. https://mail.google.com/mail/u/0/#search/rfc822msgid:<Message-ID> or search query>"
---
```

Below the frontmatter, format the note body cleanly:
1. **Title:** Large H1 heading `# 📧 Email Log: [Cleaned Subject]`
2. **Email Metadata:** Labeled key-value pairs:
   - **From:** [Original Sender Name <Email>]
   - **Date:** [Original Email Date]
   - **Subject:** [Cleaned Subject]
   - **Message ID:** [Gmail Message ID] (to fetch full email if needed)
3. **Context Note:** If Justin provided any instruction or extra thoughts, include them in a `## Context` section.
4. **Summary:** Add a brief summary of the entire thread (concise bullets or paragraph outlining key discussions, decisions, and action items — **do not copy the email contents verbatim**).

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
- **Person note:** *"Person note for <Name>"* or *"<Name> works at <Org>"* → Create a brand-new Person note named `<Capitalized Spaced Full Name>.md` in `/home/justin.guest/vault/inbox/` (or update the existing note in-place if it already exists under `/Contacts/` or `/inbox/`).
- **Company/Organization note:** *"New company <Name>"*, *"Company note for <Name>"*, or *"<Name> is a new company"* → Create a brand-new Organization note named `<Capitalized Spaced Name>.md` in `/home/justin.guest/vault/inbox/` (or update the existing note in-place if it already exists under `/Contacts/` or `/inbox/`).
- **Project note:** *"New project <Name>"*, *"Project note for <Name>"*, or *"<Name> is a new project"* → Create `<lowercase-name-slug>.md` under `projects/` using Project formatting (executive summary, Status: Active, and creation Timeline).
- **Append to existing note:** *"Add to <note title>"*, *"Append to <note title>"*, or *"Add [content] to the <note title> note"* → Find the closest match vault-wide (the user may say "in my inbox" or guess the wrong folder, but the note often resides in its correct MECE directory like `personal/trips/` or `projects/`) and append a dated bullet point (format: `- YYYY-MM-DD | Ingest — <context/details>`).
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
   - If filing: Generate and write the markdown note to `inbox/` or `Inputs/Emails/`.
   - After filing, run `llm-wiki` integrate-light (log + index + daily notepad).
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

## Troubleshooting & Pitfalls

- **Empty plaintext parts in HTML emails:** Some systems/senders (like Expedia transactional emails) send `multipart/alternative` messages with a nearly empty text/plain part containing only `\r\n` (whitespace). Because `google_api.py` previously checked `if not body:`, this truthy whitespace caused it to skip extracting the actual HTML content. Always ensure `google_api.py` checks `if not body.strip():` when extracting bodies to correctly fall back to the rich HTML content.
