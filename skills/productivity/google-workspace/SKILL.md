---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python."
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.


> **⚠️ SEMI-READ-ONLY MODE (Bes-specific customization)**
>
> This installation of the google-workspace skill is mostly **scoped read-only**, except
> for **Google Calendar** which has **full write access** so you can schedule
> and manage events on Justin's behalf.
>
> **You can use these write commands:**
> - `calendar create`, `calendar delete`
>
> **You can use these read-only subcommands:**
> - `gmail search`, `gmail get`, `gmail labels`
> - `calendar list`
> - `drive search`, `drive get`, `drive download`
> - `contacts list`
> - `sheets get`
> - `docs get`
>
> **You CANNOT use these write commands — calls will return 403:**
> - `gmail send`, `gmail reply`, `gmail modify`
> - `drive upload`, `drive create-folder`, `drive share`, `drive delete`
> - `sheets create`, `sheets update`, `sheets append`
> - `docs create`, `docs append`
>
> If Justin asks you to send mail or modify a Drive file, tell him this account
> is read-only for those services and ask whether he wants to widen the scope.
> For Google Calendar, write commands will work.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user TWO questions:

**Question 1: "What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?"**

- **Email only** → They don't need this skill at all. Use the `himalaya` skill
  instead — it works with a Gmail App Password (Settings → Security → App
  Passwords) and takes 2 minutes to set up. No Google Cloud project needed.
  Load the himalaya skill and follow its setup instructions.

- **Email + Calendar** → Continue with this skill, but use
  `--services email,calendar` during auth so the consent screen only asks for
  the scopes they actually need.

- **Calendar/Drive/Sheets/Docs only** → Continue with this skill and use a
  narrower `--services` set like `calendar,drive,sheets,docs`.

- **Full Workspace access** → Continue with this skill and use the default
  `all` service set.

**Question 2: "Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library:
>    https://console.cloud.google.com/apis/library
>    Enable: Gmail API, Google Calendar API, Google Drive API,
>    Google Sheets API, Google Docs API, People API
> 3. Create the OAuth client here:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Application type: "Desktop app" → Create
> 5. If the app is still in Testing, add the user's Google account as a test user here:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Download the JSON file and tell me the file path
>
> Important Hermes CLI note: if the file path starts with `/`, do NOT send only the bare path as its own message in the CLI, because it can be mistaken for a slash command. Send it in a sentence instead, like:
> `The JSON file path is: /home/user/Downloads/client_secret_....json`

Once they provide the path:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

If they paste the raw client ID / client secret values instead of a file path,
write a valid Desktop OAuth JSON file for them yourself, save it somewhere
explicit (for example `~/Downloads/hermes-google-client-secret.json`), then run
`--client-secret` against that file.

### Step 3: Get authorization URL

Use the service set chosen in Step 1. Examples:

```bash
$GSETUP --auth-url --services email,calendar --format json
$GSETUP --auth-url --services calendar,drive,sheets,docs --format json
$GSETUP --auth-url --services all --format json
```

This returns JSON with an `auth_url` field and also saves the exact URL to
`~/.hermes/google_oauth_last_url.txt`.

Agent rules for this step:
- Extract the `auth_url` field and send that exact URL to the user as a single line.
- Tell the user that the browser will likely fail on `http://localhost:1` after approval, and that this is expected.
- Tell them to copy the ENTIRE redirected URL from the browser address bar.
- If the user gets `Error 403: access_denied`, send them directly to `https://console.cloud.google.com/auth/audience` to add themselves as a test user.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...`
or just the code string. Either works. The `--auth-url` step stores a temporary
pending OAuth session locally so `--auth-code` can complete the PKCE exchange
later, even on headless systems:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

If `--auth-code` fails because the code expired, was already used, or came from
an older browser tab, it now returns a fresh `fresh_auth_url`. In that case,
immediately send the new URL to the user and have them retry with the newest
browser redirect only.

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored at `~/.hermes/google_token.json` and auto-refreshes.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- If `gws` is installed, `google_api.py` points it at the same `~/.hermes/google_token.json` credentials file. Users do not need to run a separate `gws auth login` flow.
- To revoke: `$GSETUP --revoke`

## Usage

All commands go through the API script. Set `GAPI` as a shorthand:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Extract one field as raw text — preferred for shell, avoids `| python3 -c` and `| jq`
# (the python3 pipe pattern trips Hermes' command-approval security scanner)
$GAPI gmail get MESSAGE_ID --field body
$GAPI gmail get MESSAGE_ID --field body --max-len 2000
$GAPI gmail get MESSAGE_ID --field subject
# Fallback if you need a field --field doesn't cover, use jq (NOT python3 -c):
$GAPI gmail get MESSAGE_ID | jq -r '.body | .[0:2000]'

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```


## Multi-Account Usage (Bes customization)

Justin has multiple Google accounts. This installation supports per-account tokens
and cross-account read queries. Tokens are stored as
`~/.hermes/google_tokens/<account>.json`.

### Listing registered accounts

```bash
GWS_MULTI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/gws_multi.py"
$GWS_MULTI accounts
```

Returns JSON like `{"accounts": [{"account": "work", "auth_valid": true}, ...]}`.

### Running a command against a specific account

Use `--account <name>` (BEFORE the gmail/calendar/etc. subcommand):

```bash
$GWS_MULTI --account work gmail search "is:unread newer_than:1d" --max 5
$GWS_MULTI --account personal-main calendar list
$GWS_MULTI --account personal-junk gmail search "from:newsletter@example.com" --max 10
```

### Running a command across ALL accounts (cross-account view)

Use `--account all`:

