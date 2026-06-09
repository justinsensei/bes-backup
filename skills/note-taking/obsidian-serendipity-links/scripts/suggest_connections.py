import os
import re
import json
import random
import sys
import argparse

def parse_frontmatter(content):
    # Quick regex parser for simple frontmatter
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

def get_thoughts_and_beliefs(vault_path):
    notes_dir = os.path.join(vault_path, 'Notes')
    notes = []
    if not os.path.exists(notes_dir):
        return notes
        
    for f in os.listdir(notes_dir):
        if f.endswith('.md'):
            path = os.path.join(notes_dir, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as file_obj:
                    content = file_obj.read()
                fm = parse_frontmatter(content)
                category = fm.get('category', '')
                if '[[Thoughts]]' in category or '[[Beliefs]]' in category:
                    title = f[:-3]
                    # Strip frontmatter for clean reading
                    body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL).strip()
                    notes.append({
                        "path": path,
                        "title": title,
                        "category": "Thoughts" if "Thoughts" in category else "Beliefs",
                        "body": body[:1200]  # First 1200 chars to avoid token flood
                    })
            except Exception as e:
                pass
    return notes

def main():
    parser = argparse.ArgumentParser(description="Sample thoughts and beliefs for serendipitous linking.")
    parser.add_argument('--seed', type=str, default=None, help="Optional seed topic keyword")
    parser.add_argument('--vault', type=str, default=None, help="Vault path")
    args = parser.parse_args()
    
    vault_path = args.vault or os.environ.get('OBSIDIAN_VAULT_PATH', '/home/justin.guest/vault')
    notes = get_thoughts_and_beliefs(vault_path)
    
    if not notes:
        print(json.dumps({"error": "No Thoughts or Beliefs found in vault/Notes/"}))
        sys.exit(1)
        
    sampled_notes = []
    if args.seed:
        seed_lower = args.seed.lower()
        # Find matches based on title, content, or path
        matches = [n for n in notes if seed_lower in n['title'].lower() or seed_lower in n['body'].lower()]
        non_matches = [n for n in notes if n not in matches]
        
        # Take up to 6 matches
        match_sample_size = min(len(matches), 6)
        sampled_matches = random.sample(matches, match_sample_size) if matches else []
        
        # Take remaining from non-matches to fill pool to 12
        remaining_needed = max(12 - len(sampled_matches), 6)
        non_match_sample_size = min(len(non_matches), remaining_needed)
        sampled_non_matches = random.sample(non_matches, non_match_sample_size) if non_matches else []
        
        sampled_notes = sampled_matches + sampled_non_matches
        random.shuffle(sampled_notes)
    else:
        sample_size = min(len(notes), 12)
        sampled_notes = random.sample(notes, sample_size)
        
    print(json.dumps({
        "notes": sampled_notes,
        "total_available": len(notes),
        "seed_used": args.seed
    }, indent=2))

if __name__ == '__main__':
    main()
