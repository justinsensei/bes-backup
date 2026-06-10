import os
import json
import re
from collections import defaultdict
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
    # Disabled. We now rely on Obsidian's Backlinks panel.
    return False

def scan_file_for_signals(file_path, content, entities, vault_path, event_date, enriched_counts):
    # Disabled. We now rely on Obsidian's Backlinks panel.
    return

def get_all_vault_filenames(vault_path):
    filenames = set()
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Utilities"}
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if f.endswith('.md'):
                filenames.add(f[:-3].lower())
    return filenames

def discover_plain_text_candidates(content, entities, all_vault_filenames):
    candidates = []
    
    # Remove markdown link brackets to avoid matching links (which are already handled)
    # e.g. [[Dave Rohrl]] -> Dave Rohrl
    content_no_links = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
    
    # Match two or three capitalized words
    # e.g., Samir Patwardhan, Atomic Jolt, Raptor Technologies
    matches_2 = re.findall(r'\b([A-Z][a-zA-Z]+)\s+([A-Z][a-zA-Z]+)\b', content_no_links)
    matches_3 = re.findall(r'\b([A-Z][a-zA-Z]+)\s+([A-Z][a-zA-Z]+)\s+([A-Z][a-zA-Z]+)\b', content_no_links)
    
    # Combine matches
    raw_names = []
    for m in matches_3:
        raw_names.append(" ".join(m))
    for m in matches_2:
        # Only add if not already part of a matched 3-word phrase
        name = " ".join(m)
        if not any(name in n for n in raw_names):
            raw_names.append(name)
            
    stop_words = {
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'obsidian', 'github', 'posthog', 'revenuecat', 'customer', 'linear', 'google', 'slack', 'zoom', 'teams', 'signlab', 'duolingo', 'powerschool',
        'revenue', 'product', 'sprint', 'engineering', 'design', 'marketing', 'roadmap', 'quarter', 'weekly', 'monthly', 'meeting', 'standup', 'sync',
        'project', 'note', 'thought', 'belief', 'concept', 'reference', 'decision', 'source', 'sources', 'agenda', 'action', 'items', 'next', 'steps',
        'yesterday', 'tomorrow', 'today', 'pittsburgh', 'united', 'states', 'canada', 'america', 'europe', 'brazil', 'pakistan', 'australia',
        'classroom', 'classrooms', 'lessons', 'lesson', 'teacher', 'teachers', 'student', 'students', 'school', 'schools', 'education', 'edtech',
        'app', 'web', 'mobile', 'native', 'stripe', 'payments', 'payment', 'flow', 'webinars', 'webinar', 'campaign', 'campaigns', 'advertising',
        'analytics', 'replays', 'replay', 'session', 'sessions', 'cohort', 'cohorts', 'retention', 'activation', 'onboarding', 'refactor',
        'heloc', 'citizens', 'bank', 'taxes', 'personal', 'work', 'log', 'logs', 'briefing', 'morning', 'thought', 'thoughts', 'opinions',
        'gratitude', 'thank', 'thanks', 'happy', 'good', 'great', 'awesome', 'amazing', 'beautiful', 'wonderful', 'perfect', 'excellent'
    }
    
    for name in raw_names:
        name_lower = name.lower()
        
        # Split and check if any word is a stop word or if the whole name is a stop word
        words = name_lower.split()
        if any(w in stop_words for w in words):
            continue
            
        # Skip if any word is less than 3 chars (except common initials)
        if any(len(w) < 3 for w in words if w not in ['de', 'st', 'jr', 'sr']):
            continue
            
        # Skip if it is already in the vault as a filename
        if name_lower in all_vault_filenames:
            continue
            
        # Skip if it's already an existing entity or alias
        if name_lower in entities:
            continue
            
        is_alias = False
        for ent_info in entities.values():
            if ent_info.get('aliases') and any(alias.lower() == name_lower for alias in ent_info['aliases']):
                is_alias = True
                break
        if is_alias:
            continue
            
        # Success! Found a new candidate
        ptype = 'person'
        org_indicators = ['school', 'group', 'company', 'foundation', 'club', 'association', 'lab', 'academy', 'technology', 'technologies', 'clinic', 'hospital', 'solutions', 'partners', 'associates', 'ventures', 'studios', 'consulting']
        if any(ind in name_lower for ind in org_indicators):
            ptype = 'organization'
            
        candidates.append({
            "name": name,
            "type": ptype
        })
        
    return candidates

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
            
        # Check if matches any existing entity's alias
        is_alias = False
        for ent_info in entities.values():
            if ent_info.get('aliases') and any(alias.lower() == link_key for alias in ent_info['aliases']):
                is_alias = True
                break
        if is_alias:
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
            
    # Find all plain-text contact candidates
    plain_candidates = discover_plain_text_candidates(content, entities, all_vault_filenames)
    for cand in plain_candidates:
        cand["context_file"] = os.path.relpath(file_path, vault_path)
        discovered.append(cand)
            
    return discovered

