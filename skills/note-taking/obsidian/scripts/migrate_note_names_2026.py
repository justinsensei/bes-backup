import os
import re
import sys

def run_migration(vault_path, commit=False):
    id_pattern = re.compile(r"\d{14}")
    
    rename_map = {}  # old_path -> new_path
    title_map = {}   # old_title_lower -> new_title
    
    print(f"Scanning vault: {vault_path}")
    
    for root, dirs, files in os.walk(vault_path):
        if ".git" in root or ".trash" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            base, ext = os.path.splitext(f)
            
            match_id = id_pattern.search(base)
            if not match_id:
                continue
                
            note_id = match_id.group(0)
            
            # Read frontmatter for category
            category = "None"
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    head = fh.read(1000)
                    m_cat = re.search(r'category:\s*["\']?\[\[([^\]]+)\]\]["\']?', head, re.MULTILINE)
                    if m_cat:
                        category = m_cat.group(1).strip()
            except Exception as e:
                print(f"Warning: Could not read {f} to check category: {e}")
                
            # Rule 1: References - no ID strings in filename
            if category == "References":
                new_base = base.replace(note_id, "").strip()
                new_base = re.sub(r"^[-_\s]+", "", new_base)
                new_base = re.sub(r"[-_\s]+$", "", new_base)
                new_base = re.sub(r"\s+", " ", new_base)
                if not new_base:
                    new_base = base
            else:
                # Rule 2: ID strings at the end of the filename
                m_start = re.match(r"^(\d{14})[-_\s]+(.*)$", base)
                if m_start:
                    rest = m_start.group(2).strip()
                    new_base = f"{rest} {note_id}"
                else:
                    if base == note_id:
                        new_base = base
                    elif not base.endswith(note_id):
                        rest = base.replace(note_id, "").strip()
                        rest = re.sub(r"^[-_\s]+", "", rest)
                        rest = re.sub(r"[-_\s]+$", "", rest)
                        rest = re.sub(r"\s+", " ", rest)
                        new_base = f"{rest} {note_id}"
                    else:
                        new_base = base
            
            if new_base != base:
                new_path = os.path.join(root, new_base + ext)
                rename_map[path] = new_path
                title_map[base.lower()] = new_base

    # Check for collisions
    print(f"\nChecking for filename collisions...")
    new_paths_seen = {}
    collisions = []
    for old_path, new_path in rename_map.items():
        new_path_lower = new_path.lower()
        if new_path_lower in new_paths_seen:
            collisions.append((old_path, new_paths_seen[new_path_lower], new_path))
        else:
            new_paths_seen[new_path_lower] = old_path
            
        if os.path.exists(new_path) and new_path != old_path and new_path not in rename_map:
            collisions.append((old_path, new_path, new_path))

    if collisions:
        print(f"CRITICAL: Found {len(collisions)} naming collisions! Aborting.")
        for col in collisions[:5]:
            print(f"  Collision: {col[0]} AND {col[1]} both map to {col[2]}")
        sys.exit(1)
    else:
        print("No naming collisions found. Proceeding.")

    print(f"\nTotal files to rename: {len(rename_map)}")
    
    # Step 2: Healing Wikilinks in all Markdown files
    link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
    
    def heal_content(content):
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
            
            if target_filename_lower in title_map:
                new_target_title = title_map[target_filename_lower]
                dir_part = os.path.dirname(base_target_clean)
                new_base_target = os.path.join(dir_part, new_target_title) if dir_part else new_target_title
                
                if display:
                    return f"[[{new_base_target}{section}|{display}]]"
                else:
                    return f"[[{new_base_target}{section}]]"
            return match.group(0)
            
        return link_pattern.sub(replace_link, content)

    print("\nScanning and healing wikilinks...")
    healed_files_count = 0
    healed_links_count = 0
    
    for root, dirs, files in os.walk(vault_path):
        if ".git" in root or ".trash" in root:
            continue
        for f in files:
            if f.endswith(".md"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                        
                    new_content = heal_content(content)
                    if new_content != content:
                        healed_files_count += 1
                        old_links = link_pattern.findall(content)
                        new_links = link_pattern.findall(new_content)
                        diffs = sum(1 for o, n in zip(old_links, new_links) if o != n)
                        healed_links_count += diffs
                        
                        if commit:
                            with open(path, "w", encoding="utf-8") as fh:
                                fh.write(new_content)
                except Exception as e:
                    print(f"Error healing links in file {f}: {e}")

    print(f"Wikilinks healing completed. Files modified: {healed_files_count}, Total links healed: {healed_links_count}")

    if commit:
        print("\nRenaming files on disk...")
        renamed_count = 0
        for old_path, new_path in rename_map.items():
            try:
                os.rename(old_path, new_path)
                renamed_count += 1
            except Exception as e:
                print(f"Error renaming {old_path} -> {new_path}: {e}")
        print(f"DISK RENAME COMPLETE: {renamed_count} files renamed.")
    else:
        print("\nDRY RUN complete. No files were renamed or modified on disk.")
        print("To apply changes, run with '--commit'.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate vault note naming conventions.")
    parser.add_argument("--vault", default="/home/justin.guest/Developer/obsidian-vault", help="Path to the Obsidian vault")
    parser.add_argument("--commit", action="store_true", help="Commit the changes to disk")
    args = parser.parse_args()
    
    run_migration(args.vault, commit=args.commit)
