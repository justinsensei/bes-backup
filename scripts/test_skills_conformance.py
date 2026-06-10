#!/usr/bin/env python3
"""
Automated Skill Validation & Conformance Testing
This script scans Bes's custom skills under ~/.hermes/skills/ (and nested directories)
to enforce conformance with specified standards.
"""

import os
import sys
import re
import json
import yaml
import argparse
from datetime import datetime

# Path Configuration
USER_HOME = os.path.expanduser("~")
SKILLS_DIR = os.path.join(USER_HOME, ".hermes/skills")
VAULT_DIR = os.path.join(USER_HOME, "vault")
REPORT_PATH = os.path.join(USER_HOME, ".hermes/skills_validation_report.json")

def get_all_skill_dirs():
    """Scan ~/.hermes/skills/ and return all skill directories (depth 2 subdirectories)."""
    skill_dirs = []
    
    if not os.path.exists(SKILLS_DIR):
        return skill_dirs
        
    for category in os.listdir(SKILLS_DIR):
        if category.startswith('.'):
            continue
        category_path = os.path.join(SKILLS_DIR, category)
        if not os.path.isdir(category_path):
            continue
            
        for skill_name in os.listdir(category_path):
            if skill_name.startswith('.'):
                continue
            skill_path = os.path.join(category_path, skill_name)
            if not os.path.isdir(skill_path):
                continue
                
            skill_dirs.append({
                'category': category,
                'name': skill_name,
                'path': skill_path
            })
            
    # Sort for predictable output
    skill_dirs.sort(key=lambda x: (x['category'], x['name']))
    return skill_dirs

def get_vault_index():
    """Index vault files for fast, robust wikilink validation."""
    vault_files = set()
    vault_basenames = set()
    
    if os.path.exists(VAULT_DIR):
        for root, dirs, files in os.walk(VAULT_DIR):
            # Ignore hidden directories like .obsidian, .git
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.startswith('.'):
                    continue
                rel_path = os.path.relpath(os.path.join(root, f), VAULT_DIR)
                vault_files.add(rel_path.lower())
                vault_basenames.add(f.lower())
                
                # Also index without extension
                base, ext = os.path.splitext(f)
                vault_basenames.add(base.lower())
                
    return vault_files, vault_basenames

def strip_code(text):
    """Strip code blocks and inline code from markdown text to avoid false positives in link / tag parsing."""
    lines = text.splitlines()
    clean_lines = []
    in_code_block = False
    code_block_fence = None
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```') or stripped.startswith('````'):
            fence = '````' if stripped.startswith('````') else '```'
            if not in_code_block:
                in_code_block = True
                code_block_fence = fence
            else:
                if fence == code_block_fence:
                    in_code_block = False
                    code_block_fence = None
            continue
            
        if in_code_block:
            continue
        else:
            clean_lines.append(line)
            
    clean_text = "\n".join(clean_lines)
    # Strip inline code backticks
    clean_text = re.sub(r'`+[^`\n]+`+', '', clean_text)
    return clean_text

def validate_html_tags(text):
    """Verify there are no unclosed/mismatched HTML tags from a whitelist of expected tags."""
    # Matches <tag ...> or </tag>
    tag_pattern = re.compile(r'<(/?[a-zA-Z][a-zA-Z0-9]*)\b[^>]*>')
    
    # Whitelist of standard HTML tags to check
    html_whitelist = {
        'div', 'span', 'p', 'a', 'details', 'summary', 'br', 'hr', 'img', 
        'b', 'i', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 
        'table', 'tr', 'td', 'th', 'thead', 'tbody', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    }
    
    # Self-closing tags
    self_closing_tags = {'br', 'hr', 'img', 'input', 'link', 'meta'}
    
    stack = []
    errors = []
    
    for match in tag_pattern.finditer(text):
        full_match = match.group(0)
        tag_name = match.group(1).lower()
        
        is_closing = tag_name.startswith('/')
        actual_tag = tag_name[1:] if is_closing else tag_name
        
        if actual_tag not in html_whitelist:
            # Skip placeholders and other non-HTML patterns
            continue
            
        # Check if self-closing
        if full_match.endswith('/>') or actual_tag in self_closing_tags:
            if is_closing:
                errors.append(f"Self-closing tag '{actual_tag}' should not have a closing tag: {full_match}")
            continue
            
        if is_closing:
            if not stack:
                errors.append(f"Mismatched closing tag: {full_match} without an opening tag")
            else:
                last_open = stack.pop()
                if last_open != actual_tag:
                    errors.append(f"Mismatched closing tag: expected '</{last_open}>', but found '{full_match}'")
        else:
            stack.append(actual_tag)
            
    # Check for unclosed tags at the end
    if stack:
        for open_tag in stack:
            errors.append(f"Unclosed HTML tag: '<{open_tag}>'")
            
    return errors

