#!/usr/bin/env python3
"""
reconcile_granola.py — Reconciles raw Granola meeting notes in meetings/ with standard vault frontmatter.
Adds id, daily_note, and category: "[[Meetings]]", and cleans up typical markdown anomalies.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Try to resolve vault path from env, fallback to default
vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
if not vault_path:
    vault_path = os.path.expanduser("~/vault")

MEETINGS_DIR = Path(vault_path) / "meetings"

def get_weekday(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%A").lower()
    except Exception:
        return "monday"

def reconcile_file(file_path: Path, existing_ids: set):
    content = file_path.read_text(encoding="utf-8")
    filename = file_path.name
    
    # Extract date from filename prefix YYYY-MM-DD
    date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", filename)
    if not date_match:
        return False
        
    date_str = date_match.group(1)
    weekday = get_weekday(date_str)
    
    # Check if frontmatter already exists
    has_frontmatter = content.startswith("---")
    
    fm_block = ""
    body = content
    
    if has_frontmatter:
        # Find closing ---
        end_fm = content.find("---", 3)
        if end_fm > 0:
            fm_block = content[3:end_fm]
            body = content[end_fm + 3:]
        else:
            has_frontmatter = False
            
    # Parse fields from frontmatter if it exists
    note_id = ""
    if has_frontmatter:
        id_match = re.search(r"^id:\s*[\"']?(\d+)[\"']?", fm_block, re.MULTILINE)
        if id_match:
            note_id = id_match.group(1).strip()
            
    # Check for missing fields
    id_missing = not note_id
    dn_missing = "daily_note:" not in fm_block
    cat_missing = "category:" not in fm_block
    
    # Generate unique ID if missing
    if id_missing:
        stat_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        time_suffix = stat_time.strftime("%H%M%S")
        candidate_id = f"{date_str.replace('-', '')}{time_suffix}"
        
        while candidate_id in existing_ids:
            candidate_id = str(int(candidate_id) + 1)
            
        note_id = candidate_id
        existing_ids.add(note_id)
    
    # Reconstruct/Add Frontmatter
    if not has_frontmatter:
        # Check if the file starts with '--' (frequent Granola artifact) and strip it
        if body.lstrip().startswith("--\n") or body.lstrip().startswith("--\r\n"):
            body = re.sub(r"^--\s*\n", "", body.lstrip())
            
        new_fm = f"id: {note_id}\ndaily_note: '[[{date_str} {weekday.capitalize()}|{date_str} {weekday.capitalize()}]]'\ncategory: \"[[Meetings]]\""
    else:
        new_fm_lines = []
        # Rebuild existing fields except id, daily_note, category if they need to be rewritten
        for line in fm_block.splitlines():
            if line.startswith("id:"):
                continue
            if dn_missing and line.startswith("daily_note:"):
                continue
            if cat_missing and line.startswith("category:"):
                continue
            new_fm_lines.append(line)
            
        new_fm_lines.insert(0, f"id: {note_id}")
        if dn_missing:
            new_fm_lines.append(f"daily_note: '[[{date_str} {weekday.capitalize()}|{date_str} {weekday.capitalize()}]]'")
        if cat_missing:
            new_fm_lines.append("category: \"[[Meetings]]\"")
        new_fm = "\n".join(new_fm_lines)
        
    # Clean up dual/messy horizontal rules at the start of body
    body_clean = body.lstrip()
    if body_clean.startswith("---"):
        body_clean = re.sub(r"^---\s*\n", "", body_clean)
        
    # Standardize remaining '--' lines to '---' (Obsidian rule)
    body_clean = re.sub(r"^--\s*$", "---", body_clean, flags=re.MULTILINE)
    
    final_content = f"---\n{new_fm.strip()}\n---\n{body_clean}"
    
    if final_content != content:
        file_path.write_text(final_content, encoding="utf-8")
        print(f"Reconciled: {filename}")
        return True
    return False

def main():
    if not MEETINGS_DIR.exists():
        print(f"Meetings directory {MEETINGS_DIR} does not exist.")
        sys.exit(1)
        
    # Collect existing IDs to avoid duplicates
    existing_ids = set()
    skip_dirs = {"Readwise", "utilities", ".git", ".trash", ".cursor", ".claude", "sources", "daily"}
    for root, dirs, files in os.walk(MEETINGS_DIR.parent):
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
                
    reconciled_count = 0
    for f in sorted(MEETINGS_DIR.glob("*.md")):
        if f.is_file():
            try:
                if reconcile_file(f, existing_ids):
                    reconciled_count += 1
            except Exception as e:
                print(f"Error processing {f.name}: {e}", file=sys.stderr)
                
    print(f"Completed granola reconciliation. Total reconciled: {reconciled_count}")

if __name__ == "__main__":
    main()
