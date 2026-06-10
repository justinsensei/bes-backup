#!/usr/bin/env python3
"""Append-only entity fan-out: update project and contact hub pages after ingest."""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from vault_entities import (
    VAULT_DEFAULT,
    build_ambiguous_keys,
    get_existing_entities,
    match_contacts,
    match_projects,
)

UNMATCHED_STATE_PATH = os.path.expanduser(
    "~/.hermes/state/integrate_entities_unmatched.json"
)

DECISION_CATEGORIES = {"Decisions", "decisions"}
STATE_KEYWORDS = re.compile(
    r"\b(decided|decision|resolved|resolution|approved|status|blocked|shipped|launched|"
    r"completed|cancelled|canceled|postponed|delayed|on hold|greenlit|go/no-go)\b",
    re.IGNORECASE,
)


def parse_frontmatter(content):
    fm = {}
    body = content
    fm_lists = {}
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end > 0:
            fm_raw = content[3:end]
            body = content[end + 4 :].lstrip("\n")
            current_list_key = None
            for line in fm_raw.split("\n"):
                if not line.strip():
                    continue
                list_item = re.match(r"^\s*-\s+(.+)$", line)
                if list_item and current_list_key:
                    fm_lists.setdefault(current_list_key, []).append(
                        list_item.group(1).strip().strip("\"'")
                    )
                    continue
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip("\"'")
                if val == "" or val == "|":
                    current_list_key = key
                    fm_lists.setdefault(key, [])
                else:
                    current_list_key = None
                    fm[key] = val
            for key, items in fm_lists.items():
                fm[key] = items
    return fm, body


def parse_frontmatter_list(fm, key):
    raw = fm.get(key, "")
    if not raw:
        return []
    if raw.startswith("["):
        return [x.strip().strip("\"'") for x in raw.strip("[]").split(",") if x.strip()]
    return [raw.strip().strip("\"'")]


def extract_date(fm, file_path, vault_path):
    dn = fm.get("daily_note", "")
    m = re.search(r"(\d{4}-\d{2}-\d{2})", dn)
    if m:
        return m.group(1)
    filename = os.path.basename(file_path)
    m = re.search(r"^(\d{4}-\d{2}-\d{2})", filename)
    if m:
        return m.group(1)
    rel = os.path.relpath(file_path, vault_path)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", rel)
    if m:
        return m.group(1)
    return datetime.now().strftime("%Y-%m-%d")


def parse_category(fm):
    raw = fm.get("category", "")
    m = re.search(r"\[\[([^\]]+)\]\]", raw)
    return m.group(1) if m else raw.strip("[]")


def shortest_wikilink(vault_path, ingest_path):
    rel = os.path.relpath(ingest_path, vault_path).replace("\\", "/")
    slug = rel[:-3] if rel.endswith(".md") else rel
    title = os.path.basename(ingest_path)[:-3]
    return slug, title


def extract_gist(body, fm, override=None):
    if override:
        return override.strip()
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.startswith("- **") or line.startswith("##"):
            continue
        if len(line) > 20:
            return line[:200]
    return os.path.basename(body)[:120] if body else "Ingest"


def is_decision_ingest(fm, body, ingest_path):
    cat = parse_category(fm)
    if cat in DECISION_CATEGORIES:
        return True
    if "Decision" in os.path.basename(ingest_path):
        return True
    if re.search(r"^#\s*.*Decision", body, re.MULTILINE):
        return True
    return False


def needs_state_update(fm, body, ingest_path):
    if is_decision_ingest(fm, body, ingest_path):
        return True
    cat = parse_category(fm)
    if cat == "Meetings" and STATE_KEYWORDS.search(body):
        return True
    return False


