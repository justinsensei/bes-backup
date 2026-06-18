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
import json
from collections import defaultdict
from pathlib import Path
import requests
import urllib.parse
import urllib3

from vault_entities import get_existing_entities, match_projects
from integrate_entities import integrate_ingest, append_meeting_related

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/justin.guest/Developer/obsidian-vault"))


def inputs_base(vault_path):
    vault = Path(vault_path)
    if (vault / "Inputs").exists():
        return vault / "Inputs"
    return vault / "Logs"


def readings_dirs(vault_path):
    vault = Path(vault_path)
    dirs = []
    for candidate in [
        vault / "Inputs" / "Readings",
        vault / "Logs" / "Readings",
        vault / "Logs" / "Sources",
    ]:
        if candidate.exists():
            dirs.append(candidate)
    return dirs


def expected_folder_prefix(category, vault_path):
    base = str(inputs_base(vault_path)).replace("\\", "/")
    rules = {
        "Readings": f"{base}/Readings/",
        "Meetings": f"{base}/Meetings/",
        "Emails": f"{base}/Emails/",
        "Slack": f"{base}/Slack/",
        "Scraps": "inbox/",
        "Sources": "Notes/",
        "Notes": "Notes/",
        "Thoughts": "Notes/",
        "Concepts": "Notes/",
        "Beliefs": "Notes/",
        "References": "Notes/",
        "Decisions": "Notes/",
        "Memories": "Notes/",
        "Projects": "Notes/Projects/",
    }
    return rules.get(category)


def acceptable_folder_prefixes(category, vault_path):
    vault = Path(vault_path)
    base_inputs_path = inputs_base(vault_path)
    if base_inputs_path.is_absolute():
        base_inputs_path = base_inputs_path.relative_to(vault_path)
    base_inputs = str(base_inputs_path).replace("\\", "/")
    
    base_logs_path = vault / "Logs"
    if base_logs_path.is_absolute():
        base_logs_path = base_logs_path.relative_to(vault_path)
    base_logs = str(base_logs_path).replace("\\", "/")
    
    input_cats = {"Readings", "Meetings", "Emails", "Slack"}
    if category in input_cats:
        prefixes = [f"{base_inputs}/{category}/"]
        if (vault / "Logs").exists() and base_inputs != base_logs:
            prefixes.append(f"{base_logs}/{category}/")
        if category == "Readings":
            prefixes.extend([f"{base_logs}/Sources/", f"{base_logs}/Readings/"])
        return prefixes
    expected = expected_folder_prefix(category, vault_path)
    return [expected] if expected else []


def parse_category(fm_raw):
    m = re.search(r'^category:\s*["\']?\[\[([^\]]+)\]\]["\']?', fm_raw, re.MULTILINE)
    return m.group(1).strip() if m else ""


def is_immutable_input_path(rel_str):
    parts = rel_str.replace("\\", "/").split("/")
    if len(parts) < 2:
        return False
    top = parts[0]
    if top not in ("Inputs", "Logs"):
        return False
    sub = parts[1]
    return sub in ("Readings", "Emails", "Slack", "Sources")

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
        
        new_links = []
        for key, ent_info in all_keys:
            if key.lower() == current_file_title.lower():
                continue
                
            pattern = rf'\b{re.escape(key)}\b'
            
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
    daily_notes_dir = Path(vault_path) / "Notes" / "Daily Notes"
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
    
    dest_dir = inputs_base(vault_path) / "Meetings"
    dest_dir.mkdir(parents=True, exist_ok=True)
        
    print("Reconciling meetings from Granola...")
    
    # Pre-scan vault for existing IDs to avoid collisions
    existing_ids = set()
    skip_dirs = {"Inputs", "Readwise", "Utilities", ".git", ".trash", ".cursor", ".claude", "Daily Notes"}
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

    src_dirs = [(meetings_dir, True), (dest_dir, False)]
    legacy_dest = Path(vault_path) / "Logs" / "Meetings"
    if legacy_dest.exists() and legacy_dest.resolve() != dest_dir.resolve():
        src_dirs.append((legacy_dest, False))

    for src_dir, is_raw in src_dirs:
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
                daily_note = f"[[{date_str} {weekday_cap}]]"
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

            match_text = filename + "\n" + body_content
            matched_projects, _ = match_projects(match_text, entities)
            for proj in matched_projects:
                new_body = append_meeting_related(body_content, proj["title"])
                if new_body != body_content:
                    body_content = new_body
                    needs_update = True
                
            if is_raw or needs_update:
                new_fm = (
                    f"---\nid: {note_id}\n"
                    f"daily_note: '{daily_note}'\n"
                    f"category: \"[[Meetings]]\"\n"
                    f"---\n"
                )
                new_text = new_fm + body_content
                dest_path = dest_dir / filename
                dest_path.write_text(new_text, encoding="utf-8")
                rel_dest = str(dest_path.relative_to(vault_path)).replace("\\", "/")

                try:
                    integrate_report = integrate_ingest(vault_path, rel_dest)
                    updated = integrate_report.get("updated", {})
                    parts = updated.get("projects", []) + updated.get("contacts", [])
                    if parts:
                        print(f"  integrate-entities → {', '.join(parts)}")
                except Exception as e:
                    print(f"  integrate-entities error for {filename}: {e}")
                
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

