---
name: bes-email-dispatch
description: Process an email that Justin forwarded to goff.justin+bes@gmail.com — parse the inline instruction (first line of body or subject prefix), turn the email into the right kind of Obsidian artifact (note, Person note update, append to existing note, ad-hoc judgment), and report back to Telegram. Read-only on Gmail.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [email, gmail, obsidian, dispatch, polling]
    related_skills: [google-workspace, obsidian, polling-cron-agent]
---

# Bes Email Dispatch

Handler skill for the email-forwarding workflow. Justin forwards an email to `goff.justin+bes@gmail.com` with a one-line instruction at the top of the body (or just a subject prefix); a Gmail filter labels it `Bes/Inbox`; a poller (`poll_bes_inbox.py`) detects it and invokes this skill once per new message ID.

This skill is **read-only on Gmail**. It never archives, marks read, or replies. The source of truth for "has Bes seen this?" is the watermark file (`~/.hermes/state/bes-inbox-watermark.json`), not Gmail label state — so Justin can archive or re-label freely without confusing the agent.

## Inputs

One Gmail message ID. The poller passes it via the cron prompt; you call `scripts/load_context.py <id>` to fetch.

## Process

For each message ID:

1. **Load context** — `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/note-taking/bes-email-dispatch/scripts/load_context.py <MESSAGE_ID>`. Returns JSON with:
   - `id`, `subject`, `subject_clean`, `from`, `to`, `date` — raw email fields (`subject_clean` strips `Fwd:`/`Re:`)
   - `body_text` — plaintext body (HTML auto-stripped if the email was HTML-only)
   - `body_is_html` — true if the original was HTML
   - `forwarded_from` — best-effort sender of the original email (parsed from `---------- Forwarded message ----------` blocks)
   - `forwarded_subject` — best-effort original subject
   - `forwarded_body` — the original email body with the forwarding wrapper stripped
   - `instruction` — Justin's free-form instruction, parsed from the top of the body (everything BEFORE the first forward marker, with quoted reply markers stripped, capped at 600 chars)
   - `instruction_source` — `"body"` (parsed from body), `"subject"` (subject after stripping `Fwd:` had a `[tag]` prefix), or `"none"` (no instruction found → default behavior)
   - `is_real` — `false` if loader couldn't fetch the message (deleted, wrong account, scope error). Skip if false.

   **Note:** if `instruction_source` is `"none"`, default to "save as note." Don't try to extract intent from the email body itself — Justin's instruction lives at the top of the forward, not inside the original message.

2. **Decide intent**. The instruction is free-form, so use judgment. Common shapes:

   | Shape of instruction | Action |
   |---|---|
   | "Save as a note" / "Save this" / "Note this" / empty | Create a new note at the **root of the vault** titled from the original subject |
   | "Person note for <Name>" / "Add to <Name>'s page" / "<Name> works at <Org>" | Create or update a person note at the **root of the vault** (see Person notes below) |
   | "Add to <existing note>" / "Append to <title>" | Find the closest matching note by title; append under a dated heading **in whatever folder the note already lives in** (do not move the note) |
   | "Summarize and …" / free-form prose | Use judgment. The instruction is authorization to do reasonable, reversible things in the vault. |

3. **Write to vault**. Vault path is `/home/justin.guest/vault` (also in `$OBSIDIAN_VAULT_PATH`). The vault syncs to Justin's Macbook via the watcher (see `vm-hermes-vault-sync` skill) — your writes show up on his iPad within a minute or two.

   **All new notes land at the root of the vault.** Sorting into subfolders is a distinct flow Justin handles himself. The vault has subfolders (`Notebook/`, `Daily Notes/`, `Granola/`, `Meetings/`, `References/`, `Attachments/`, etc.) but they exist for Justin's manual organization, not as agent write targets.

4. **Report**. One concise line per processed message in your final response, suitable for Telegram delivery:
   - `✅ <subject snippet> → created <filename>.md (instruction: <verbatim or "default save">)`
   - `✅ <subject snippet> → updated <Name>.md (added: <one-sentence summary>)`
   - `⚠ <subject snippet> → ambiguous instruction "<text>"; saved to <filename>.md and flagged in body`
   - `❌ <subject snippet> → load_context failed (is_real=false). Skipping.`

## Vault layout conventions

**All new notes go to the root of the vault.** Justin sorts manually — pre-sorting into folders is the wrong move because it competes with his organizational flow.

- **New note ("Save as note", default, or no instruction)** → root, filename `YYYY-MM-DD <Subject>.md` (subject cleaned of `Fwd:` and trimmed to ~60 chars; sanitize illegal filename characters: `/ \ : * ? " < > |`).
- **New person note** → root, filename `<Full Name>.md`. Look for an existing match case-insensitively first; if a match exists with slightly different formatting, append to the existing one rather than creating a duplicate.
- **Append to an existing note** → use that note's current location, do not move it. If the title match is ambiguous (multiple plausible matches), pick the closest and mention the chosen path in the report; if no match, fall back to creating a new note at root and note that in the report.
- **Filename collision** → if `YYYY-MM-DD <Subject>.md` already exists, append a short numeric suffix (`YYYY-MM-DD <Subject> 2.md`). Never overwrite.

## Person note shape

When creating or updating `<Name>.md` at the root of the vault:

```markdown
---
name: <Full Name>
type: person
created: <YYYY-MM-DD>
---

# <Full Name>

<role/affiliation summary if known>

## Email captures

### <YYYY-MM-DD> — <original subject>

> From: <forwarded_from> · To: <forwarded_to if present>
> Instruction: <Justin's instruction, verbatim>

<concise extracted facts: who, what, when, where, contact info, dates mentioned>

<optional: short quoted snippet of the original email if it's information-dense>
```

When updating, **append** a new `### <date> — <subject>` block under `## Email captures`. Do not edit prior blocks.

## Default note shape (when "Save as note" or no instruction)

Filename: `<YYYY-MM-DD> <subject>.md` at the **root of the vault**.

```markdown
---
source: email
forwarded_from: <forwarded_from>
forwarded_subject: <forwarded_subject>
captured: <YYYY-MM-DD HH:MM>
instruction: <Justin's instruction or "default save">
---

# <subject (cleaned)>

> Forwarded by Justin from <forwarded_from>
> <forwarded_date if present>

<the original email body, cleaned of HTML/quoted-reply chains where reasonable>
```

## When to NOT act

- `is_real == false` from load_context → just log and skip.
- Instruction is wildly outside the email's content (e.g. "delete my whole vault") → save the email as a default note and flag for review. The mention is authorization for reversible vault operations, NOT for destructive ones.
- Body looks like Bes himself sent the original (loop guard) — if `from` matches Justin's own addresses but content looks like a Bes confirmation, skip. The poller should filter most of these, but double-check.

## Rate limit

Designed for ≤ a few emails per cron tick. If the queue is suspiciously long (>10 new messages in one tick), process the first 5, then return early with a note that the rest will be picked up next tick.

## Verification

After writing, verify the file exists and is non-empty before reporting success. Cheap insurance against partial writes.
