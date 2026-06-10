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
import requests
import urllib.parse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VAULT = Path("/home/justin.guest/vault")

def verify_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
        if not (parsed.scheme and parsed.netloc) or parsed.scheme not in ("http", "https"):
            return "Malformed URL"
    except Exception:
        return "Malformed URL"
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.head(url, headers=headers, timeout=3.0, allow_redirects=True, verify=False)
        if response.status_code in (404, 405):
            response = requests.get(url, headers=headers, timeout=3.0, allow_redirects=True, verify=False, stream=True)
            
        if response.status_code >= 400:
            return f"HTTP {response.status_code}"
        return None
    except requests.exceptions.Timeout:
        return "Timeout (3s)"
    except requests.exceptions.ConnectionError:
        return "Connection Error"
    except Exception as e:
        return f"Error: {type(e).__name__}"

def get_existing_entities(vault_path):
    entities = {}
    
    def parse_contact_file(file_path, filename):
        ptype = 'person'
        aliases = []
        title = filename[:-3]
        is_contact = False
        try:
            with open(file_path, encoding='utf-8', errors='replace') as file_obj:
                content = file_obj.read()
                m_cat = re.search(r'^category:\s*["\']?\[\[(People|Organizations)\]\]["\']?', content, re.MULTILINE)
                m_type = re.search(r'^type:\s*[\'"]?([a-zA-Z0-9_-]+)[\'"]?', content, re.MULTILINE)
                if m_cat or m_type:
                    is_contact = True
                if m_type:
                    ptype = m_type.group(1).strip()
                elif m_cat:
                    ptype = 'person' if m_cat.group(1) == 'People' else 'organization'
                m_aliases = re.search(r'^aliases:\s*\n((?:\s*-\s*.*?\n)+)', content, re.MULTILINE)
                if m_aliases:
                    aliases = [a.strip()[1:].strip().strip('"\'') for a in m_aliases.group(1).split('\n') if a.strip().startswith('-')]
        except Exception:
            pass
        return is_contact, ptype, title, aliases

    contacts_dir = os.path.join(vault_path, 'Contacts')
    if os.path.exists(contacts_dir):
        for f in os.listdir(contacts_dir):
            if f.endswith('.md'):
                file_path = os.path.join(contacts_dir, f)
                _, ptype, title, aliases = parse_contact_file(file_path, f)
                name_key = f[:-3].lower()
                entities[name_key] = {
                    "path": file_path,
                    "type": ptype,
                    "title": title,
                    "aliases": aliases
                }
                
    inbox_dir = os.path.join(vault_path, 'inbox')
    if os.path.exists(inbox_dir):
        for f in os.listdir(inbox_dir):
            if f.endswith('.md'):
                file_path = os.path.join(inbox_dir, f)
                is_contact, ptype, title, aliases = parse_contact_file(file_path, f)
                if is_contact:
                    name_key = f[:-3].lower()
                    entities[name_key] = {
                        "path": file_path,
                        "type": ptype,
                        "title": title,
                        "aliases": aliases
                    }
                
    projects_dir = os.path.join(vault_path, 'Notes', 'Projects')
    if os.path.exists(projects_dir):
        for f in os.listdir(projects_dir):
            if f.endswith('.md'):
                file_path = os.path.join(projects_dir, f)
                try:
                    with open(file_path, encoding='utf-8', errors='replace') as file_obj:
                        content = file_obj.read()
                        name_key = f[:-3].lower()
                        clean_name = re.sub(r'\s*\d{4,14}$', '', f[:-3]).lower().strip()
                        entities[name_key] = {
                            "path": file_path,
                            "type": "project",
                            "title": f[:-3],
                            "aliases": [clean_name] if clean_name != name_key else []
                        }
                except Exception:
                    pass
                    
    return entities

