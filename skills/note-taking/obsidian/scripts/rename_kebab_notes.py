import os
import re
import argparse

def parse_and_convert(filename):
    base, ext = os.path.splitext(filename)
    if ext != '.md':
        return None
        
    # 1. Detect date prefix: YYYY-MM-DD
    date_prefix = ""
    rest = base
    m_date = re.match(r'^(\d{4}-\d{2}-\d{2})[-_\s]+(.*)$', base)
    if m_date:
        date_prefix = m_date.group(1)
        rest = m_date.group(2)
        
    # 2. Detect timestamp suffix: YYYYMMDDHHmmss
    timestamp_suffix = ""
    m_time_suffix = re.match(r'^(.*?)[-_\s]+(\d{14})$', rest)
    if m_time_suffix:
        rest = m_time_suffix.group(1)
        timestamp_suffix = m_time_suffix.group(2)
        
    # 3. Detect timestamp prefix: YYYYMMDDHHmmss
    timestamp_prefix = ""
    m_time_prefix = re.match(r'^(\d{14})[-_\s]+(.*)$', rest)
    if m_time_prefix:
        timestamp_prefix = m_time_prefix.group(1)
        rest = m_time_prefix.group(2)
        
    # Check if "rest" contains hyphens and no spaces
    if "-" not in rest or " " in rest:
        return None
        
    # Convert "rest" to normal case (hyphens -> spaces)
    normal_text = rest.replace("-", " ")
    # Capitalize the first letter
    if len(normal_text) > 0:
        normal_text = normal_text[0].upper() + normal_text[1:]
        
    ts = timestamp_suffix or timestamp_prefix
    
    new_base = normal_text
    if date_prefix:
        new_base = f"{date_prefix} {new_base}"
    if ts:
        new_base = f"{new_base} {ts}"
        
    return new_base + ext

def build_rename_maps(vault_path, excluded_dirs):
    rename_map = {}  # old_path -> new_path
    title_map = {}   # old_title_lower -> new_title
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith(".")]
        for f in files:
            new_name = parse_and_convert(f)
            if new_name:
                old_path = os.path.join(root, f)
                new_path = os.path.join(root, new_name)
                rename_map[old_path] = new_path
                
                old_title, _ = os.path.splitext(f)
                new_title, _ = os.path.splitext(new_name)
                title_map[old_title.lower()] = new_title
    return rename_map, title_map

def make_transform_fn(title_map):
    pattern = r'\[\[([^\]]+)\]\]'
    
    def replace_link(match):
        inner = match.group(1)
        if '|' in inner:
            target_part, display = inner.split('|', 1)
        else:
            target_part, display = inner, None
            
        if '#' in target_part:
            base_target, section = target_part.split('#', 1)
            section = '#' + section
        else:
            base_target, section = target_part, ""
            
        base_target_clean = base_target.strip()
        base_target_lower = base_target_clean.lower()
        
        # Extract base filename
        target_filename_lower = os.path.basename(base_target_lower)
        
        if target_filename_lower in title_map:
            new_target_title = title_map[target_filename_lower]
            dir_part = os.path.dirname(base_target_clean)
            new_base_target = os.path.join(dir_part, new_target_title) if dir_part else new_target_title
            
            # Reconstruct link
            if display:
                return f"[[{new_base_target}{section}|{display}]]"
            else:
                return f"[[{new_base_target}{section}]]"
        return match.group(0)
        
    return lambda content: re.sub(pattern, replace_link, content)

def run_migration(vault_path, commit=False):
    excluded_dirs = {".git", ".trash", ".obsidian", "utilities", "sources", "daily"}
    scan_link_dirs_exclude = {".git", ".trash", ".obsidian", "utilities", "sources"}
    
    rename_map, title_map = build_rename_maps(vault_path, excluded_dirs)
    print(f"Total files matched for renaming: {len(rename_map)}")
    
    transform_fn = make_transform_fn(title_map)
    
    # 1. Update Wikilinks in markdown files
    healed_files = 0
    total_healed = 0
    
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in scan_link_dirs_exclude and not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                        content = fh.read()
                except Exception as e:
                    print(f"Error reading {path}: {e}")
                    continue
                    
                new_content = transform_fn(content)
                if new_content != content:
                    healed_files += 1
                    # Count differences
                    old_links = re.findall(r'\[\[([^\]]+)\]\]', content)
                    new_links = re.findall(r'\[\[([^\]]+)\]\]', new_content)
                    diff_count = sum(1 for o, n in zip(old_links, new_links) if o != n)
                    total_healed += diff_count
                    
                    if commit:
                        try:
                            with open(path, 'w', encoding='utf-8') as fh:
                                fh.write(new_content)
                        except Exception as e:
                            print(f"Error writing {path}: {e}")
                            
    print(f"Wikilinks updated in {healed_files} files (total of {total_healed} links healed).")
    
    # 2. Rename files
    renamed_count = 0
    for old_path, new_path in rename_map.items():
        if commit:
            try:
                os.rename(old_path, new_path)
                renamed_count += 1
            except Exception as e:
                print(f"Error renaming {old_path} -> {new_path}: {e}")
        else:
            renamed_count += 1
            
    if commit:
        print(f"Successfully renamed {renamed_count} files on disk.")
    else:
        print(f"Dry-run: {renamed_count} files would be renamed on disk.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename kebab-case notes and heal wikilinks.")
    parser.add_argument("--vault", default="/home/justin.guest/Developer/obsidian-vault", help="Path to Obsidian vault")
    parser.add_argument("--commit", action="store_true", help="Perform actual rename and edits")
    args = parser.parse_args()
    
    run_migration(args.vault, commit=args.commit)
