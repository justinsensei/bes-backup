Hermes handles infrastructure & skill management for Justin's agents. Defer skill migration/creation tasks to him.
§
Email: read Gmail via Google OAuth. Tokens at `~/.hermes/google_tokens/{work,personal-main,personal-junk}.json`. Cross-account wrapper: `python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account all|<name>|<csv> gmail search "..." --max N`. Single-account: set `HERMES_GOOGLE_TOKEN_FILE` and call `google_api.py`. Read-only. Do NOT use himalaya.
§
Obsidian folder taxonomy uses lower-case root folders routed by category Type: Contacts live in contacts/, Notes (concepts, projects, travel/trips, thoughts, decisions, references) live in notes/, Logs (daily, meetings) live in logs/, and Category representations live in utilities/categories/.
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
Vault hygiene ignores Copilot/Granola logs. Granola notes sync directly to meetings/ and are auto-reconciled and moved to logs/meetings/ via vault_hygiene.py.
§
Forwarded emails should not be copied to vault unless explicitly requested.
§
Obsidian horizontal rule: always use three hyphens `---` for a horizontal line, never two hyphens `--`.
§
Readwise script is at ~/sync_readwise.py. It exports highlights tagged 'vault' (case-insensitive) to vault/sources/.
§
Justin has abandoned gbrain and prefers growing custom agent solutions on top of Bes by selectively reusing skills.