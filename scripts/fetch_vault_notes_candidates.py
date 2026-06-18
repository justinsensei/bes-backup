#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse
from datetime import datetime, timedelta, timezone

def parse_args():
    parser = argparse.ArgumentParser(description="Scan vault notes for candidates")
    parser.add_argument("--lookback-hours", type=int, default=48, help="Lookback hours for modified files")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of Markdown")
    return parser.parse_args()

def get_slug(vault_path, file_path):
    rel_path = os.path.relpath(file_path, vault_path)
    # Remove .md extension and replace path separators with forward slashes
    slug = rel_path[:-3].replace(os.path.sep, '/')
    return slug

def parse_creation_id(content):
    # Parse 14-digit timestamp from frontmatter id (e.g. id: 20260611080000 or id: "20260611080000")
    match = re.search(r"^id:\s*[\"']?(\d{14})[\"']?", content, re.MULTILINE)
    if match:
        try:
            id_str = match.group(1)
            return datetime.strptime(id_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None

def is_daily_note(slug, filename):
    # Skip if slug/filename matches daily note patterns
    if "Daily Notes/" in slug or "daily/" in slug or "Logs/Daily/" in slug or "logs/daily/" in slug:
        return True
    if re.match(r"^\d{4}-\d{2}-\d{2}", filename):
        return True
    return False

def is_granola_note(slug):
    if "Granola/" in slug or "granola/" in slug:
        return True
    return False

def scan_file_for_candidates(file_path, content, slug, is_new, lookback_cutoff, candidates):
    # 1. Unchecked tasks: - [ ]
    task_pattern = re.compile(r"^\s*-\s*\[\s*\]\s*(.+)$", re.MULTILINE)
    for match in task_pattern.finditer(content):
        task_text = match.group(1).strip()
        if not task_text or len(task_text) < 3:
            continue
        # Skip templated/generic tasks
        if "template" in task_text.lower() or "placeholder" in task_text.lower():
            continue
        candidates.append({
            "source": "Obsidian/note",
            "type": "task",
            "description": f"{task_text}",
            "context": f"Unchecked item in [[{slug}]]",
            "url": f"obsidian://open?vault=vault&file={urllib_parse_quote(slug)}"
        })

    # 2. First-person commitment phrases
    commitment_keywords = [
        "i need to", "i have to", "follow up on", "remind me to", 
        "i should", "i must", "don't forget to", "action item:"
    ]
    lines = content.split('\n')
    for line in lines:
        line_strip = line.strip()
        # Skip headers, lists/tasks, or short lines
        if line_strip.startswith('#') or line_strip.startswith('- [') or len(line_strip) < 10:
            continue
        line_lower = line_strip.lower()
        for kw in commitment_keywords:
            if kw in line_lower:
                # Make sure it's not a quote/reference
                if line_strip.startswith('>') or line_strip.startswith('*'):
                    continue
                candidates.append({
                    "source": "Obsidian/note",
                    "type": "task",
                    "description": f"Follow up: {line_strip}",
                    "context": f"Commitment in [[{slug}]]",
                    "url": f"obsidian://open?vault=vault&file={urllib_parse_quote(slug)}"
                })
                break

    # 3. Suggest tasks related to developing, extending, connecting, or following up on new notes
    if is_new:
        category = "note"
        # Infer category from slug or frontmatter
        category_match = re.search(r"^category:\s*[\"']?\[\[([^\]]+)\]\][\"']?", content, re.MULTILINE)
        if category_match:
            category = category_match.group(1).strip().lower()
        elif "Thoughts/" in slug or "thoughts/" in slug:
            category = "thoughts"
        elif "Beliefs/" in slug or "beliefs/" in slug:
            category = "beliefs"
        elif "Concepts/" in slug or "concepts/" in slug:
            category = "concepts"
        elif "Contacts/" in slug or "contacts/" in slug:
            category = "contacts"
        elif "Meetings/" in slug or "meetings/" in slug:
            category = "meetings"
        elif "Readings/" in slug or "readings/" in slug:
            category = "readings"

        if category in ["thoughts", "opinions", "beliefs", "concepts", "note"]:
            candidates.append({
                "source": "Obsidian/note-new",
                "type": "development",
                "description": f"Develop note: [[{slug}]]",
                "context": f"Newly created {category} note [[{slug}]]",
                "url": f"obsidian://open?vault=vault&file={urllib_parse_quote(slug)}"
            })
            candidates.append({
                "source": "Obsidian/note-new",
                "type": "development",
                "description": f"Connect [[{slug}]] to related concepts in the vault",
                "context": f"Integrate newly created {category} note [[{slug}]]",
                "url": f"obsidian://open?vault=vault&file={urllib_parse_quote(slug)}"
            })
        elif category in ["contacts", "people", "organizations"]:
            candidates.append({
                "source": "Obsidian/note-new",
                "type": "follow-up",
                "description": f"Follow up with [[{slug}]]",
                "context": f"New contact profile created: [[{slug}]]",
                "url": f"obsidian://open?vault=vault&file={urllib_parse_quote(slug)}"
            })
        elif category in ["meetings", "readings", "sources", "emails"]:
            candidates.append({
                "source": "Obsidian/note-new",
                "type": "follow-up",
                "description": f"Process and extract key insights from [[{slug}]]",
                "context": f"Newly logged {category} [[{slug}]]",
                "url": f"obsidian://open?vault=vault&file={urllib_parse_quote(slug)}"
            })

def urllib_parse_quote(s):
    # Simple URL encoding for obsidian URI (only space and special chars)
    import urllib.parse
    return urllib.parse.quote(s)

def main():
    args = parse_args()
    vault_path = os.environ.get('OBSIDIAN_VAULT_PATH', '/home/justin.guest/Developer/obsidian-vault')
    
    # Calculate cutoff time in UTC
    now_utc = datetime.now(timezone.utc)
    lookback_cutoff = now_utc - timedelta(hours=args.lookback_hours)
    
    candidates = []
    
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Utilities", "Readwise", "archive"}
    
    if not os.path.exists(vault_path):
        if args.json:
            print(json.dumps([]))
        else:
            print("Vault path not found.")
        return
        
    for root, dirs, files in os.walk(vault_path):
        # In-place modify dirs to skip unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if not f.endswith(".md") or f == "RESOLVER.md":
                continue
                
            file_path = os.path.join(root, f)
            try:
                mtime_ts = os.path.getmtime(file_path)
                mtime_dt = datetime.fromtimestamp(mtime_ts, timezone.utc)
                if mtime_dt < lookback_cutoff:
                    continue
            except Exception:
                continue
                
            slug = get_slug(vault_path, file_path)
            if is_daily_note(slug, f) or is_granola_note(slug):
                continue
                
            content = ""
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as fh:
                    content = fh.read()
            except Exception:
                continue
                
            # Determine if new or modified
            created_dt = parse_creation_id(content)
            is_new = False
            if created_dt:
                is_new = (created_dt >= lookback_cutoff)
            else:
                # If no ID frontmatter, fallback to mtime (treat as modified unless mtime is very fresh and no daily note match)
                # But to be safe, treat as new only if creation ID matches lookback, or fallback to file creation time if OS supports it.
                # Since Justin's vault notes use YAML frontmatter ID for creation, checking `id` is highly reliable.
                pass
                
            scan_file_for_candidates(file_path, content, slug, is_new, lookback_cutoff, candidates)
            
    if args.json:
        print(json.dumps(candidates, indent=2))
    else:
        # Output Markdown list
        if not candidates:
            print("No action items or suggestions found in vault notes.")
        else:
            tasks_only = [c for c in candidates if c["type"] == "task"]
            devs_only = [c for c in candidates if c["type"] in ["development", "follow-up"]]
            
            if tasks_only:
                print("## Action items")
                for c in tasks_only:
                    print(f"- [Obsidian] {c['description']} | context: {c['context']}")
                    
            if devs_only:
                print("\n## Suggestions")
                for c in devs_only:
                    print(f"- [Obsidian] {c['description']} | context: {c['context']}")

if __name__ == "__main__":
    main()