def check_markdown_integrity(skill_dir, markdown_body, vault_files, vault_basenames, known_skill_names, known_skill_dir_names):
    """Validate links, unclosed code blocks, and HTML tags in the markdown body."""
    errors = []
    warnings = []
    
    # 1. Code Block Closure Verification
    lines = markdown_body.splitlines()
    in_code_block = False
    code_block_fence = None
    open_line_num = 0
    
    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('```') or stripped.startswith('````'):
            fence = '````' if stripped.startswith('````') else '```'
            if not in_code_block:
                in_code_block = True
                code_block_fence = fence
                open_line_num = line_idx + 1
            else:
                if fence == code_block_fence:
                    in_code_block = False
                    code_block_fence = None
                    
    if in_code_block:
        errors.append(f"Unclosed code block starting with {code_block_fence} at line {open_line_num}")
        
    # Strip code before examining links and HTML
    clean_text = strip_code(markdown_body)
    
    # 2. HTML Tag Integrity
    html_errors = validate_html_tags(clean_text)
    errors.extend(html_errors)
    
    # 3. Standard Markdown Links Verification
    standard_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', clean_text)
    for text, dest in standard_links:
        dest = dest.strip().strip('<>')
        if dest.startswith(('http://', 'https://', 'mailto:', 'tel:')) or dest.startswith('#'):
            continue
            
        dest_clean = dest.split('#')[0].split('?')[0]
        if not dest_clean:
            continue
            
        ref_path = os.path.abspath(os.path.join(skill_dir, dest_clean))
        if not os.path.exists(ref_path):
            errors.append(f"Invalid standard link: '{dest_clean}' referenced in '[{text}]({dest})' does not exist.")
            
    # 4. Wikilinks Verification
    wikilinks = re.findall(r'\[\[([^\]]+)\]\]', clean_text)
    for wl in wikilinks:
        dest = wl.split('|')[0].strip()
        dest_clean = dest.split('#')[0].strip()
        if not dest_clean:
            continue
            
        dest_lower = dest_clean.lower()
        
        # Check targets
        # A) Relative file
        rel_path = os.path.abspath(os.path.join(skill_dir, dest_clean))
        rel_path_md = rel_path + ".md"
        if os.path.exists(rel_path) or os.path.exists(rel_path_md):
            continue
            
        # B) Other Skill Name
        if dest_lower in known_skill_names or dest_lower in known_skill_dir_names:
            continue
            
        # C) Vault Note
        if dest_lower in vault_files or (dest_lower + ".md") in vault_files:
            continue
        if dest_lower in vault_basenames:
            continue
            
        errors.append(f"Invalid wikilink: '{dest_clean}' could not be resolved to any file, skill, or vault note.")
        
    return errors, warnings

