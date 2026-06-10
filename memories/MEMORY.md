Hermes handles infra/skills. Defer migrations/creations to Justin.
§
Gmail (read-only): tokens under ~/.hermes/google_tokens/. Search via gws_multi.py. Do not use himalaya.
§
Obsidian routes: Notes/Contacts/, Notes/Daily Notes/, Notes/, Inputs/ (Readings/Meetings/Emails/Slack), Utilities/. Layer 2 compiled Sources in Notes/. Dividers: always `---`.
§
App Store Connect issue emails are not Justin's to handle — ignore them when capturing action items from email.
§
Todoist is for actions only — no informational notes or FYIs. If something isn't actionable, don't capture it.
§
Inbox fills: exclude generic meeting prep/internal syncs, and do not suggest tasks for Linear issues already linked/referenced in Todoist.
§
Justin uses Apple Notes as a "filing cabinet" for references (previously in Obsidian References/), while continuing to use Obsidian for general note-taking.
§
Google Calendar has write access; Bes can directly schedule events on Justin's behalf (e.g., during morning briefings or from forwarded emails) using `gws_multi.py --account <name> calendar create` instead of creating 'Add to calendar' tasks in Todoist.
§
Scraps (ID) default under the vault root (/) as scratchpad. Notes are factual support. Inbox is for Bes-created reviews. Decisions in inbox.
§
Any new contact (people or companies) created by Bes must land in /home/justin.guest/vault/inbox/. Existing contacts in Notes/Contacts/ are updated in place and never relocated.
§
Timelines are disabled in favor of native Backlinks. check_vault_signals.py is read-only, and integrate_entities.py only updates project State on decisions.
§
Query syntheses → inbox/ on creation via llm-wiki, printed in channel, log.md append.
§
Tier-3 semantic lint (`wiki_semantic_lint.py`) runs monthly (1st, 8am cron `a3f8c2e91b04`). Report-only — orphans (inbound), stale Sources, promotion gaps, contradiction candidates. State: `~/.hermes/state/semantic_lint_last.json`. Structural lint stays in `vault_hygiene.py`.
§
Vault chronological logging is active; logs are appended to Utilities/log.md.