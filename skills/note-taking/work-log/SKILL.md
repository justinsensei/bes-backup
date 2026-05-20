---
name: work-log
description: Use when Justin asks to "create a work log", "log today's work", "write a work log", or otherwise wants today's work activity summarized and appended to today's daily note in the Obsidian vault. Pulls from Slack (SignLab), Linear, Gmail (work + personal-main + personal-junk), Google Calendar (all 3 accounts), plus the daily note and any chat brain-dump.
platforms: [linux, macos]
---

# Work Log

Summarize today's work activity and append a structured Work Log block to **today's daily note** in the Obsidian vault. Do NOT create a separate file.

The block has three sections — **Highlights / Decisions / Open Questions** — synthesized across all sources. New sources do not get their own headings; they feed the synthesis. The footer enumerates which sources were actually pulled and rough counts.

## Step 1 — Resolve vault path

Read `OBSIDIAN_VAULT_PATH` from env (typically `/home/justin.guest/vault` inside `bes-vm`). Do not hard-code. If unset, fall back to `~/Documents/Obsidian Vault`. See the `obsidian` skill for full path-handling conventions.

## Step 2 — Find today's daily note

Daily-note filename format: `YYYY-MM-DD DayName.md` (e.g. `2026-05-20 Wednesday.md`).

Justin's vault convention: **current** daily notes live in the vault root; **archived** daily notes live in `Daily Notes/`. Check the root first:

