#!/usr/bin/env python3
"""
vault_hygiene.py — Obsidian vault hygiene check + auto-fix.
Leverages `gbrain lint --fix` for content fixes and misplaced file moving,
and runs local checks for ID conflicts, missing IDs, and missing daily notes.
"""

import os
import re
import subprocess
import datetime
from collections import defaultdict
from pathlib import Path

VAULT = Path("/home/justin.guest/vault")

def reconcile_granola_meetings(vault_path):
    meetings_dir = Path(vault_path) / "meetings"
    meetings_dir.mkdir(parents=True, exist_ok=True)
    
    dest_dir = Path(vault_path) / "logs" / "meetings"
    dest_dir.mkdir(parents=True, exist_ok=True)
        
    print("Reconciling meetings from Granola...")
    
    # Pre-scan vault for existing IDs to avoid collisions
    existing_ids = set()
    skip_dirs = {"Readwise", "utilities", ".git", ".trash", ".cursor", ".claude", "sources", "daily"}
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if not f.endswith(".md"):
                continue
            p = Path(root) / f
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                if content.startswith("---"):
                    end = content.find("\n---", 3)
                    if end > 0:
                        fm = content[3:end]
                        id_match = re.search(r"^id:\s*[\"']?(\d+)[\"']?", fm, re.MULTILINE)
                        if id_match:
                            existing_ids.add(id_match.group(1).strip())
            except Exception:
                pass

    for src_dir, is_raw in [(meetings_dir, True), (dest_dir, False)]:
        for path in sorted(src_dir.glob("*.md")):
            filename = path.name
            # Match YYYY-MM-DD at start of filename
            date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", filename)
            if not date_match:
                continue
                
            date_str = date_match.group(1)
            try:
                dt = datetime.date.fromisoformat(date_str)
                weekday_lower = dt.strftime("%A").lower()
                weekday_cap = dt.strftime("%A")
            except ValueError:
                continue
                
            text = path.read_text(encoding="utf-8", errors="replace")
            
            # Check if the file has standard frontmatter
            has_frontmatter = False
            fm_content = ""
            body_content = text
            
            if text.startswith("---"):
                fm_end = text.find("\n---", 3)
                if fm_end > 0:
                    has_frontmatter = True
                    fm_content = text[3:fm_end]
                    body_content = text[fm_end+4:]
                    
            # Parse fields from frontmatter if it exists
            note_id = ""
            daily_note = ""
            
            if has_frontmatter:
                id_match = re.search(r"^id:\s*[\"']?(\d+)[\"']?", fm_content, re.MULTILINE)
                dn_match = re.search(r"^daily_note:\s*[\"']?([^\"'\n]+)[\"']?", fm_content, re.MULTILINE)
                if id_match:
                    note_id = id_match.group(1).strip()
                if dn_match:
                    daily_note = dn_match.group(1).strip()
                    
            needs_update = False
            
            if not note_id:
                mtime = path.stat().st_mtime
                mtime_dt = datetime.datetime.fromtimestamp(mtime)
                if mtime_dt.strftime("%Y-%m-%d") == date_str:
                    time_part = mtime_dt.strftime("%H%M%S")
                else:
                    time_part = "120000"
                    
                candidate_id = f"{date_str.replace('-', '')}{time_part}"
                while candidate_id in existing_ids:
                    # Increment the ID to make it unique
                    candidate_id = str(int(candidate_id) + 1)
                
                note_id = candidate_id
                existing_ids.add(note_id)
                needs_update = True
                
            if not daily_note or "[[" not in daily_note:
                daily_note = f"[[logs/daily/{date_str}-{weekday_lower}|{date_str} {weekday_cap}]]"
                needs_update = True
                
            # Clean body: strip leading whitespace and redundant separators
            original_body = body_content
            body_content = body_content.lstrip()
            
            # Clean up double hyphens / horizontal rules at top of body (Granola artifact)
            if body_content.startswith("--\n") or body_content.startswith("--\r\n"):
                body_content = body_content.split("\n", 1)[1].lstrip()
                needs_update = True
            elif body_content.startswith("-- ") or body_content.startswith("--\t"):
                body_content = body_content.split("\n", 1)[1].lstrip()
                needs_update = True
            elif body_content.startswith("---\n") or body_content.startswith("---\r\n"):
                body_content = body_content.split("\n", 1)[1].lstrip()
                needs_update = True
                
            if body_content != original_body:
                needs_update = True
                
            if is_raw or needs_update:
                # Construct clean frontmatter and write to dest_dir
                new_fm = f"---\nid: {note_id}\ndaily_note: '{daily_note}'\n---\n"
                new_text = new_fm + body_content
                dest_path = dest_dir / filename
                dest_path.write_text(new_text, encoding="utf-8")
                
                if needs_update:
                    print(f"  Fixed/Reconciled: {filename}")
                else:
                    print(f"  Processed and moved: {filename}")
                    
                if is_raw:
                    # Delete original file
                    try:
                        path.unlink()
                    except Exception as e:
                        print(f"  Error deleting original raw file {filename}: {e}")

# 1. Reconcile raw Granola meetings from external syncing
reconcile_granola_meetings(VAULT)

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
