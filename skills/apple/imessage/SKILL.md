---
name: imessage
description: Use when working with imessage. Read recent iMessages from a Justin-curated
  allowlist of 13 chats via SSH proxy to the Mac Mini host. Read-only; cannot send.
version: 2.0.0
author: Hermes Agent (Bes customization)
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - iMessage
    - SMS
    - messaging
    - macOS
    - Apple
    - read-only
    - ssh-proxy
prerequisites:
  commands:
  - ssh
---

# iMessage (Bes — Read-Only Proxy)

> **⚠️ READ-ONLY, ALLOWLISTED ACCESS (Bes-specific customization)**
>
> This is NOT the upstream `imessage` skill. Bes runs inside a Lima VM and cannot
> reach macOS Messages directly. Instead, Justin set up an SSH forced-command on the
> Mac Mini host that exposes ONLY three verbs against an allowlist of 13 chats.
>
> **You CAN:** list allowlisted chats, read recent messages from one chat, read recent
>              messages across all allowlisted chats.
>
> **You CANNOT:** send messages, see chats not on the allowlist, read attachments
>                 not surfaced by the proxy, modify anything.
>
> **If Justin asks Bes to text someone:** explain that this account is read-only,
> and the action would have to happen on the host directly (e.g. via Justin's host
> Hermes agent, or by Justin from his phone). Don't try to send; the SSH key
> doesn't have that capability — the attempt will be rejected by the forced-command
> wrapper, not silently fail.
>
> The OTHER Hermes agent on the host has the full read+send `imessage` skill.
> The two skills are intentionally divergent — do not copy this one to the host,
> and do not assume the host's skill describes Bes's actual capabilities.

## When to Use

- Justin references a text he received and wants Bes to act on it (e.g. "what did Nana text me", "log the prescription pickup from CVS")
- Justin asks to summarize recent family/personal-chat activity
- A task creation in Todoist or work-log entry obviously stems from something that came in by text — verify the source before fabricating details
- Justin asks "did anyone text me about X" — `recent-all` with a tight `--since`

## When NOT to Use