```bash
$GWS_MULTI --account all calendar list           # All events across work + personal accounts
$GWS_MULTI --account all gmail search "is:unread newer_than:1d" --max 5
```

Or a subset:

```bash
$GWS_MULTI --account work,personal-main calendar list
```

### Extracting a single field as raw text (preferred over pipes)

When you only need one field from a `gmail get` (typically `body`), use
`--field` — it prints the raw value with no JSON wrapping, no jq, and no
`python3 -c`. The `python3 -c` pattern trips Hermes' command-approval
security scanner with a HIGH "pipe to interpreter" finding every time, so
prefer `--field` for routine work.

```bash
# Single account, raw body text:
$GWS_MULTI --account personal-main gmail get MSG_ID --field body --max-len 2000

# Multiple accounts: each account's output is prefixed with === <name> ===
$GWS_MULTI --account work,personal-main gmail get MSG_ID --field body

# Reading several emails in one go (the original use case):
for ID in 19e45975c0bdc35f 19e46218eb633052 19e457c4f0f6e434; do
  echo "=== $ID ==="
  $GWS_MULTI --account personal-main gmail get "$ID" --field body --max-len 2000
done
```

Documented fallback when `--field` doesn't cover what you need (nested
fields, multiple fields in one call, transformations): use `jq`, not
`python3 -c`. The scanner doesn't flag jq.

```bash
$GWS_MULTI --account personal-main gmail get MSG_ID \
  | jq -r '.body | .[0:2000]'
$GWS_MULTI --account personal-main gmail get MSG_ID \
  | jq -r '"Subject: \(.subject)\nFrom: \(.from)\n\n\(.body[0:2000])"'
```

### Output format with --account

Every record in the response gets an `"account": "<name>"` field added so you can
tell which account contributed which row. Per-account errors don't abort the
whole run — they're collected into a top-level `"_errors"` field on the response.

When summarizing for Justin, **always preface results with the account tag**:
- ✅ "On `work`: 3 unread; on `personal-main`: 1 unread."
- ❌ "4 unread emails." (loses the per-account view he wants)

### Decision: when to use --account all vs. a single account

- **Default to `--account all`** for time-sensitive queries ("what's on my calendar
  today", "any urgent unread emails") — Justin lives across all his accounts.
- Use a **specific account** when Justin explicitly names one ("check work email
  from Alice") or when the query is account-specific by topic (e.g. company-only
  Drive folders → `--account work`).
- For write operations (like creating calendar events): specify the correct target account using `--account <name>` (e.g. `gws_multi.py --account work calendar create ...` or `gws_multi.py --account personal-main calendar create ...`). Do not use `--account all` for write operations.

### Legacy single-account compatibility

If `--account` is omitted, the script falls back to the legacy single-token path
(`~/.hermes/google_token.json`) which is now a symlink to
`google_tokens/work.json`. So old calls like
`python google_api.py gmail search ...` still work and resolve to the work
account. Prefer the explicit `--account` form in new code.

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`

## Email noise filtering (for action-item capture)

When scanning Gmail to extract action items for Todoist or similar:

**Skip these automatically — they are never actionable for Justin:**
- Automated notifications: shipping/delivery (Amazon, etc.), parking receipts (PayByPhone), payment receipts
- App Store Connect issue alerts — Justin doesn't handle these; engineering does
- Calendar invite confirmations (accepted/declined auto-replies)
- Marketing newsletters (Mobbin, Loom, Figma announcements, Substack, Readwise summaries, Lenny's Newsletter, etc.)
- Todoist onboarding/tip emails
- Raymond James email-address-update confirmations
- Proud Haven / Hello Neighbor weekly newsletters (volunteer org updates, not personal asks)
- Guidepoint consultation requests — decline unless Justin explicitly says he wants to take them

**Read the full body before deciding on:**
- Emails from schools (Waldorf Pittsburgh, Winchester-Thurston) — often contain hard deadlines
- Emails from family (Nana, teachers) — may require coordinated action
- Raymond James / financial advisor threads — may have pending decisions
- Emails from SignLab colleagues — check for asks, not just FYIs

**Capture rule:** Only add to Todoist if there is a concrete next action for Justin. Informational emails, FYIs, and emails where Justin already replied are not actions.

## Rules

1. **Never send email, delete Drive files, share files, or modify Docs/Sheets without confirming with the user first.** Show what will be done (recipients, file IDs, content, share role) and ask for approval. For `drive delete`, prefer the default trash (reversible) over `--permanent`. For creating/deleting calendar events, confirm with Justin first unless he explicitly instructs you to create/schedule the events on his behalf (e.g. from forwarded emails, or during the morning briefing conversation).
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Pitfalls

1. **`json.loads()` fails on Gmail search output with control characters.** Email snippets frequently contain Unicode control chars (e.g. `\u034f`, zero-width spaces) that cause `json.decoder.JSONDecodeError: Invalid control character`. Always use `json_parse()` from `hermes_tools` (which uses `strict=False`) instead of `json.loads()` when parsing gmail search/get output in `execute_code`.

   ```python
   from hermes_tools import json_parse
   data = json_parse(result["output"])  # not json.loads(result["output"])
   ```

2. **Use `--field body --max-len N` for targeted email reads.** Avoids piping through `python3 -c` (trips the security scanner) and keeps output manageable. Fall back to `jq` (not `python3 -c`) when you need multiple fields or transformations.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `AUTHENTICATED (partial)` or "Token missing scopes" | New write capabilities (Drive write/delete, Docs create/edit) require re-authorization. `$GSETUP --revoke` then redo Steps 3-5 to grant the upgraded scopes. |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoking Access

```bash
$GSETUP --revoke
```