# ==========================================
# Filename Capitalization & Link Healing
# ==========================================

ACRONYMS = {
    "ai": "AI",
    "adhd": "ADHD",
    "b2c": "B2C",
    "b2b": "B2B",
    "ab": "AB",
    "pm": "PM",
    "qa": "QA",
    "ci": "CI",
    "cd": "CD",
    "gtm": "GTM",
    "asl": "ASL",
    "dau": "DAU",
    "wsp": "WSP",
    "sp": "SP",
    "pr": "PR",
    "okr": "OKR",
    "okrs": "OKRs",
    "k12": "K12",
    "edtech": "EdTech",
    "sped": "SPED",
}

PROPER_NOUNS = {
    "amazon": "Amazon",
    "costco": "Costco",
    "novak": "Novak",
    "posthog": "PostHog",
    "signlab": "SignLab",
    "smartpass": "SmartPass",
    "duolingo": "Duolingo",
    "powerschool": "PowerSchool",
    "lingvano": "Lingvano",
    "raptor": "Raptor",
    "breezeway": "Breezeway",
    "granola": "Granola",
    "readwise": "Readwise",
    "slack": "Slack",
    "telegram": "Telegram",
    "gmail": "Gmail",
    "google": "Google",
    "linear": "Linear",
    "github": "GitHub",
    "git": "Git",
    "typescript": "TypeScript",
    "python": "Python",
    "javascript": "JavaScript",
    "postgres": "Postgres",
    "postgresql": "PostgreSQL",
    "asl": "ASL",
    "da": "da",
    "van": "van",
}

BLACKLIST_WORDS = {
    "learning", "school", "pittsburgh", "partner", "technologies", "smartpass", 
    "design", "development", "tech", "software", "engineering", "product", 
    "management", "doctors", "game", "mobile", "group", "health", "insurance", 
    "academy", "training", "solutions", "classroom", "production", "video",
    "as", "a", "an", "the", "on", "and", "or", "but", "with", "from", "for", 
    "in", "at", "by", "of", "to", "up", "down", "out", "over", "under", "about",
    "increases", "agility", "games", "language", "zero", "marginal", "cost",
    "breaks", "coding", "key", "learnings", "website", "test", "testing",
    "thoughts", "so", "far", "why", "hallucinates", "new", "kind", "interface",
    "alternatives", "special", "ed", "strategy", "notifications", "fit", "doesn"
}