def validate_skill(skill_dir_info, vault_files, vault_basenames, known_skill_names, known_skill_dir_names):
    """Validate a single skill directory and its SKILL.md file."""
    skill_dir = skill_dir_info['path']
    skill_name_dir = skill_dir_info['name']
    category = skill_dir_info['category']
    
    errors = []
    warnings = []
    metadata_info = {}
    
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    
    # Requirement 1: Enforce that each skill directory contains a SKILL.md file
    if not os.path.exists(skill_md_path):
        errors.append(f"Missing required SKILL.md file in directory: {category}/{skill_name_dir}")
        return {
            'name': skill_name_dir,
            'category': category,
            'path': skill_dir,
            'status': 'FAIL',
            'errors': errors,
            'warnings': warnings,
            'metadata': metadata_info
        }
        
    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Requirement 2: Parse YAML frontmatter of SKILL.md
        if not content.startswith('---'):
            errors.append("SKILL.md must start with a '---' YAML frontmatter block at line 1.")
            return {
                'name': skill_name_dir,
                'category': category,
                'path': skill_dir,
                'status': 'FAIL',
                'errors': errors,
                'warnings': warnings,
                'metadata': metadata_info
            }
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            errors.append("YAML frontmatter block is not closed (missing closing '---').")
            return {
                'name': skill_name_dir,
                'category': category,
                'path': skill_dir,
                'status': 'FAIL',
                'errors': errors,
                'warnings': warnings,
                'metadata': metadata_info
            }
            
        frontmatter_str = parts[1]
        markdown_body = parts[2]
        
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except Exception as e:
            errors.append(f"YAML frontmatter parsing failed: {str(e)}")
            return {
                'name': skill_name_dir,
                'category': category,
                'path': skill_dir,
                'status': 'FAIL',
                'errors': errors,
                'warnings': warnings,
                'metadata': metadata_info
            }
            
        if not isinstance(frontmatter, dict):
            errors.append("YAML frontmatter must be a dictionary/mapping.")
            return {
                'name': skill_name_dir,
                'category': category,
                'path': skill_dir,
                'status': 'FAIL',
                'errors': errors,
                'warnings': warnings,
                'metadata': metadata_info
            }
            
        # Save parsed frontmatter metadata
        metadata_info = frontmatter
        
        # Enforce required frontmatter fields: name, description, platforms, related_skills
        # name field
        if 'name' not in frontmatter:
            errors.append("Missing required frontmatter field: 'name'")
        elif not isinstance(frontmatter['name'], str):
            errors.append("Frontmatter field 'name' must be a string")
        elif len(frontmatter['name']) > 64:
            errors.append("Frontmatter field 'name' exceeds max length of 64 characters")
        elif not re.match(r'^[a-z0-9-]+$', frontmatter['name']):
            errors.append("Frontmatter field 'name' must be lowercase, alphanumeric and hyphens only")
            
        # description field
        if 'description' not in frontmatter:
            errors.append("Missing required frontmatter field: 'description'")
        elif not isinstance(frontmatter['description'], str):
            errors.append("Frontmatter field 'description' must be a string")
        elif len(frontmatter['description']) > 1024:
            errors.append("Frontmatter field 'description' exceeds max length of 1024 characters")
            
        # platforms field
        if 'platforms' not in frontmatter:
            errors.append("Missing required frontmatter field: 'platforms' (must be a list)")
        elif not isinstance(frontmatter['platforms'], list):
            errors.append("Frontmatter field 'platforms' must be a list")
            
        # related_skills field (can be at top level, or under metadata.hermes.related_skills)
        related_skills_val = None
        if 'related_skills' in frontmatter:
            related_skills_val = frontmatter['related_skills']
        elif 'metadata' in frontmatter and isinstance(frontmatter['metadata'], dict):
            hermes_meta = frontmatter['metadata'].get('hermes')
            if isinstance(hermes_meta, dict):
                related_skills_val = hermes_meta.get('related_skills')
                
        if related_skills_val is None:
            errors.append("Missing required frontmatter field: 'related_skills' (must be a list, top-level or under metadata.hermes.related_skills)")
        elif not isinstance(related_skills_val, list):
            errors.append("Frontmatter field 'related_skills' must be a list")
            
        # Requirement 3: Validate markdown headings/sections
        headings = []
        for line_idx, line in enumerate(markdown_body.splitlines()):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                headings.append({
                    'level': len(match.group(1)),
                    'text': match.group(2).strip(),
                    'line': line_idx + 1
                })
                
        if not headings:
            errors.append("SKILL.md does not contain any markdown headings.")
        else:
            # Must start with a level 1 heading
            if headings[0]['level'] != 1:
                errors.append(f"SKILL.md must start with a level 1 heading (e.g., '# Title'). Found level {headings[0]['level']}: '{headings[0]['text']}'")
                
            level_1s = [h for h in headings if h['level'] == 1]
            if len(level_1s) > 1:
                warnings.append(f"Multiple level 1 headings found: {[h['text'] for h in level_1s]}. Recommend only one main title.")
                
            # Check for key sections
            heading_texts = [h['text'].lower() for h in headings]
            
            if not any('overview' in t for t in heading_texts):
                warnings.append("Missing recommended section: 'Overview'")
            if not any('when to use' in t or 'triggers' in t for t in heading_texts):
                warnings.append("Missing recommended section: 'When to Use' or 'Triggers'")
            if not any('pitfall' in t for t in heading_texts):
                warnings.append("Missing recommended section: 'Common Pitfalls'")
            if not any('checklist' in t or 'verification' in t for t in heading_texts):
                warnings.append("Missing recommended section: 'Verification Checklist'")
                
        # Requirement 4: Check for markdown syntax integrity
        integ_errors, integ_warnings = check_markdown_integrity(
            skill_dir, markdown_body, vault_files, vault_basenames, 
            known_skill_names, known_skill_dir_names
        )
        errors.extend(integ_errors)
        warnings.extend(integ_warnings)
        
    except Exception as e:
        errors.append(f"Unhandled error during validation: {str(e)}")
        
    status = 'FAIL' if errors else ('WARN' if warnings else 'PASS')
    return {
        'name': frontmatter.get('name', skill_name_dir) if 'frontmatter' in locals() and isinstance(frontmatter, dict) else skill_name_dir,
        'category': category,
        'path': skill_dir,
        'status': status,
        'errors': errors,
        'warnings': warnings,
        'metadata': metadata_info
    }