1. `<vault>/<YYYY-MM-DD DayName>.md` — primary
2. `<vault>/Daily Notes/<YYYY-MM-DD DayName>.md` — fallback (rare; means today's note already got archived, which is unusual mid-day)

Use `search_files` with `target: "files"` to locate. If neither exists, tell Justin "Today's daily note doesn't exist yet — create it first." and stop.

## Step 3 — Gather raw material (parallel, one subagent per source)

Spawn **one `delegate_task` subagent per external source** in a single batch so raw API output stays out of your context. Each subagent returns a small filtered summary (bullets, ~10–30 items max). You only see the summaries.

Today's date in vault timezone is the cutoff for every source. Pre-compute it once (`date +%F` in the VM shell) and pass it to each subagent verbatim — don't let subagents re-derive it.

### Subagent A — Slack (SignLab)

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `slack`
- **Goal:** "Summarize Justin's Slack activity for `<YYYY-MM-DD>` in the SignLab workspace. Use the `slack` CLI."
- **Context to pass:**
  - Today's date.
  - Workspace: SignLab (only one wired up).
  - Scope: messages Justin sent, messages directed at him (@mentions, DMs, threads he was in), and any channel where he reacted or participated.
  - Filter out: pure social chatter Justin wasn't part of; bot/integration noise (Zapier, GitHub bots, deploy bots) unless Justin reacted; channels he's only lurking in.
  - Keep: decisions, asks, blockers, FYIs to/from him, threads where he weighed in, any DMs.
  - Output format: bullet list grouped by channel/DM, each bullet has `[#channel | @person]` prefix, one-line gist, and (if material) the slack permalink. End with a count: `Total: N messages across M channels/DMs.`

### Subagent B — Linear

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `linear`
- **Goal:** "Summarize Justin's Linear activity for `<YYYY-MM-DD>`."
- **Context to pass:**
  - Today's date.
  - Pull issues where Justin is assignee, creator, or commenter AND that had activity today (status change, comment, new issue, completion).
  - Output format: bullets like `[TEAM-123 | status] Title — what changed today.` End with `Total: N issues touched.`

### Subagent C — Email (all 3 Gmail accounts via gws_multi)

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `google-workspace`
- **Goal:** "Summarize emails Justin sent or received on `<YYYY-MM-DD>` across all 3 accounts (work, personal-main, personal-junk)."
- **Context to pass:**
  - Today's date in `YYYY/MM/DD` form (Gmail search uses `after:`/`before:` with slashes).
  - Use the `gws_multi.py` wrapper, `--account all`, search `after:YYYY/MM/DD before:YYYY/MM/DD+1`. The wrapper path lives at `${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py`.
  - Bes's gws token is **read-only** — `gmail search` and `gmail get` work; sending does not. Do not attempt sends.
  - Filter out per account:
    - **work**: drop pure CI/build notifications, calendar invites that already show in Calendar, automated reports unless Justin replied. Keep human-to-human threads and anything he sent.
    - **personal-main**: keep only items that touch work, scheduling, or Justin-as-operator-of-his-life decisions. Drop newsletters, receipts, marketing.
    - **personal-junk**: this is the newsletter/marketing inbox by design. Default = drop everything. Only surface a thread if a real human DM-style email slipped through.
  - Output format: bullets grouped by account, `[account | from→to]` prefix, one-line gist. End with `Total: N relevant threads (work: X, personal-main: Y, personal-junk: Z).`

### Subagent D — Calendar (all 3 Google accounts via gws_multi)

- **Toolsets:** `["terminal"]`
- **Skill to mention:** `google-workspace`
- **Goal:** "List Justin's calendar events for `<YYYY-MM-DD>` across all 3 accounts."
- **Context to pass:**
  - Today's date.
  - Use `gws_multi.py --account all calendar list` and filter to events whose start is today (vault timezone).
  - Include: meetings (with attendees), focus blocks Justin himself created, all-day events that materially affected today.
  - Output format: chronological bullets like `HH:MM–HH:MM [account] Title — attendees (if any) — location/link (if any).` Note whether each event happened, was cancelled/declined, or is upcoming-later-today. End with `Total: N events.`

### Subagent E (optional) — recent git activity

Skip unless Justin specifically mentions code work. If you do run it: scope to repos under `~/clio-backup`, `~/bes-backup`, `~/hermes-agent` (if present), and any project repo Justin mentioned in the daily note. Use `git log --author --since=midnight --pretty` per repo. Return commits as bullets `[repo] sha — subject`.

### After subagents return

You now have 4 (or 5) small summaries. Also do these two **in-context** reads — they're cheap:

1. **Read today's daily note** with `read_file`. Scan for decisions, completions, blockers, links, meeting notes Justin wrote himself.
2. **Ask Justin in chat** what else he worked on that isn't in any source yet. Short prompt: *"Anything from today not captured in Slack/Linear/email/calendar/daily-note? Side-quests, conversations IRL, decisions in your head?"* If he says "nothing," move on.

If a subagent fails (auth expired, network, etc.), include the failure in the footer (`Slack: ERR — token expired`) rather than silently dropping the source. Then continue with what you have.

## Step 4 — Synthesize three sections

Produce a Work Log block with three section headings. Omit any section that has no real content (don't include an empty heading).

### `### Today's Highlights`
The most important things that happened — shipped work, key conversations, decisions reached, code written, problems solved. Pull from all sources. Be specific: name the people, channels, projects, outcomes. Past tense. 6–12 bullets typically; fewer is fine if it was a quiet day. Cite the source inline only when it adds clarity, e.g. *"Resolved blocker with Maya on render pipeline (#product-leads thread)."*

### `### Decisions Made`
Consequential decisions only. For each, bold the decision itself; include owner if not obvious. Skip if no real decisions were made — don't promote tasks or observations into "decisions." A Linear status change is not a decision; a Slack thread where a tradeoff was settled IS.

### `### Open Questions / Blockers`
Unresolved questions, pending actions, known blockers as of end-of-day. Includes asks Justin owes a reply to (from Slack/email), Linear issues stalled waiting on someone, calendar conflicts upcoming. Skip if none.

Writing style: concise, specific, past tense for highlights. Match the voice of prior work logs if Justin has any (grep for `## 💼 Work Log` in the daily-notes archive to find examples).

## Step 5 — Append to the daily note

Use `patch` (anchored append) or `write_file` (whole-note rewrite). Append this block at the **end** of the note, preserving everything above:

```
## 💼 Work Log

### Today's Highlights
[bullets]

### Decisions Made
[bullets]

### Open Questions / Blockers
[bullets]

---
*Sources: Slack (12 msgs / 4 channels) | Linear (5 issues) | Gmail work (8 threads), personal-main (1), personal-junk (0) | Calendar (4 events / 3 accts) | daily note + chat.*
```

Use the **actual counts** from the subagent summaries. If a source was unavailable, mark it `ERR` with a short reason. Always include `daily note + chat` at the end.

Do NOT add a separate frontmatter block. Do NOT modify anything else in the file.

## Step 6 — Don't commit

Justin's `bes-vault-sync` watcher auto-commits and pushes the vault to `obsidian-vault` on GitHub within seconds of any write. Do NOT manually `git add` or `git commit` — it races the watcher and creates spurious commits.

## Important behaviors

- **No duplicate Work Log blocks.** If the daily note already contains `## 💼 Work Log`, ask Justin: replace, update, or skip? Don't append a second one silently.
- **Omit empty sections.** A Work Log with only Highlights is better than one with empty "Decisions Made" / "Open Questions" headings.
- **No file creation.** The only write operation is appending to the existing daily note.
- **Skip cleanup of the daily note.** Don't reformat or tidy what Justin already wrote — the Work Log block is additive.
- **Privacy posture.** Slack DMs and personal email can be sensitive. The subagent filter steps exist for a reason — keep the synthesis at the "what Justin did / decided / owes" level, not verbatim quotes. If something looks too private to land in a vault that auto-pushes to GitHub (even a private repo), ask Justin before including it.
- **Date precision.** "Today" means today in the vault's timezone, not UTC. Pre-compute the date once at Step 3 and pass it to every subagent. Don't trust subagents to re-derive it.
- **Source failures are non-fatal.** If Slack auth expired or Linear is down, log it in the footer and continue. A 3-source work log is still useful.

## Pitfalls

- **`gws_multi.py` path varies by Hermes home.** Always resolve it as `${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py` — don't hardcode `/home/justin.guest/...`.
- **Gmail date format is `YYYY/MM/DD` with slashes**, not dashes. Calendar event listings use ISO. Don't mix them up.
- **`slack` CLI defaults to read-only-ish use.** Never let a subagent post to a channel — the work-log gather is read-only by definition.
- **Calendar "all-day events" can be timezone-shifted by one day** depending on how they were created. If something looks off-by-one, double-check the event's raw start/end before flagging it as a discrepancy.
- **Linear API key auth header has NO "Bearer" prefix** — see the linear skill if a subagent hits 401s.
