#!/usr/bin/env python3
"""
vault_hygiene.py — Obsidian vault hygiene check + auto-fix.
Leverages `gbrain lint --fix` for content fixes and misplaced file moving,
and runs local checks for ID conflicts, missing IDs, and missing daily notes.
"""

import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path

VAULT = Path("/home/justin.guest/vault")

# 1. Run gbrain lint --fix to auto-fix and move files
print("Running gbrain lint...")
subprocess.run(["gbrain", "lint", str(VAULT), "--fix"], capture_output=True, text=True)

# 2. Walk the vault to detect ID conflicts, missing ID, missing daily_note
id_to_paths = defaultdict(list)
missing_ids = []
missing_daily_notes = []

# Folders to skip for manual checks
skip_dirs = {"Readwise", "utilities", ".git", ".trash", ".cursor", ".claude", "sources", "daily"}

for root, dirs, files in os.walk(VAULT):
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
    for f in sorted(files):
        if not f.endswith(".md") or f == "RESOLVER.md":
            continue
        path = Path(root) / f
        text = path.read_text(encoding="utf-8", errors="replace")
        
        # Parse frontmatter
        note_id = ""
        daily_note = ""
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end > 0:
                fm_raw = text[3:end]
                id_match = re.search(r"^id:\s*[\"']?(\d+)[\"']?", fm_raw, re.MULTILINE)
                dn_match = re.search(r"^daily_note:\s*[\"']?([^\"'\n]+)[\"']?", fm_raw, re.MULTILINE)
                if id_match:
                    note_id = id_match.group(1).strip()
                if dn_match:
                    daily_note = dn_match.group(1).strip()
        
        rel_path = path.relative_to(VAULT)
        if note_id:
            id_to_paths[note_id].append(rel_path)
        else:
            missing_ids.append(rel_path)
            
        if not daily_note or "[[" not in daily_note:
            missing_daily_notes.append(rel_path)

# 3. Format output for vault_hygiene_cron.py
lines = []

# ID Conflicts
id_conflicts = {nid: paths for nid, paths in id_to_paths.items() if len(paths) > 1}
if id_conflicts:
    lines.append("## 🔴 ID conflicts")
    for nid, paths in sorted(id_conflicts.items()):
        for p in paths:
            lines.append(f"  - {p}: id={nid} shared by {len(paths)} notes")

# Missing ID
if missing_ids:
    lines.append("\n## 🔴 Missing ID")
    for p in sorted(missing_ids):
        lines.append(f"  - {p}")

# Missing daily_note
if missing_daily_notes:
    lines.append("\n## 🔴 Missing daily_note")
    for p in sorted(missing_daily_notes):
        lines.append(f"  - {p}")

if lines:
    print("\n".join(lines))
else:
    print("✅ Vault looks clean — no issues found.")