- Anything work-related (work chats are not in the allowlist by design — that's Hermes's territory, not Bes's)
- 2FA codes, banking texts, anything from short-codes other than `27104` (prescriptions). The allowlist excludes these, and the host wrapper additionally enforces a `deny_senders` filter.
- Sending replies. Out of scope; the SSH key has no send capability. If Justin wants to reply, he does it himself or asks Hermes (on the host) to draft and send.

## The Three Verbs

All invocations go through the SSH alias `mac-host`. The wrapper on the host
parses `$SSH_ORIGINAL_COMMAND`, so quote-passing is straightforward.

### `chats` — list allowlisted chats

```bash
ssh mac-host bes-imsg chats
```

Returns JSON `{"chats": [{"chat_id": N, "label": "Friendly Name"}, ...]}`. Use
this to remind yourself which chats are accessible and what their IDs are. Cheap
call; doesn't touch the Messages DB.

### `recent` — read one chat

```bash
ssh mac-host bes-imsg recent --chat-id N [--limit L] [--since DURATION]
```

- `--chat-id N` — must be one returned by `chats` (others are rejected exit 2)
- `--limit L` — 1 to 200, default 50
- `--since DURATION` — `30m`, `2h`, `7d` (max 30d)

Returns JSON `{"chat_id": N, "label": "...", "messages": [...]}`. Each message
has `text`, `sender` (phone or email handle, NOT masked), `created_at` ISO
timestamp, `is_from_me: false` (Justin's outgoing texts are filtered out — Bes
never sees them).

### `recent-all` — sweep across the allowlist

```bash
ssh mac-host bes-imsg recent-all [--limit L] [--since DURATION]
```

Returns JSON `{"chats": [{...}, {...}, ...]}`, one entry per allowlisted chat
that had matching messages. Skips empty chats. **Use a tight `--since`** (e.g.
`24h` or `48h`) — wider windows pull a lot of family-chat noise and burn tokens.

## The Allowlist

Bes can read from these 13 chats:

1. **Nana** (1-1)
2. **Nana & Kathy**
3. **The Seal Appreciation Society** (group: Nana, goobler, Rosa, Sam)
4. **The Fam** (extended family group)
5. **27104 (prescriptions)** — CVS pickup notices and similar
6. **Andy, Pat, Meghan, and Kathy** (siblings group)
7. **Rosa Goff** (1-1)
8. **Sam Goff** (1-1)
9. **goobler (Jamie)** (1-1)
10. **Rosa, Sam, goobler** (sibling group)
11. **Nana & Sam**
12. **Nana & Rosa**
13. **Nana & goobler**

The allowlist file lives on the host at `~/.local/share/bes/imsg/allowlist.json`.
**Bes cannot modify it.** If Justin asks to add or remove a chat, tell him the
change has to be made on the host filesystem, then ask Hermes (the host agent)
to apply it OR direct him to edit the file himself.

## Identifying senders

Senders come back as raw phone numbers or email addresses (e.g. `+14129958896`,
`samgoff1122@gmail.com`). Justin's contacts:

- `+14129958896` = **Nana** (phone)
- `nana.massie@gmail.com` = **Nana** (email — used in some older threads)
- `rosagoff0516@icloud.com` = **Rosa**
- `samgoff1122@gmail.com` = **Sam**
- `jamesgoff0508@gmail.com` = **goobler** (Jamie)
- `+141****5283` last-4 5283 = **Kathy**
- `+141****2726` last-4 2726 = **Meghan**
- `+141****0192` last-4 0192 = **Andy**
- `+141****5811` last-4 5811 = **Pat**
- `27104` = CVS prescription shortcode

In group chats, infer who's speaking from the `sender` field. When citing a
message to Justin, USE THE FRIENDLY NAME ("Nana", not "+14129958896"). Justin
doesn't think about phone numbers.

## Chaining with other skills

Common workflows:

- **"Make a Todoist task for what Tom asked"**: `recent --chat-id 56` (goobler / replace with right id), find the relevant message, then use `productivity/todoist` to create a task. Reference the source briefly in the task description ("Per Jamie text Tue 2pm: …").
- **"What did I miss while I was offline?"**: `recent-all --since 12h` (or however long), summarize per-chat with friendly names.
- **"Log my call with Mom"** style work-logging: if the conversation context implies a text led to the call, fetch the text first to ground the log entry.

## Rules

1. **Do not invent message content.** If `recent` returns nothing for the window asked, say so. Don't fabricate plausible-sounding texts.
2. **Do not claim to have sent anything.** Bes has no send capability via this tool.
3. **When summarizing groups, attribute messages.** Family chats have many speakers; "someone in The Fam said X" is much less useful than "Pat in The Fam said X".
4. **Respect Justin's filter:** if a sender appears in the response that smells like a bank, carrier, 2FA service, or other deny_senders category, treat it as suspect — the host wrapper *should* have stripped it, but flag any escapes to Justin.
5. **Use friendly labels in user-facing output.** Phone numbers and email handles are for internal disambiguation only.

## Example Workflow

**Justin: "Did Nana text me anything about Sunday?"**

```bash
# Search across Nana-related chats with a moderate window
ssh mac-host bes-imsg recent --chat-id 4 --since 7d   # Nana 1-1
ssh mac-host bes-imsg recent --chat-id 8 --since 7d   # Nana & Rosa
ssh mac-host bes-imsg recent --chat-id 49 --since 7d  # Nana & Kathy
```

Then synthesize: "Nana texted you Friday at 3pm saying she's bringing the
casserole on Sunday and asking if you can pick up Rosa on the way. She didn't
mention Sunday in the Nana & Rosa or Nana & Kathy threads in the last 7 days."

## Troubleshooting

- **`bes-imsg: chat_id N not in allowlist`** — you asked for an id that isn't in the 13. Run `bes-imsg chats` to remind yourself, OR Justin needs to add the chat to `~/.local/share/bes/imsg/allowlist.json` on the host.
- **`authorization denied (code: 23)` / FDA error** — the host's `sshd` may not have Full Disk Access. Justin needs to add `sshd-keygen-wrapper` (and possibly `sshd`) to System Settings → Privacy & Security → Full Disk Access on the Mac Mini.
- **Connection timeouts / "Host key verification failed"** — `mac-host` resolves to `host.lima.internal`. If that hostname doesn't resolve, check `~/.ssh/config` inside bes-vm.
- **Empty `messages` array but you know there was activity** — `is_from_me: true` messages are filtered out by the wrapper. Bes only sees incoming, not Justin's outgoing replies.

## Notes

- The wrapper logs every access to `~/.local/share/bes/imsg/access.log` on the host. Justin can audit what Bes pulled and when.
- Identical proxy pattern could be extended to other host-only macOS tools (Apple Notes via memo CLI, Apple Reminders via remindctl, FindMy, etc.) — same forced-command + allowlist shape. See `references/readonly-proxy-pattern.md` if it exists in this skill dir, otherwise extrapolate from `bes-imsg.sh` on the host.
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