def scan_file_for_ambiguous_mentions(file_path, content, entities, key_to_paths, ambiguous_keys, vault_path):
    discovered = []
    
    # Remove pre-existing links to avoid matching inside brackets
    content_no_links = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
    
    for key in ambiguous_keys:
        # Ignore very short/junk keys
        if len(key.strip()) < 2 or not re.search(r'[a-zA-Z0-9]', key):
            continue
            
        pattern = rf'\b{re.escape(key)}\b'
        if re.search(pattern, content_no_links, re.IGNORECASE):
            # Resolve candidates: names of files that share this alias
            paths = key_to_paths[key.lower()]
            candidates = []
            for p in paths:
                candidates.append(os.path.basename(p)[:-3])
            
            discovered.append({
                "alias": key,
                "context_file": os.path.relpath(file_path, vault_path),
                "candidates": sorted(list(set(candidates)))
            })
    return discovered

def main():
    vault_path = os.environ.get('OBSIDIAN_VAULT_PATH', '/home/justin.guest/vault')
    now_dt = datetime.now()
    watermark_dt = load_watermark()
    
    print(f"Scanning vault signals since: {watermark_dt.isoformat()}")
    
    # Load all existing entities
    entities = get_existing_entities(vault_path)
    
    # Identify non-unique (ambiguous) aliases
    key_to_paths = defaultdict(list)
    for ent_key, ent_info in entities.items():
        key_to_paths[ent_info["title"].lower()].append(ent_info["path"])
        for alias in ent_info.get("aliases", []):
            key_to_paths[alias.lower()].append(ent_info["path"])
            
    ambiguous_keys = {k for k, paths in key_to_paths.items() if len(set(paths)) > 1}
    
    # Find all modified markdown files
    modified_files = []
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Utilities", "Readwise"}
    
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if f.endswith('.md'):
                file_path = os.path.join(root, f)
                rel = os.path.relpath(file_path, vault_path).replace("\\", "/")
                if rel.startswith(("Inputs/Readings/", "Inputs/Emails/", "Inputs/Slack/",
                                   "Logs/Sources/", "Logs/Readings/", "Logs/Emails/", "Logs/Slack/")):
                    continue
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime > watermark_dt:
                        modified_files.append(file_path)
                except Exception:
                    pass
                    
    print(f"Found {len(modified_files)} modified files to scan.")
    
    enriched_counts = {"person": 0, "organization": 0, "project": 0}
    all_discovered = []
    all_ambiguous = []
    
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
            
            # 2.5 Discover ambiguous mentions in plain text
            ambiguous = scan_file_for_ambiguous_mentions(file_path, content, entities, key_to_paths, ambiguous_keys, vault_path)
            all_ambiguous.extend(ambiguous)
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            
    # Deduplicate discovered candidates
    deduped_discovered = {}
    for item in all_discovered:
        name_key = item['name'].lower()
        if name_key not in deduped_discovered:
            deduped_discovered[name_key] = item
            
    discovered_list = list(deduped_discovered.values())
    
    # Deduplicate ambiguous mentions
    deduped_ambiguous = {}
    for item in all_ambiguous:
        key = (item['alias'].lower(), item['context_file'].lower())
        if key not in deduped_ambiguous:
            deduped_ambiguous[key] = item
            
    # Output report
    out = {
        "status": "ok",
        "scanned_files_count": len(modified_files),
        "enriched_counts": enriched_counts,
        "discovered_entities": {
            "people": [item for item in discovered_list if item['type'] == 'person'],
            "organizations": [item for item in discovered_list if item['type'] == 'organization']
        },
        "ambiguous_mentions": list(deduped_ambiguous.values())
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