def extract_resolution_gist(body):
    m = re.search(
        r"##\s*[⚖️]*\s*Resolution\s*\n+(.*?)(?=\n##|\Z)",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        text = m.group(1).strip()
        first = text.split("\n")[0].strip("- ").strip()
        if first:
            return first[:200]
    for line in body.split("\n"):
        if STATE_KEYWORDS.search(line) and len(line.strip()) > 15:
            return line.strip("- ").strip()[:200]
    return extract_gist(body, {})


def section_exists_with_link(content, section_heading, wikilink_slug):
    pattern = rf"^{re.escape(section_heading)}\s*$"
    m = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    if not m:
        return False
    rest = content[m.end() :]
    next_h = re.search(r"^##\s", rest, re.MULTILINE)
    section_text = rest[: next_h.start()] if next_h else rest
    return f"[[{wikilink_slug}" in section_text or f"[[{wikilink_slug}|" in section_text


def append_to_section(content, section_heading, bullet_line):
    lines = content.splitlines(keepends=True)
    if content and not content.endswith("\n"):
        lines.append("\n")

    heading_idx = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == section_heading.lower():
            heading_idx = i
            break

    bullet = bullet_line if bullet_line.endswith("\n") else bullet_line + "\n"

    if heading_idx == -1:
        while lines and lines[-1].strip() == "":
            lines.pop()
        if lines and not lines[-1].endswith("\n\n"):
            if not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append("\n")
        lines.append(f"{section_heading}\n")
        lines.append(bullet)
        return "".join(lines)

    insert_idx = heading_idx + 1
    while insert_idx < len(lines) and lines[insert_idx].strip() == "":
        insert_idx += 1
    next_heading_idx = len(lines)
    for j in range(insert_idx, len(lines)):
        if lines[j].startswith("## ") and j > heading_idx:
            next_heading_idx = j
            break
    lines.insert(next_heading_idx, bullet)
    return "".join(lines)


def set_frontmatter_project(content, project_title):
    fm, body = parse_frontmatter(content)
    project_val = f'"[[{project_title}]]"'
    if fm.get("project") and project_title.lower() in fm.get("project", "").lower():
        return content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end > 0:
            fm_raw = content[3:end]
            if re.search(r"^project:", fm_raw, re.MULTILINE):
                new_fm = re.sub(
                    r"^project:.*$",
                    f"project: {project_val}",
                    fm_raw,
                    count=1,
                    flags=re.MULTILINE,
                )
            else:
                new_fm = fm_raw.rstrip() + f"\nproject: {project_val}\n"
            return f"---\n{new_fm}---\n" + body
    return content


def append_meeting_related(content, project_title):
    if f"[[{project_title}]]" in content:
        return content
    related_heading = "### Related"
    bullet = f"- [[{project_title}]]"
    if re.search(r"^### Related\s*$", content, re.MULTILINE):
        return append_to_section(content, related_heading, bullet)
    content = content.rstrip() + "\n\n"
    content += f"{related_heading}\n{bullet}\n"
    return content


def accumulate_unmatched(report, ingest_date, unmatched_path=None):
    state_path = unmatched_path or UNMATCHED_STATE_PATH
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    existing = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    day = existing.setdefault(ingest_date, {"project_candidates": [], "contact_candidates": []})
    for cand in report.get("unmatched", {}).get("project_candidates", []):
        if cand not in day["project_candidates"]:
            day["project_candidates"].append(cand)
    for cand in report.get("unmatched", {}).get("contact_candidates", []):
        if cand not in day["contact_candidates"]:
            day["contact_candidates"].append(cand)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def integrate_ingest(vault_path, ingest_rel_path, gist_override=None, unmatched_path=None):
    ingest_path = (
        ingest_rel_path
        if os.path.isabs(ingest_rel_path)
        else os.path.join(vault_path, ingest_rel_path)
    )
    if not os.path.exists(ingest_path):
        return {"error": f"File not found: {ingest_rel_path}"}

    with open(ingest_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    entities = get_existing_entities(vault_path)
    ambiguous = build_ambiguous_keys(entities)

    participants = fm.get("participants", [])
    if isinstance(participants, str):
        participants = parse_frontmatter_list({"participants": participants}, "participants")
    channel = fm.get("channel", "").strip().strip("\"'")
    explicit_project = fm.get("project", "").strip().strip("\"'")

    match_text = body + "\n" + os.path.basename(ingest_path)
    if fm.get("category"):
        match_text += "\n" + fm["category"]

    contacts, unmatched_contacts = match_contacts(participants, entities, ambiguous)
    projects, unmatched_projects = match_projects(
        match_text,
        entities,
        channel=channel or None,
        explicit_project=explicit_project or None,
        ambiguous_keys=ambiguous,
        channel_map_path=os.environ.get("CHANNEL_PROJECT_MAP_PATH"),
    )

    ingest_date = extract_date(fm, ingest_path, vault_path)
    slug, title = shortest_wikilink(vault_path, ingest_path)
    gist = extract_gist(body, fm, gist_override)
    timeline_bullet = f"- {ingest_date} | [[{slug}|{title}]] — {gist}"
    state_gist = extract_resolution_gist(body) if needs_state_update(fm, body, ingest_path) else gist
    state_bullet = f"- {ingest_date} | Decision — {state_gist} ([[{slug}|{title}]])"

    report = {
        "updated": {"projects": [], "contacts": []},
        "skipped": [],
        "unmatched": {
            "project_candidates": unmatched_projects,
            "contact_candidates": unmatched_contacts,
        },
    }

    update_state = needs_state_update(fm, body, ingest_path)

    for proj in projects:
        if not update_state:
            continue
        proj_path = proj["path"]
        with open(proj_path, encoding="utf-8", errors="replace") as f:
            proj_content = f.read()

        changed = False
        if not section_exists_with_link(proj_content, "## State", slug):
            proj_content = append_to_section(proj_content, "## State", state_bullet)
            changed = True

        if changed:
            with open(proj_path, "w", encoding="utf-8") as f:
                f.write(proj_content)
            report["updated"]["projects"].append(proj["title"])

    # Timeline updates on contacts are disabled in favor of native backlinks
    for contact in contacts:
        report["skipped"].append(f"{contact['title']}:Timeline")

    if len(projects) == 1 and not explicit_project:
        new_content = set_frontmatter_project(content, projects[0]["title"])
        if new_content != content:
            with open(ingest_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    accumulate_unmatched(report, ingest_date, unmatched_path=unmatched_path)
    return report


def main():
    parser = argparse.ArgumentParser(description="Integrate ingest into entity hub pages")
    parser.add_argument("ingest_rel_path", help="Vault-relative path to ingest note")
    parser.add_argument("--gist", default=None, help="One-line summary override")
    parser.add_argument(
        "--vault",
        default=os.environ.get("OBSIDIAN_VAULT_PATH", VAULT_DEFAULT),
        help="Vault root path",
    )
    args = parser.parse_args()

    report = integrate_ingest(args.vault, args.ingest_rel_path, args.gist)
    print(json.dumps(report, indent=2))
    if "error" in report:
        sys.exit(1)


if __name__ == "__main__":
    main()