def auto_link_text(text, entities, current_file_title):
    # Find which keys are ambiguous (belonging to more than one distinct contact path)
    key_to_paths = defaultdict(list)
    for ent_key, ent_info in entities.items():
        key_to_paths[ent_info["title"].lower()].append(ent_info["path"])
        for alias in ent_info.get("aliases", []):
            key_to_paths[alias.lower()].append(ent_info["path"])
            
    ambiguous_keys = {k for k, paths in key_to_paths.items() if len(set(paths)) > 1}

    all_keys = []
    for ent_key, ent_info in entities.items():
        title = ent_info["title"]
        if title.lower() not in ambiguous_keys:
            all_keys.append((title, ent_info))
        for alias in ent_info.get("aliases", []):
            if len(alias) >= 3 and alias.lower() not in ambiguous_keys:
                all_keys.append((alias, ent_info))
                
    all_keys.sort(key=lambda x: len(x[0]), reverse=True)
    
    lines = text.split('\n')
    in_code_block = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block or line.strip().startswith('#'):
            continue
            
        links = []
        def mask_link(match):
            links.append(match.group(0))
            return f"__LINK_MASK_{len(links)-1}__"
            
        code_spans = []
        def mask_code(match):
            code_spans.append(match.group(0))
            return f"__CODE_MASK_{len(code_spans)-1}__"
            
        masked_line = re.sub(r'\[\[[^\]]+\]\]', mask_link, line)
        masked_line = re.sub(r'`[^`]+`', mask_code, masked_line)
        
        for key, ent_info in all_keys:
            if key.lower() == current_file_title.lower():
                continue
                
            pattern = rf'\b{re.escape(key)}\b'
            new_links = []
            
            def replace_key(match):
                matched_text = match.group(0)
                slug = os.path.basename(ent_info["path"])[:-3]
                if slug.lower() == matched_text.lower():
                    link_str = f"[[{slug}]]"
                else:
                    link_str = f"[[{slug}|{matched_text}]]"
                new_links.append(link_str)
                return f"__NEW_LINK_MASK_{len(new_links)-1}__"
                
            masked_line = re.sub(pattern, replace_key, masked_line, flags=re.IGNORECASE)
            
            for idx, link_str in enumerate(new_links):
                masked_line = masked_line.replace(f"__NEW_LINK_MASK_{idx}__", link_str)
                
        for idx, link_str in enumerate(links):
            masked_line = masked_line.replace(f"__LINK_MASK_{idx}__", link_str)
        for idx, code_str in enumerate(code_spans):
            masked_line = masked_line.replace(f"__CODE_MASK_{idx}__", code_str)
            
        lines[i] = masked_line
        
    return '\n'.join(lines)

def auto_link_recent_daily_notes(vault_path, entities):
    daily_notes_dir = Path(vault_path) / "Daily Notes"
    if not daily_notes_dir.exists():
        return
        
    print("Auto-linking recent daily notes...")
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)
    
    for path in daily_notes_dir.glob("*.md"):
        try:
            mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
            if mtime > seven_days_ago:
                text = path.read_text(encoding="utf-8", errors="replace")
                
                has_frontmatter = False
                fm_content = ""
                body_content = text
                if text.startswith("---"):
                    fm_end = text.find("\n---", 3)
                    if fm_end > 0:
                        has_frontmatter = True
                        fm_content = text[:fm_end+4]
                        body_content = text[fm_end+4:]
                        
                linked_body = auto_link_text(body_content, entities, path.name[:-3])
                if linked_body != body_content:
                    new_text = fm_content + linked_body
                    path.write_text(new_text, encoding="utf-8")
                    print(f"  Auto-linked contacts in daily note: {path.name}")
        except Exception as e:
            print(f"  Error auto-linking daily note {path.name}: {e}")

def reconcile_granola_meetings(vault_path):
    entities = get_existing_entities(vault_path)
    meetings_dir = Path(vault_path) / "meetings"
    meetings_dir.mkdir(parents=True, exist_ok=True)
    
    dest_dir = Path(vault_path) / "Logs" / "Meetings"
    dest_dir.mkdir(parents=True, exist_ok=True)
        
    print("Reconciling meetings from Granola...")
    
    # Pre-scan vault for existing IDs to avoid collisions
    existing_ids = set()
    skip_dirs = {"Readwise", "Utilities", ".git", ".trash", ".cursor", ".claude", "sources", "Daily Notes"}
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
                    body_content = text[fm_end+4:].lstrip()
                    
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
                daily_note = f"[[Daily Notes/{date_str}-{weekday_lower}|{date_str} {weekday_cap}]]"
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
                
            # Auto-link known entities in the meeting body
            linked_body = auto_link_text(body_content, entities, filename[:-3])
            if linked_body != body_content:
                body_content = linked_body
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

