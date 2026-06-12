Hermes handles infra/skills. Defer migrations/creations to Justin.
§
Gmail (read-only): tokens under ~/.hermes/google_tokens/. Search via gws_multi.py. Do not use himalaya.
§
Obsidian routes: Notes/Contacts/, Notes/Daily Notes/, Notes/, Inputs/ (Readings/Meetings/Emails/Slack/Linear), Utilities/. Layer 2 compiled Sources in Notes/. Dividers: always `---`. Log appends to Utilities/log.md.
§
Ignore App Store Connect emails (not Justin's).
§
Todoist rules: Actions only. Inbox fills exclude generic prep, iMessage, archived mail, Linear Triage/Backlog/Completed/Canceled, and items already in Todoist.
§
Justin uses Apple Notes as a "filing cabinet" for references (previously in Obsidian References/), while continuing to use Obsidian for general note-taking.
§
Google Calendar has write access; Bes can directly schedule events on Justin's behalf (e.g., during morning briefings or from forwarded emails) using `gws_multi.py --account <name> calendar create` instead of creating 'Add to calendar' tasks in Todoist.
§
New contacts to vault/inbox/ (existing in Notes/Contacts/ updated in place). Scraps to inbox/. Forwarded emails to Inputs/Emails/. Inbox holds Bes-created reviews, Decisions, and Query syntheses.
§
Always query and use Telegram/cron session history (titles/summaries from state.db) as a core input when creating work logs for Justin, ensuring that all Bes/Vault development chat sessions are captured.
§
The ~/.hermes/ directory on the VM is a live runtime directory, NOT a Git repository. Never run git init or git commands inside ~/.hermes/ or its subfolders (such as ~/.hermes/skills/). The actual Git repository for system-state backups is ~/bes-backup/. Always perform git commits, pushes, and status checks inside ~/bes-backup/ instead.
§
When writing Python scripts or calling execute_code, do not attempt to import from hermes_tools.mcp_todoist or any other mcp-specific submodules. The hermes_tools library only exposes read_file, write_file, search_files, patch, and terminal. Standard MCP tools are not importable in Python. To call external APIs (Todoist, Linear, Slack, etc.) from Python scripts, make direct HTTP requests using urllib.request and the corresponding token from .env (e.g. TODOIST_API_KEY, LINEAR_API_KEY).