def heal_vault_filename_capitalizations(vault_path):
    vault = Path(vault_path)
    contacts_dir = vault / "Notes" / "Contacts"
    
    contact_words = set()
    if contacts_dir.exists():
        for f in os.listdir(contacts_dir):
            if f.endswith(".md"):
                name = f[:-3]
                for w in re.split(r"[-_\s]+", name):
                    if w:
                        contact_words.add(w.lower())
                        
    contact_words = contact_words - BLACKLIST_WORDS
    
    def clean_filename(filename: str) -> str:
        base, ext = os.path.splitext(filename)
        if ext != ".md":
            return filename
            
        words = base.split(" ")
        new_words = []
        for w in words:
            w_clean = re.sub(r"[^\w/]", "", w)
            w_lower = w_clean.lower()
            
            if w_lower in ACRONYMS:
                val = ACRONYMS[w_lower]
                w_new = w.replace(w_clean, val)
            elif w_lower in PROPER_NOUNS:
                val = PROPER_NOUNS[w_lower]
                w_new = w.replace(w_clean, val)
            elif w_lower in contact_words:
                val = w_clean.capitalize()
                w_new = w.replace(w_clean, val)
            else:
                w_new = w
            new_words.append(w_new)
            
        new_base = " ".join(new_words)
        new_base = re.sub(r"\bdoesn\s+t\b", "doesn't", new_base, flags=re.IGNORECASE)
        return new_base + ext

    renames = {}
    title_mapping = {}
    ignore_dirs = {"Inputs", "Readwise", "Templates", "Daily Notes", "Categories", ".git", ".trash", ".cursor", ".claude", "Copilot"}
    
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ignore_dirs]
        for f in files:
            if f.endswith(".md"):
                old_path = Path(root) / f
                new_f = clean_filename(f)
                if new_f != f:
                    new_path = Path(root) / new_f
                    renames[old_path] = new_path
                    title_mapping[f[:-3].lower()] = new_f[:-3]
                    
    if renames:
        print(f"Auto-fixing {len(renames)} incorrectly capitalized file names on disk...")
        for old_path, new_path in renames.items():
            try:
                old_path.rename(new_path)
                print(f"  Renamed: {old_path.name} -> {new_path.name}")
            except Exception as e:
                print(f"  Error renaming {old_path.name}: {e}")
                
        # Heal Wikilinks inside all markdown files
        link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
        
        def heal_links_in_text(content):
            def replace_link(match):
                inner = match.group(1)
                if "|" in inner:
                    target_part, display = inner.split("|", 1)
                else:
                    target_part, display = inner, None
                    
                if "#" in target_part:
                    base_target, section = target_part.split("#", 1)
                    section = "#" + section
                else:
                    base_target, section = target_part, ""
                    
                base_target_clean = base_target.strip()
                base_target_lower = base_target_clean.lower()
                target_filename_lower = os.path.basename(base_target_lower)
                
                if target_filename_lower in title_mapping:
                    new_target_title = title_mapping[target_filename_lower]
                    dir_part = os.path.dirname(base_target_clean)
                    new_base_target = os.path.join(dir_part, new_target_title) if dir_part else new_target_title
                    
                    if display:
                        return f"[[{new_base_target}{section}|{display}]]"
                    else:
                        return f"[[{new_base_target}{section}]]"
                return match.group(0)
                
            return link_pattern.sub(replace_link, content)
            
        modified_files = 0
        for root, dirs, files in os.walk(vault):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ignore_dirs]
            for f in files:
                if f.endswith(".md"):
                    path = Path(root) / f
                    try:
                        content = path.read_text(encoding="utf-8", errors="replace")
                        new_content = heal_links_in_text(content)
                        if new_content != content:
                            path.write_text(new_content, encoding="utf-8")
                            modified_files += 1
                    except Exception as e:
                        print(f"  Error healing links in {f}: {e}")
        if modified_files:
            print(f"Auto-healed wikilinks in {modified_files} files to match new capitalization.")

# Run filename capitalization healer first
heal_vault_filename_capitalizations(VAULT)

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
id_to_rel_path_catalog = {}  # 14-digit ID suffix -> original rel_path

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
            # Catalog 14-digit ID suffix for robust resolution fallback
            id_match = re.search(r"(\d{14})", f)
            if id_match:
                id_to_rel_path_catalog[id_match.group(1)] = rel_str

# Ghost links detection variables
ghost_links = defaultdict(set)
incoming_links = defaultdict(set)
outgoing_links = defaultdict(set)
all_audited_notes = set()

skip_dirs = {"Inputs", "Readwise", "Utilities", ".git", ".trash", ".cursor", ".claude", "Daily Notes"}

wrong_folder = []
source_linkage_issues = []
legacy_path_links = defaultdict(set)
category_fixes = []

