---
name: apple-notes
description: Use when working with apple notes. Manage and search your Apple Notes
  'filing cabinet' on the macOS host via the secure SSH proxy.
version: 1.1.0
platforms:
- linux
metadata:
  hermes:
    tags:
    - Notes
    - Apple
    - macOS
    - filing-cabinet
    - proxy
author: Bes
license: MIT
---

# Apple Notes (VM-to-Host Proxy)

Use this skill inside Bes-VM to interact with your Apple Notes "filing cabinet" on the macOS host. All commands run securely over SSH via `mac-host-notes`.

## When to Use

- User asks to view, create, or search Apple Notes filing cabinet.
- Supporting ongoing filing cabinet organization and management.

## When NOT to Use

- Direct host-side executions (use `ssh mac-host-notes` instead).
- Local VM-level files.

## Quick Reference

### List Folders
```bash
ssh mac-host-notes list-folders
```

### List Notes in a Folder
```bash
ssh mac-host-notes list-notes "Folder Name"
```

### Create a Folder
```bash
ssh mac-host-notes create-folder "New Folder Name"
```

### Create a Note
```bash
ssh mac-host-notes create-note "Folder Name" "Note Title" "<h1>Note Title</h1><p>HTML Note Content</p>" [host_attachment_paths...]
```

### Search Notes
```bash
ssh mac-host-notes search-notes "query"
```

## Migration Script

To run the one-time migration of your Obsidian vault to Apple Notes (migrating all of `References/` and any other note tagged with `#filing_cabinet`), run the migration script inside `bes-vm` using the system Python (to ensure `markdown` is available outside virtualenvs):

```bash
/usr/bin/python3 ~/migrate_notes.py
```

This script automatically scans the vault, builds matching folders, converts Markdown/YAML frontmatter to clean HTML format, resolves images/PDFs from the Attachments directory, and imports them flawlessly into Apple Notes!

## Pitfalls & SSH Argument Escaping

When running manual `ssh mac-host-notes` commands, the SSH protocol flattens the arguments into a single string which is re-parsed by the remote shell. This means **spaces in arguments (like folder names or note titles) will get split** unless they are nested-quoted:

- **Fails:** `ssh mac-host-notes list-notes "References/ID Docs"` (remote side sees `"References/ID"` and `"Docs"`)
- **Succeeds:** `ssh mac-host-notes list-notes "'References/ID Docs'"`
- **Python usage:** Always use `shlex.quote()` on each argument before passing them to the SSH command list to handle quoting automatically.
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
