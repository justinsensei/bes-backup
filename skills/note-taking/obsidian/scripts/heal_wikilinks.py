import os
import re
from pathlib import Path
from collections import defaultdict

def main():
    vault_path = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/justin.guest/Developer/obsidian-vault"))
    if not vault_path.exists():
        print(f"Vault path not found: {vault_path}")
        return

    # 1. Map all lowercase base filenames to their relative paths to identify collisions
    filename_map = defaultdict(list)
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Utilities"}
    
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if f.endswith(".md"):
                rel_path = (Path(root).relative_to(vault_path) / f).as_posix()
                base_name = Path(f).stem.lower()
                filename_map[base_name].append(rel_path)

    collisions = {name for name, paths in filename_map.items() if len(paths) > 1}
    print(f"Identified {len(collisions)} base-name collisions in vault. Paths will be preserved for these.")

    # 2. Compile wikilink regex
    wikilink_re = re.compile(r'\[\[([^\]]+)\]\]')
    files_updated = 0

    # 3. Heal files
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if not f.endswith(".md"):
                continue
            path = Path(root) / f
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                print(f"Error reading {path}: {e}")
                continue
                
            new_content = content
            
            def replace_link(match):
                inner = match.group(1)
                # Split display part
                if '|' in inner:
                    target, display = inner.split('|', 1)
                else:
                    target, display = inner, None
                    
                # Split heading/section part
                if '#' in target:
                    base_target, section = target.split('#', 1)
                    section = '#' + section
                else:
                    base_target, section = target, ""
                    
                # Check if there are slashes in base_target
                if '/' in base_target:
                    parts = base_target.split('/')
                    stem = parts[-1].strip()
                    stem_clean = stem.replace(".md", "")
                    stem_clean_lower = stem_clean.lower()
                    
                    if stem_clean_lower not in collisions:
                        # Simplify!
                        new_target = f"{stem_clean}{section}"
                        if display is not None:
                            return f"[[{new_target}|{display}]]"
                        else:
                            return f"[[{new_target}]]"
                
                return match.group(0)
                
            new_content = wikilink_re.sub(replace_link, content)
            if new_content != content:
                try:
                    path.write_text(new_content, encoding="utf-8")
                    files_updated += 1
                except Exception as e:
                    print(f"Error writing to {path}: {e}")

    print(f"Successfully healed links in {files_updated} files.")

if __name__ == "__main__":
    main()