for root, dirs, files in os.walk(VAULT):
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
    for f in sorted(files):
        if not f.endswith(".md") or f == "RESOLVER.md":
            continue
        path = Path(root) / f
        text = path.read_text(encoding="utf-8", errors="replace")
        
        note_id = ""
        daily_note = ""
        category = ""
        fm_raw = ""
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end > 0:
                fm_raw = text[3:end]
                # Auto-wrap unwrapped wikilinks in frontmatter to prevent YAML parse errors
                new_fm_raw = re.sub(r"^([a-zA-Z0-9_-]+):\s*(\[\[[^\]\n]+\]\])\s*$", r'\1: "\2"', fm_raw, flags=re.MULTILINE)
                if new_fm_raw != fm_raw:
                    new_text = f"---\n{new_fm_raw}\n---\n" + text[end + 4:]
                    path.write_text(new_text, encoding="utf-8")
                    fm_raw = new_fm_raw
                    text = new_text
                    print(f"  Healed unwrapped frontmatter wikilink in: {f}")
                
                id_match = re.search(r"^id:\s*[\"']?(\d+)[\"']?", fm_raw, re.MULTILINE)
                dn_match = re.search(r"^daily_note:\s*[\"']?([^\"'\n]+)[\"']?", fm_raw, re.MULTILINE)
                if id_match:
                    note_id = id_match.group(1).strip()
                if dn_match:
                    daily_note = dn_match.group(1).strip()
                category = parse_category(fm_raw)

        rel_path = path.relative_to(VAULT)
        rel_str_f = str(rel_path).replace("\\", "/")
        all_audited_notes.add(rel_str_f)

        if category and rel_str_f.startswith(("Inputs/Readings/", "Logs/Readings/", "Logs/Sources/")):
            if category == "Sources":
                new_fm = re.sub(
                    r'^category:\s*["\']?\[\[Sources\]\]["\']?',
                    'category: "[[Readings]]"',
                    fm_raw,
                    count=1,
                    flags=re.MULTILINE,
                )
                if new_fm != fm_raw:
                    new_text = f"---\n{new_fm}\n---\n" + text[end + 4:]
                    path.write_text(new_text, encoding="utf-8")
                    category_fixes.append(rel_str_f)
                    category = "Readings"
                    fm_raw = new_fm
                    text = new_text

        if category:
            if rel_str_f.lower().startswith("inbox/"):
                # Any note in the inbox is in a valid temporary landing/review state
                pass
            else:
                expected = expected_folder_prefix(category, VAULT)
                prefixes = acceptable_folder_prefixes(category, VAULT)
                if category == "Sources":
                    if not rel_str_f.startswith("Notes/") or rel_str_f.startswith("Notes/Projects/"):
                        wrong_folder.append((rel_str_f, category, "Notes/"))
                elif category == "Projects":
                    if not rel_str_f.startswith("Notes/Projects/"):
                        wrong_folder.append((rel_str_f, category, "Notes/Projects/"))
                elif category == "Readings" and rel_str_f.startswith("Notes/"):
                    wrong_folder.append((rel_str_f, category, expected or prefixes[0]))
                elif category == "Scraps":
                    if not rel_str_f.lower().startswith("inbox/"):
                        wrong_folder.append((rel_str_f, category, "Inbox/"))
                elif prefixes and not any(rel_str_f.startswith(p.rstrip("/")) for p in prefixes):
                    wrong_folder.append((rel_str_f, category, expected or prefixes[0]))

        if category == "Sources" and rel_str_f.startswith("Notes/") and not rel_str_f.startswith("Notes/Projects/"):
            raw_section = re.search(r"^## Raw inputs\s*$", text, re.MULTILINE | re.IGNORECASE)
            if not raw_section:
                source_linkage_issues.append((rel_str_f, "missing ## Raw inputs section"))
            else:
                section_text = text[raw_section.end():]
                next_heading = re.search(r"^## ", section_text, re.MULTILINE)
                if next_heading:
                    section_text = section_text[:next_heading.start()]
                reading_links = re.findall(r"\[\[([^\]|#]+)", section_text)
                if not reading_links:
                    source_linkage_issues.append((rel_str_f, "no Reading wikilinks in ## Raw inputs"))

        for legacy_link in re.findall(r"\[\[(Logs/[^\]|#]+)", text):
            legacy_path_links[rel_str_f].add(legacy_link)
        
        if note_id:
            id_to_paths[note_id].append(rel_path)
        else:
            missing_ids.append(rel_path)
            
        is_contact = (category in ["People", "Organizations"]) or rel_str_f.lower().startswith("notes/contacts/")
        if not is_contact:
            if not daily_note or "[[" not in daily_note:
                missing_daily_notes.append(rel_path)
            
        # Parse wikilinks
        wikilinks = re.findall(r'<!--.*?-->|(?<!\\\\)\[\[([^\]]+)\]\]', text)
        for link in wikilinks:
            if not link: continue # Skip commented out links
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
                # Fallback: match by extracting 14-digit ID suffix from link target
                id_suffix_match = re.search(r"(\d{14})", file_target)
                if id_suffix_match:
                    target_id = id_suffix_match.group(1)
                    if target_id in id_to_rel_path_catalog:
                        resolved = id_to_rel_path_catalog[target_id]
                        
            if not resolved:
                ghost_links[rel_str_f].add(file_target)
            else:
                outgoing_links[rel_str_f].add(resolved)
                incoming_links[resolved].add(rel_str_f)

