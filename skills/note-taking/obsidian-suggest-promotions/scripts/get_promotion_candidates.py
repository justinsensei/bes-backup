import os
import re
import sys
import json
import random
import argparse

def parse_frontmatter(content):
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match:
        return {}
    fm_text = fm_match.group(1)
    fm = {}
    for line in fm_text.split('\n'):
        if ':' in line:
            parts = line.split(':', 1)
            key = parts[0].strip()
            val = parts[1].strip().strip('"\'')
            fm[key] = val
    return fm

def find_backlinks(vault_path, target_title, max_backlinks=5):
    # Search for [[Target Title]] or [[Target Title|Alias]] across the vault
    escaped_title = re.escape(target_title)
    # Match [[Title]] or [[Title|something]]
    pattern = re.compile(r'\[\[' + escaped_title + r'(?:\|[^\]]+)?\]\]', re.IGNORECASE)
    
    backlinks = []
    
    # We walk the vault to search for links
    for root, dirs, files in os.walk(vault_path):
        # Ignore hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.git' and d != '.trash']
        for f in files:
            if f.endswith('.md'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as file_obj:
                        content = file_obj.read()
                    
                    matches = list(pattern.finditer(content))
                    if matches:
                        # Get a couple of context lines around the first match
                        first_match = matches[0]
                        start = max(0, first_match.start() - 150)
                        end = min(len(content), first_match.end() + 150)
                        snippet = content[start:end].strip()
                        # Clean up snippet boundaries
                        if start > 0: snippet = "..." + snippet
                        if end < len(content): snippet = snippet + "..."
                        
                        rel_path = os.path.relpath(path, vault_path)
                        backlinks.append({
                            "path": rel_path,
                            "title": f[:-3],
                            "snippet": snippet
                        })
                        if len(backlinks) >= max_backlinks:
                            break
                except Exception:
                    pass
        if len(backlinks) >= max_backlinks:
            break
            
    return backlinks

def get_candidates(vault_path, seed=None):
    notes_dir = os.path.join(vault_path, 'Notes')
    candidates = []
    if not os.path.exists(notes_dir):
        return candidates
        
    for f in os.listdir(notes_dir):
        if f.endswith('.md'):
            path = os.path.join(notes_dir, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as file_obj:
                    content = file_obj.read()
                fm = parse_frontmatter(content)
                category = fm.get('category', '')
                
                # We care about: Notes, Sources, and Thoughts
                cat_lower = category.lower()
                is_tier1 = '[[notes]]' in cat_lower or '[[sources]]' in cat_lower
                is_tier2 = '[[thoughts]]' in cat_lower
                
                if is_tier1 or is_tier2:
                    title = f[:-3]
                    body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL).strip()
                    
                    candidates.append({
                        "path": os.path.relpath(path, vault_path),
                        "title": title,
                        "category": "Notes/Sources" if is_tier1 else "Thoughts",
                        "body": body[:1200]  # First 1200 chars for analysis
                    })
            except Exception:
                pass
                
    # Filter by seed if provided
    if seed:
        seed_lower = seed.lower()
        candidates = [c for c in candidates if seed_lower in c['title'].lower() or seed_lower in c['body'].lower()]
        
    return candidates

def main():
    parser = argparse.ArgumentParser(description="Gather candidates for note promotion.")
    parser.add_argument('--seed', type=str, default=None, help="Optional seed topic keyword")
    parser.add_argument('--vault', type=str, default=None, help="Vault path")
    args = parser.parse_args()
    
    vault_path = args.vault or os.environ.get('OBSIDIAN_VAULT_PATH', '/home/justin.guest/vault')
    
    if not os.path.exists(vault_path):
        print(json.dumps({"error": f"Vault path {vault_path} does not exist"}))
        sys.exit(1)
        
    all_candidates = get_candidates(vault_path, args.seed)
    
    if not all_candidates:
        print(json.dumps({"candidates": [], "total_available": 0}))
        sys.exit(0)
        
    # Sample up to 15 candidates for evaluation pool
    sample_size = min(len(all_candidates), 15)
    sampled = random.sample(all_candidates, sample_size)
    
    # Enumerate backlinks for the sampled candidates to help with synthesis
    for item in sampled:
        item["backlinks"] = find_backlinks(vault_path, item["title"])
        
    print(json.dumps({
        "candidates": sampled,
        "total_available": len(all_candidates),
        "seed_used": args.seed
    }, indent=2))

if __name__ == '__main__':
    main()