# 1.5 Auto-link recent daily notes
entities = get_existing_entities(VAULT)
auto_link_recent_daily_notes(VAULT, entities)

# 2. Walk the vault to detect ID conflicts, missing ID, missing daily_note, ghost links, and build graph for orphan notes
id_to_paths = defaultdict(list)
missing_ids = []
missing_daily_notes = []

# Build catalogs of all existing files and directories across the entire vault (no skipping) for link resolution
existing_rel_paths = {}      # lowercase rel_path -> original rel_path
existing_basenames = defaultdict(list)  # lowercase basename -> list of original rel_paths

for root, dirs, files in os.walk(VAULT):
    for d in dirs:
        full_path = Path(root) / d
        rel_path = full_path.relative_to(VAULT)
        rel_str = str(rel_path).replace("\\", "/")
        existing_rel_paths[rel_str.lower()] = rel_str
        
    for f in files:
        full_path = Path(root) / f
        rel_path = full_path.relative_to(VAULT)
        rel_str = str(rel_path).replace("\\", "/")
        existing_rel_paths[rel_str.lower()] = rel_str
        
        f_lower = f.lower()
        existing_basenames[f_lower].append(rel_str)
        if f_lower.endswith(".md"):
            existing_basenames[f_lower[:-3]].append(rel_str)

# Ghost links detection variables
ghost_links = defaultdict(set)
incoming_links = defaultdict(set)
outgoing_links = defaultdict(set)
all_audited_notes = set()

# Folders to skip for manual checks
skip_dirs = {"Readwise", "Utilities", ".git", ".trash", ".cursor", ".claude", "sources", "Daily Notes"}

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
        rel_str_f = str(rel_path).replace("\\", "/")
        all_audited_notes.add(rel_str_f)
        
        if note_id:
            id_to_paths[note_id].append(rel_path)
        else:
            missing_ids.append(rel_path)
            
        if not daily_note or "[[" not in daily_note:
            missing_daily_notes.append(rel_path)
            
        # Parse wikilinks
        wikilinks = re.findall(r'\[\[([^\]]+)\]\]', text)
        for link in wikilinks:
            # Parse link target (before '#' or '|')
            target_part = link.split('|')[0].strip()
            file_target = target_part.split('#')[0].strip()
            
            if not file_target:
                continue
                
            norm_target = file_target.replace("\\", "/").lower().strip()
            resolved = None
            if norm_target in existing_rel_paths:
                resolved = existing_rel_paths[norm_target]
            elif (norm_target + ".md") in existing_rel_paths:
                resolved = existing_rel_paths[norm_target + ".md"]
            elif norm_target in existing_basenames:
                resolved = existing_basenames[norm_target][0]
            elif (norm_target + ".md") in existing_basenames:
                resolved = existing_basenames[norm_target + ".md"][0]
                
            if not resolved:
                ghost_links[rel_str_f].add(file_target)
            else:
                outgoing_links[rel_str_f].add(resolved)
                incoming_links[resolved].add(rel_str_f)

# 2.5 Citation & Web Source Validation
citation_issues = defaultdict(list)
sources_dir = VAULT / "Logs" / "Sources"
url_cache = {}

