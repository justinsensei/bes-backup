#!/usr/bin/env python3
import json
import re
import os
import sys

def normalize(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def clean_content(text):
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if "::" in stripped:
            # Skip Logseq block properties (e.g. collapsed:: true, heading:: 1)
            # but do not skip URLs
            match = re.match(r'^[a-zA-Z0-9_\-]+::', stripped)
            if match and "://" not in stripped:
                continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()

def resolve_block_refs(text, block_map):
    if not text:
        return ""
    
    def replacer(match):
        ref_id = match.group(1)
        ref_block = block_map.get(ref_id)
        if ref_block:
            ref_content = ref_block.get("content", "").strip()
            return clean_content(ref_content)
        return match.group(0)
        
    return re.sub(r'\(\(([a-f0-9\-]+)\)\)', replacer, text)

def format_block(block, block_map, level=0):
    raw_content = block.get("content", "")
    content = clean_content(raw_content)
    content = resolve_block_refs(content, block_map)
    
    properties = block.get("properties") or {}
    children = block.get("children", [])
    
    lines = []
    is_header = "heading" in properties or content.startswith("#")
    
    indent = "  " * level
    
    if content:
        if is_header:
            h_level = properties.get("heading")
            if h_level and not content.startswith("#"):
                prefix = "#" * h_level + " "
                formatted_content = prefix + content
            else:
                formatted_content = content
            lines.append(formatted_content)
        else:
            content_lines = content.split("\n")
            first_line = content_lines[0]
            lines.append(f"{indent}- {first_line}")
            for line in content_lines[1:]:
                lines.append(f"{indent}  {line}")
    elif children and level == 0:
        pass
    elif children:
        lines.append(f"{indent}- ")
        
    next_level = level
    if content and not is_header:
        next_level = level + 1
        
    for child in children:
        child_str = format_block(child, block_map, next_level)
        if child_str:
            lines.append(child_str)
            
    return "\n".join(lines)

def main():
    if len(sys.argv) < 3:
        print("Usage: migrate_logseq_json.py <path_to_json> <vault_root_path>")
        sys.exit(1)
        
    json_path = sys.argv[1]
    vault_root = sys.argv[2]
    
    with open(json_path) as f:
        data = json.load(f)
        
    blocks = data.get("blocks", [])
    
    # Build block map
    block_map = {}
    def index_blocks(block):
        b_id = block.get("id")
        if b_id:
            block_map[b_id] = block
        for child in block.get("children", []):
            index_blocks(child)
            
    for b in blocks:
        index_blocks(b)
        
    # Map of lowercase kebab-case existing files to actual paths
    existing_files_normalized = {}
    for root, dirs, files in os.walk(vault_root):
        if any(p in root for p in [".git", ".trash", "utilities", "archive"]):
            continue
        for file in files:
            if file.endswith(".md"):
                name_without_ext = os.path.splitext(file)[0]
                existing_files_normalized[normalize(name_without_ext)] = os.path.join(root, file)
                
    for b in blocks:
        name = b.get("page-name") or b.get("properties", {}).get("page-name")
        if not name or name in ['source', 'tags', 'reference', 'person', 'None']:
            continue
            
        formatted_markdown = format_block(b, block_map).strip()
        if not formatted_markdown:
            continue
            
        norm_name = normalize(name)
        
        # Route target directories
        if "saturday" in norm_name or "sunday" in norm_name or "monday" in norm_name or "tuesday" in norm_name or "wednesday" in norm_name or "thursday" in norm_name or "friday" in norm_name:
            if re.match(r'^\d{4}-\d{2}-\d{2}', norm_name):
                target_path = os.path.join(vault_root, f"daily/{norm_name}.md")
            else:
                target_path = os.path.join(vault_root, f"notes/{norm_name}.md")
        elif "weekly" in norm_name or "sync" in norm_name or "meeting" in norm_name or b.get("properties", {}).get("tags", []) == ["meeting"]:
            target_path = os.path.join(vault_root, f"Meetings/{norm_name}.md")
        elif name in ['Benchmarks', 'PostHog SQL']:
            target_path = os.path.join(vault_root, f"concepts/{norm_name}.md")
        elif name == 'Words to live by':
            target_path = os.path.join(vault_root, f"personal/{norm_name}.md")
        else:
            # Fallback to notes directory
            target_path = os.path.join(vault_root, f"notes/{norm_name}.md")
            
        # Check if matched in normalized map
        matched_path = existing_files_normalized.get(norm_name)
        if matched_path:
            target_path = matched_path
            
        if os.path.exists(target_path):
            # Safe skip or merge
            if "daily/" in target_path:
                with open(target_path, "r") as f_in:
                    content = f_in.read()
                
                notepad_header = "## 🗒 Notepad"
                logbook_header = "## 📓 Logbook"
                
                if notepad_header in content and logbook_header in content:
                    parts = content.split(logbook_header)
                    notepad_part = parts[0]
                    logbook_part = logbook_header + parts[1]
                    
                    subparts = notepad_part.split(notepad_header)
                    before_notepad = subparts[0] + notepad_header + "\n"
                    current_notepad_content = subparts[1].strip()
                    
                    if current_notepad_content in ["-", "- "]:
                        new_notepad_content = formatted_markdown + "\n\n"
                    else:
                        new_notepad_content = current_notepad_content + "\n" + formatted_markdown + "\n\n"
                        
                    new_content = before_notepad + new_notepad_content + logbook_part
                    with open(target_path, "w") as f_out:
                        f_out.write(new_content)
                    print(f"Merged Logseq notes into: {target_path}")
                else:
                    new_content = content.strip() + "\n\n## Legacy Logseq Notes\n" + formatted_markdown + "\n"
                    with open(target_path, "w") as f_out:
                        f_out.write(new_content)
                    print(f"Appended Logseq notes to: {target_path}")
            else:
                print(f"Skipped existing meeting/concept file to prevent loss: {target_path}")
        else:
            # Write new file
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            if "daily/" in target_path:
                date_str = name.split()[0]
                clean_date = date_str.replace("-", "")
                frontmatter = f"---\nid: {clean_date}120000\n---\n--\n#daily_note \n\n## 🗒 Notepad\n{formatted_markdown}\n\n## 📓 Logbook\n"
            elif "Meetings/" in target_path:
                date_str = name.split()[0] if re.match(r'^\d{4}-\d{2}-\d{2}', name) else "2026-02-23"
                frontmatter = f"---\nid: {date_str.replace('-', '')}100000\ndaily_note: \"[[daily/{date_str}-monday|{date_str} Monday]]\"\ncategory: \"[[Meetings]]\"\n---\n--\n#meeting \n\n{formatted_markdown}\n"
            elif "concepts/" in target_path:
                frontmatter = f"---\nid: 20260225120000\ndaily_note: \"[[daily/2026-02-25-wednesday|2026-02-25 Wednesday]]\"\ncategory: \"[[Concepts]]\"\n---\n--\n{formatted_markdown}\n"
            elif "personal/" in target_path:
                frontmatter = f"---\nid: 20260222120000\ndaily_note: \"[[daily/2026-02-22-sunday|2026-02-22 Sunday]]\"\n---\n--\n{formatted_markdown}\n"
            else:
                frontmatter = f"---\nid: 20260221120000\n---\n--\n{formatted_markdown}\n"
                
            with open(target_path, "w") as f_out:
                f_out.write(frontmatter)
            print(f"Created new file: {target_path}")

if __name__ == "__main__":
    main()
