import os
import json
import re
from datetime import datetime, timedelta

def load_watermark():
    path = os.path.expanduser('~/.hermes/state/vault_signals_watermark.json')
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
                return datetime.fromisoformat(data['watermark'])
        except Exception:
            pass
    # Default to yesterday
    return datetime.now() - timedelta(days=1)

def save_watermark(now_dt):
    path = os.path.expanduser('~/.hermes/state/vault_signals_watermark.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump({"watermark": now_dt.isoformat()}, f, indent=2)

def extract_date_from_file(file_path, content):
    # Try parsing YYYY-MM-DD from frontmatter daily_note
    # e.g., daily_note: "[[2026-06-08-monday]]"
    m_daily = re.search(r'daily_note:\s*["\']?\[\[(?:Daily Notes/)?(\d{4}-\d{2}-\d{2})[^\]]*\]\]["\']?', content)
    if m_daily:
        return m_daily.group(1)
        
    # Try parsing from filename YYYY-MM-DD
    filename = os.path.basename(file_path)
    m_file = re.search(r'^(\d{4}-\d{2}-\d{2})', filename)
    if m_file:
        return m_file.group(1)
        
    # Fallback to mtime
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

def get_existing_entities(vault_path):
    entities = {}
    
    # Helper to parse a contact file
    def parse_contact_file(file_path, filename):
        ptype = 'person'
        aliases = []
        title = filename[:-3]
        is_contact = False
        try:
            with open(file_path, encoding='utf-8', errors='replace') as file_obj:
                content = file_obj.read()
                
                # Check if it's a contact (important for inbox files)
                m_cat = re.search(r'^category:\s*["\']?\[\[(People|Organizations)\]\]["\']?', content, re.MULTILINE)
                m_type = re.search(r'^type:\s*[\'"]?([a-zA-Z0-9_-]+)[\'"]?', content, re.MULTILINE)
                
                if m_cat or m_type:
                    is_contact = True
                    
                if m_type:
                    ptype = m_type.group(1).strip()
                elif m_cat:
                    ptype = 'person' if m_cat.group(1) == 'People' else 'organization'
                    
                # Parse aliases
                m_aliases = re.search(r'^aliases:\s*\n((?:\s*-\s*.*?\n)+)', content, re.MULTILINE)
                if m_aliases:
                    aliases = [a.strip()[1:].strip().strip('"\'') for a in m_aliases.group(1).split('\n') if a.strip().startswith('-')]
        except Exception:
            pass
        return is_contact, ptype, title, aliases

    # 1. Contacts (People and Organizations)
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
                
    # Also scan inbox for untriaged contacts
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
                
    # 2. Projects (from Notes/Projects/)
    projects_dir = os.path.join(vault_path, 'Notes', 'Projects')
    if os.path.exists(projects_dir):
        for f in os.listdir(projects_dir):
            if f.endswith('.md'):
                file_path = os.path.join(projects_dir, f)
                try:
                    with open(file_path, encoding='utf-8', errors='replace') as file_obj:
                        content = file_obj.read()
                        name_key = f[:-3].lower()
                        # Clean up trailing date suffix if present in name_key
                        # e.g., adhd treatment 2026 -> adhd treatment
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

def add_timeline_entry(entity_path, event_date, source_rel_path, source_title):
    try:
        with open(entity_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # Check if already mentioned
        # e.g., if source_rel_path is in the file
        slug = source_rel_path[:-3].replace(os.path.sep, '/')
        if slug in content:
            return False # already cited
            
        # Find ## Timeline section
        timeline_match = re.search(r'^## Timeline\s*$', content, re.MULTILINE)
        if not timeline_match:
            # If no timeline, append it at the bottom
            content += f"\n\n## Timeline\n- {event_date} | Mentioned in [[{slug}|{source_title}]]\n"
        else:
            idx = timeline_match.end()
            # Parse everything after ## Timeline
            tail = content[idx:]
            
            # Find all bullets under ## Timeline
            lines = tail.split('\n')
            bullets = []
            other_lines = []
            reached_non_timeline = False
            
            for line in lines:
                striped = line.strip()
                if reached_non_timeline:
                    other_lines.append(line)
                elif striped.startswith('-'):
                    bullets.append(line)
                elif striped == '':
                    continue # skip extra blank lines under Timeline
                elif striped.startswith('---') or striped.startswith('#'):
                    # Reached divider or another heading, exit timeline section
                    reached_non_timeline = True
                    other_lines.append(line)
                else:
                    # Some other non-bullet content, means we exited the timeline section
                    reached_non_timeline = True
                    other_lines.append(line)
                    
            # Add the new bullet at the top of the bullets list (reverse chronological)
            new_bullet = f"- {event_date} | Mentioned in [[{slug}|{source_title}]]"
            bullets.insert(0, new_bullet)
            
            # Reconstruct tail: one blank line after ## Timeline, then bullets, then one blank line, then the rest
            new_tail_parts = []
            new_tail_parts.append("") # exactly one empty line after heading
            for b in bullets:
                new_tail_parts.append(b)
                
            if other_lines:
                new_tail_parts.append("")
                new_tail_parts.extend(other_lines)
            else:
                new_tail_parts.append("") # trailing newline
                
            content = content[:idx] + '\n'.join(new_tail_parts)
            
        with open(entity_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error enriching {entity_path}: {e}")
        return False

def scan_file_for_signals(file_path, content, entities, vault_path, event_date, enriched_counts):
    rel_path = os.path.relpath(file_path, vault_path)
    file_title = os.path.basename(file_path)[:-3]
    
    # Don't enrich the file with itself
    file_key = file_title.lower()
    
    # Scanned content to search
    scanned_text = content.lower()
    
    for ent_key, ent_info in entities.items():
        if ent_info['path'] == file_path:
            continue
            
        # Match by exact name or aliases
        matched = False
        # 1. Match by wikilink: [[Dave Rohrl]] or [[Contacts/Dave Rohrl]]
        slug_name = os.path.basename(ent_info['path'])[:-3]
        link_patterns = [
            f"[[{slug_name.lower()}]]",
            f"[[contacts/{slug_name.lower()}]]",
            f"[[{ent_key}]]"
        ]
        for pattern in link_patterns:
            if pattern in scanned_text:
                matched = True
                break
                
        # 2. Match by exact text phrase (boundaries around name)
        if not matched:
            name_pattern = rf"\b{re.escape(ent_key)}\b"
            if re.search(name_pattern, scanned_text):
                matched = True
                
        # 3. Match by aliases
        if not matched and ent_info['aliases']:
            for alias in ent_info['aliases']:
                alias_pattern = rf"\b{re.escape(alias.lower())}\b"
                if re.search(alias_pattern, scanned_text):
                    matched = True
                    break
                    
        if matched:
            # Enrich existing note
            success = add_timeline_entry(ent_info['path'], event_date, rel_path, file_title)
            if success:
                enriched_counts[ent_info['type']] = enriched_counts.get(ent_info['type'], 0) + 1

def get_all_vault_filenames(vault_path):
    filenames = set()
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Utilities"}
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if f.endswith('.md'):
                filenames.add(f[:-3].lower())
    return filenames

def scan_file_for_unresolved_links(file_path, content, entities, vault_path, all_vault_filenames):
    discovered = []
    
    # Find all [[Link]] matches
    # e.g., [[Jeev Sahoo]] or [[The Waldorf School]] or [[Contacts/Name]]
    links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)
    
    # Excluded folders / system categories
    excluded_names = {
        'notes', 'memory', 'projects', 'thoughts', 'references', 'readings', 
        'meetings', 'people', 'organizations', 'daily notes', 'utilities', 
        'contacts', 'sources', 'notepad', 'state'
    }
    
    for link in links:
        link_clean = link.strip()
        if link_clean.startswith('Contacts/'):
            link_name = link_clean[9:]
        else:
            link_name = link_clean
            
        link_name_lower = link_name.lower()
        
        # Skip system names and category names
        if link_name_lower in excluded_names:
            continue
            
        # Skip if it contains a slash / (which means it links to a specific folder/sub-note)
        if '/' in link_name:
            continue
            
        # Skip image links and binary attachments
        if link_name_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.svg', '.mp3', '.mp4')):
            continue
            
        if 'pasted image' in link_name_lower or link_name_lower.startswith(('image ', 'drawing ')):
            continue
            
        # Skip daily notes (which look like dates)
        if re.match(r'^\d{4}-\d{2}-\d{2}', link_name):
            continue
            
        # Check if exists anywhere in vault or in entities
        link_key = link_name.lower()
        if link_key in all_vault_filenames:
            continue
            
        if link_key not in entities:
            # Unresolved!
            # Basic type inference
            ptype = 'person'
            # If name has typical organization words, default to organization
            org_indicators = ['school', 'group', 'company', 'foundation', 'club', 'association', 'lab', 'academy', 'technology', 'technologies', 'clinic', 'hospital']
            if any(ind in link_key for ind in org_indicators):
                ptype = 'organization'
            elif len(link_name.split()) > 3:
                # Long name is likely an organization
                ptype = 'organization'
                
            discovered.append({
                "name": link_name,
                "type": ptype,
                "context_file": os.path.relpath(file_path, vault_path)
            })
            
    return discovered

def main():
    vault_path = os.environ.get('OBSIDIAN_VAULT_PATH', '/home/justin.guest/vault')
    now_dt = datetime.now()
    watermark_dt = load_watermark()
    
    print(f"Scanning vault signals since: {watermark_dt.isoformat()}")
    
    # Load all existing entities
    entities = get_existing_entities(vault_path)
    
    # Find all modified markdown files
    modified_files = []
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Utilities"}
    
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if f.endswith('.md'):
                file_path = os.path.join(root, f)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime > watermark_dt:
                        modified_files.append(file_path)
                except Exception:
                    pass
                    
    print(f"Found {len(modified_files)} modified files to scan.")
    
    enriched_counts = {"person": 0, "organization": 0, "project": 0}
    all_discovered = []
    
    # Build list of all existing vault filenames
    all_vault_filenames = get_all_vault_filenames(vault_path)
    
    for file_path in modified_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            event_date = extract_date_from_file(file_path, content)
            
            # 1. Enrich existing entities based on mentions
            scan_file_for_signals(file_path, content, entities, vault_path, event_date, enriched_counts)
            
            # 2. Discover unresolved links as candidates
            unresolved = scan_file_for_unresolved_links(file_path, content, entities, vault_path, all_vault_filenames)
            all_discovered.extend(unresolved)
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            
    # Deduplicate discovered candidates
    deduped_discovered = {}
    for item in all_discovered:
        name_key = item['name'].lower()
        if name_key not in deduped_discovered:
            deduped_discovered[name_key] = item
            
    discovered_list = list(deduped_discovered.values())
    
    # Output report
    out = {
        "status": "ok",
        "scanned_files_count": len(modified_files),
        "enriched_counts": enriched_counts,
        "discovered_entities": {
            "people": [item for item in discovered_list if item['type'] == 'person'],
            "organizations": [item for item in discovered_list if item['type'] == 'organization']
        }
    }
    
    print(json.dumps(out, indent=2))
    
    # Save the output under ~/.hermes/morning-briefing/vault_signals_last_run.json
    # so we can easily inject it into the morning briefing!
    cache_dir = os.path.expanduser('~/.hermes/morning-briefing')
    os.makedirs(cache_dir, exist_ok=True)
    with open(os.path.join(cache_dir, 'vault_signals_last_run.json'), 'w') as f:
        json.dump(out, f, indent=2)
        
    save_watermark(now_dt)

if __name__ == "__main__":
    main()