if sources_dir.exists():
    print("Auditing Citation & Web Sources in Logs/Sources/...")
    all_source_files = sorted(sources_dir.glob("**/*.md"))
    unique_urls = set()
    file_to_urls = {}
    
    for path in all_source_files:
        rel_src_path = path.relative_to(VAULT)
        rel_src_str = str(rel_src_path).replace("\\", "/")
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            # Find standard markdown links [Text](URL)
            md_links = re.findall(r'\[([^\]]*)\]\(((?:https?://|www\.)[^\s\)]+)\)', content)
            
            urls_in_file = []
            for text, url in md_links:
                if url.startswith("www."):
                    url = "https://" + url
                unique_urls.add(url)
                urls_in_file.append(url)
            if urls_in_file:
                file_to_urls[rel_src_str] = urls_in_file
        except Exception as e:
            print(f"  Error reading source file {path.name}: {e}")
            
    # Check URLs in parallel using ThreadPoolExecutor
    if unique_urls:
        print(f"  Verifying {len(unique_urls)} unique URLs in parallel...")
        from concurrent.futures import ThreadPoolExecutor
        
        def check_one(url):
            return url, verify_url(url)
            
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(check_one, url) for url in unique_urls]
            for fut in futures:
                try:
                    url, err = fut.result()
                    url_cache[url] = err
                except Exception:
                    pass
                    
    # Map results back to files
    for rel_src_str, urls in file_to_urls.items():
        for url in urls:
            err = url_cache.get(url)
            if err:
                citation_issues[rel_src_str].append((url, err))

# 3. Format output for vault_hygiene_cron.py
lines = []

# ID Conflicts
id_conflicts = {nid: paths for nid, paths in id_to_paths.items() if len(paths) > 1}
if id_conflicts:
    lines.append("## 🔴 ID conflicts")
    for nid, paths in sorted(id_conflicts.items()):
        for p in paths:
            lines.append(f"  - {p}: id={nid} shared by {len(paths)} notes")

# Check for non-unique aliases
alias_to_paths = defaultdict(list)
for ent_key, ent_info in entities.items():
    title_lower = ent_info["title"].lower()
    alias_to_paths[title_lower].append(ent_info["path"])
    for alias in ent_info.get("aliases", []):
        alias_to_paths[alias.lower()].append(ent_info["path"])

duplicate_aliases = []
for alias, paths in sorted(alias_to_paths.items()):
    # Ignore blank, single-character, or non-alphanumeric aliases (e.g. '--' or junk)
    if len(alias.strip()) < 2 or not re.search(r'[a-zA-Z0-9]', alias):
        continue
    unique_paths = list(set(paths))
    if len(unique_paths) > 1:
        shared_files = ", ".join(str(Path(p).relative_to(VAULT)) for p in unique_paths)
        duplicate_aliases.append(f"  - {alias!r} shared by: {shared_files}")

if duplicate_aliases:
    lines.append("\n## 🔴 Non-unique aliases")
    lines.extend(duplicate_aliases)

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

# ⚠️ Ghost Links
if ghost_links:
    lines.append("\n## ⚠️ Ghost Links")
    for p in sorted(ghost_links.keys()):
        for target in sorted(list(ghost_links[p])):
            lines.append(f"  - {p} links to non-existent: [[{target}]]")

# ⚠️ Orphan Notes
orphan_notes = []
for note in sorted(list(all_audited_notes)):
    if len(incoming_links[note]) == 0 and len(outgoing_links[note]) == 0:
        orphan_notes.append(note)

if orphan_notes:
    lines.append("\n## ⚠️ Orphan Notes")
    for note in orphan_notes:
        lines.append(f"  - {note}")

# ⚠️ Citation & Source Issues
if citation_issues:
    lines.append("\n## ⚠️ Citation & Source Issues")
    for p in sorted(citation_issues.keys()):
        for url, err in citation_issues[p]:
            lines.append(f"  - {p}: [{err}] {url}")

if lines:
    print("\n".join(lines))
else:
    print("✅ Vault looks clean — no issues found.")

# 4. Trigger semantic pointer indexing to automatically update embeddings
print("\nTriggering semantic indexing for new/modified files...")
try:
    script_path = os.path.expanduser("~/.hermes/scripts/semantic_pointer.py")
    if os.path.exists(script_path):
        result = subprocess.run(["python3", script_path, "index"], capture_output=True, text=True, timeout=500, check=True)
        print("✅ Semantic indexing completed.")
        if result.stdout:
            print(result.stdout.strip())
    else:
        print("⚠️ Semantic pointer script not found.")
except Exception as e:
    print(f"⚠️ Failed to run semantic indexing: {e}")
