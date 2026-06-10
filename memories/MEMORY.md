Hermes handles infra/skills. Defer migrations/creations to Justin.
§
Gmail (read-only): tokens under ~/.hermes/google_tokens/. Search via gws_multi.py. Do not use himalaya.
§
Obsidian routes: Contacts/, Notes/, Inputs/ (Readings/Meetings/Emails/Slack), Daily Notes/, Utilities/. Layer 2 compiled Sources in Notes/. Dividers: always `---`.
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
Granola notes sync to meetings/ and are reconciled to Inputs/Meetings/ via vault_hygiene.py.
§
Forwarded emails should not be copied to vault unless explicitly requested.
§
Readwise script is at ~/sync_readwise.py. It exports highlights tagged 'vault' (case-insensitive) to vault/Inputs/Readings/ (migrate from Logs/Sources/).
§
User prefers modular, composable skills (no monolithic files).
§
Default new notes to 'Notes' (timestamp ID). Draft decisions in inbox using simplified narrative. Triaging: References (patterns), Thoughts (reflections), Concepts (models).
§
Weekly summaries are requested manually on the first day of the week and delivered directly to the requesting Telegram conversation instead of running on a schedule.
§
Any new contact (people or companies) created by Bes must land in /home/justin.guest/vault/inbox/. Existing contacts in Contacts/ are updated in place and never relocated.
§
Vault signals scan script (check_vault_signals.py) is read-only. Timelines are disabled in favor of native Obsidian Backlinks.