citation_issues = defaultdict(list)
url_cache = {}
readings_audit_dirs = readings_dirs(VAULT)

# External URL/citation auditing is disabled per user request. Only internal wikilinks are checked.
if False: # readings_audit_dirs:
    print("Auditing Citation & Reading URLs in Inputs/Readings/...")
    all_source_files = []
    for readings_dir in readings_audit_dirs:
        all_source_files.extend(sorted(readings_dir.glob("**/*.md")))
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
            
    # Load persistent cache
    cache_path = Path("~/.hermes/state/hygiene_url_cache.json").expanduser()
    persistent_cache = {}
    if cache_path.exists():
        try:
            persistent_cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  Warning: failed to load URL cache: {e}")

    now_iso = datetime.datetime.now().date().isoformat()
    urls_to_check = set()
    
    for url in unique_urls:
        if url in persistent_cache:
            entry = persistent_cache[url]
            checked_at_str = entry.get("checked_at")
            err = entry.get("err")
            
            try:
                checked_at = datetime.date.fromisoformat(checked_at_str)
                age_days = (datetime.date.today() - checked_at).days
            except (ValueError, TypeError):
                age_days = 9999
                
            # If the URL is fine, cache it for 30 days. If it had an error, recheck every 7 days.
            ttl_days = 30 if err is None else 7
            if age_days > ttl_days:
                urls_to_check.add(url)
            else:
                url_cache[url] = err
        else:
            urls_to_check.add(url)

    # Check URLs in parallel using ThreadPoolExecutor
    if unique_urls:
        if urls_to_check:
            print(f"  Verifying {len(urls_to_check)} unique URLs in parallel (skipped {len(unique_urls) - len(urls_to_check)} cached)...")
            from concurrent.futures import ThreadPoolExecutor
            
            def check_one(url):
                return url, verify_url(url)
                
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(check_one, url) for url in urls_to_check]
                for fut in futures:
                    try:
                        url, err = fut.result()
                        url_cache[url] = err
                        persistent_cache[url] = {
                            "err": err,
                            "checked_at": now_iso
                        }
                    except Exception:
                        pass
                        
            # Save cache
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(persistent_cache, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"  Warning: failed to save URL cache: {e}")
        else:
            print(f"  All {len(unique_urls)} URLs are cached and within TTL.")
                    
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

if wrong_folder:
    lines.append("\n## 🔴 Wrong folder")
    for p, cat, expected in sorted(wrong_folder):
        lines.append(f"  - {p}: category [[{cat}]] expected under {expected}")

if source_linkage_issues:
    lines.append("\n## ⚠️ Source linkage")
    for p, reason in sorted(source_linkage_issues):
        lines.append(f"  - {p}: {reason}")

if legacy_path_links:
    lines.append("\n## ⚠️ Legacy path links")
    for p in sorted(legacy_path_links.keys()):
        for target in sorted(legacy_path_links[p]):
            lines.append(f"  - {p} links to legacy path: [[{target}]]")

if citation_issues:
    lines.append("\n## ⚠️ Citation & Reading URL Issues")
    for p in sorted(citation_issues.keys()):
        for url, err in citation_issues[p]:
            lines.append(f"  - {p}: [{err}] {url}")

if category_fixes:
    print(f"Auto-fixed {len(category_fixes)} legacy [[Sources]] → [[Readings]] on input paths.")

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
