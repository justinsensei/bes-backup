Justin has another agent named Hermes that handles infrastructure, plumbing, and skill management for all his agents. Hermes is good at bulk skill creation and knows DevOps quirks around skill authoring. Defer skill migration/creation tasks to Hermes when appropriate; don't duplicate that work.
§
Email: read Gmail via Google OAuth. Tokens at `~/.hermes/google_tokens/{work,personal-main,personal-junk}.json`. Cross-account wrapper: `python3 ~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py --account all|<name>|<csv> gmail search "..." --max N`. Single-account: set `HERMES_GOOGLE_TOKEN_FILE` and call `google_api.py`. Read-only. Do NOT use himalaya.
§
Obsidian vault has four category notes: Meetings, Organizations, People, Projects. Each has its own template. When creating a note of a category, follow that category's template. When searching for notes by category, filter by `category: "[[CategoryName]]"` (e.g. `category: "[[Meetings]]"`).
§
Todoist structure (as of 2026-05-20): No sequential project approximation — Justin decided to accept the gap vs. OmniFocus rather than add a @blocked label with manual upkeep overhead. Revisit if it becomes a real pain point.
§
App Store Connect issue emails are not Justin's to handle — ignore them when capturing action items from email.
§
Todoist is for actions only — no informational notes or FYIs. If something isn't actionable, don't capture it.