def main():
    parser = argparse.ArgumentParser(description="Verify skill conformance and integrity across Bes's custom skills.")
    parser.parser_name = "test_skills_conformance.py"
    parser.add_argument("--strict", action="store_true", help="Fail if there are any warnings, not just errors.")
    parser.add_argument("--skill", help="Check a specific skill directory name (e.g., 'obsidian').")
    args = parser.parse_args()
    
    print("=" * 80)
    print("🛡️  AUTOMATED SKILL VALIDATION & CONFORMANCE TESTING")
    print("=" * 80)
    
    # 1. Discover skill directories
    skill_dirs = get_all_skill_dirs()
    if not skill_dirs:
        print("❌ No skills found under ~/.hermes/skills/")
        sys.exit(1)
        
    # 2. Build index of all skills and vault notes
    print(f"🔍 Indexing {len(skill_dirs)} skill directories...")
    
    # Pre-build known skill names and directory names
    known_skill_names = set()
    known_skill_dir_names = set()
    for s_dir in skill_dirs:
        known_skill_dir_names.add(s_dir['name'].lower())
        skill_md_path = os.path.join(s_dir['path'], "SKILL.md")
        if os.path.exists(skill_md_path):
            try:
                with open(skill_md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        fm = yaml.safe_load(parts[1])
                        if isinstance(fm, dict) and 'name' in fm:
                            known_skill_names.add(str(fm['name']).lower())
            except Exception:
                pass
                
    # Build vault index for shortest-path wikilink resolution
    print("📁 Indexing Obsidian vault for link validation...")
    vault_files, vault_basenames = get_vault_index()
    print(f"   Indexed {len(vault_files)} vault files.")
    
    # Filter by specific skill if requested
    if args.skill:
        skill_dirs = [s for s in skill_dirs if s['name'] == args.skill or s['category'] == args.skill]
        if not skill_dirs:
            print(f"❌ No skill matched name or category: '{args.skill}'")
            sys.exit(1)
            
    # 3. Validate each skill
    print("\n🚀 Commencing Skill Validation:\n")
    
    results = []
    total_passed = 0
    total_failed = 0
    total_warnings = 0
    
    for s_dir in skill_dirs:
        res = validate_skill(s_dir, vault_files, vault_basenames, known_skill_names, known_skill_dir_names)
        results.append(res)
        
        status = res['status']
        if status == 'PASS':
            total_passed += 1
            status_str = "🟢 PASS"
        elif status == 'WARN':
            total_warnings += 1
            status_str = "🟡 WARN"
        else:
            total_failed += 1
            status_str = "🔴 FAIL"
            
        print(f"[{status_str}]  {res['category']}/{res['name']}")
        
        if res['errors']:
            for err in res['errors']:
                print(f"  ❌ Error: {err}")
        if res['warnings']:
            for warn in res['warnings']:
                print(f"  ⚠️  Warning: {warn}")
        if res['errors'] or res['warnings']:
            print()
            
    print("-" * 80)
    print("📊 VALIDATION SUMMARY")
    print("-" * 80)
    print(f"✅ Total Passed:   {total_passed}")
    print(f"⚠️  Total Warnings: {total_warnings}")
    print(f"❌ Total Failed:   {total_failed}")
    print(f"📚 Total Checked:  {len(results)}")
    print("-" * 80)
    
    # 4. Write structured JSON validation report
    report_data = {
        'summary': {
            'total_skills_found': len(skill_dirs),
            'total_passed': total_passed,
            'total_warnings': total_warnings,
            'total_failed': total_failed,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'strict_mode': args.strict
        },
        'skills': results
    }
    
    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        print(f"💾 Structured JSON report written to: {REPORT_PATH}")
    except Exception as e:
        print(f"❌ Failed to write JSON report: {str(e)}")
        
    print("=" * 80)
    
    # Set exit code based on failure or strict warnings
    if total_failed > 0:
        sys.exit(1)
    if args.strict and total_warnings > 0:
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
