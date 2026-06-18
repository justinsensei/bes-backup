#!/usr/bin/env python3
"""Shared vault entity index and matching for contacts and projects."""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

VAULT_DEFAULT = "/home/justin.guest/Developer/obsidian-vault"
CHANNEL_MAP_PATH = os.path.expanduser("~/.hermes/state/channel-project-map.json")

STOP_WORDS = {
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "obsidian", "github", "posthog", "revenuecat", "customer", "linear", "google",
    "slack", "zoom", "teams", "signlab", "duolingo", "powerschool",
    "revenue", "product", "sprint", "engineering", "design", "marketing", "roadmap",
    "quarter", "weekly", "monthly", "meeting", "standup", "sync",
    "project", "note", "thought", "belief", "concept", "reference", "decision",
    "source", "sources", "agenda", "action", "items", "next", "steps",
    "yesterday", "tomorrow", "today", "classroom", "classrooms", "lessons", "lesson",
    "teacher", "teachers", "student", "students", "school", "schools", "education",
    "edtech", "app", "web", "mobile", "native", "stripe", "payments", "payment",
    "flow", "webinars", "webinar", "campaign", "campaigns", "advertising",
    "analytics", "replays", "replay", "session", "sessions", "cohort", "cohorts",
    "retention", "activation", "onboarding", "refactor",
    "personal", "work", "log", "logs", "briefing", "morning", "thoughts", "opinions",
    "gratitude", "thank", "thanks", "happy", "good", "great", "awesome", "amazing",
    "beautiful", "wonderful", "perfect", "excellent", "the", "and", "for", "with",
    "from", "this", "that", "about", "into", "over", "under", "after", "before",
}


def load_channel_map(path=None):
    map_path = path or os.environ.get("CHANNEL_PROJECT_MAP_PATH") or CHANNEL_MAP_PATH
    if not os.path.exists(map_path):
        return {}
    try:
        with open(map_path, encoding="utf-8") as f:
            data = json.load(f)
        return {str(k).lower(): v for k, v in data.items()}
    except Exception:
        return {}


def parse_contact_file(file_path, filename):
    ptype = "person"
    aliases = []
    title = filename[:-3]
    is_contact = False
    try:
        with open(file_path, encoding="utf-8", errors="replace") as file_obj:
            content = file_obj.read()
            m_cat = re.search(
                r'^category:\s*["\']?\[\[(People|Organizations)\]\]["\']?',
                content,
                re.MULTILINE,
            )
            m_type = re.search(r'^type:\s*[\'"]?([a-zA-Z0-9_-]+)[\'"]?', content, re.MULTILINE)
            if m_cat or m_type:
                is_contact = True
            if m_type:
                ptype = m_type.group(1).strip()
            elif m_cat:
                ptype = "person" if m_cat.group(1) == "People" else "organization"
            m_aliases = re.search(
                r'^aliases:\s*\n((?:\s*-\s*.*?\n)+)', content, re.MULTILINE
            )
            if m_aliases:
                aliases = [
                    a.strip()[1:].strip().strip("\"'")
                    for a in m_aliases.group(1).split("\n")
                    if a.strip().startswith("-")
                ]
    except Exception:
        pass
    return is_contact, ptype, title, aliases


def parse_project_file(file_path, filename):
    title = filename[:-3]
    aliases = []
    try:
        with open(file_path, encoding="utf-8", errors="replace") as file_obj:
            content = file_obj.read()
            m_aliases = re.search(
                r'^aliases:\s*\n((?:\s*-\s*.*?\n)+)', content, re.MULTILINE
            )
            if m_aliases:
                aliases = [
                    a.strip()[1:].strip().strip("\"'")
                    for a in m_aliases.group(1).split("\n")
                    if a.strip().startswith("-")
                ]
            clean_name = re.sub(r"\s*\d{4,14}$", "", title).lower().strip()
            if clean_name and clean_name != title.lower():
                aliases.append(clean_name)
    except Exception:
        pass
    return title, aliases


def get_existing_entities(vault_path):
    entities = {}

    contacts_dir = os.path.join(vault_path, "Notes", "Contacts")
    if os.path.exists(contacts_dir):
        for f in os.listdir(contacts_dir):
            if f.endswith(".md"):
                file_path = os.path.join(contacts_dir, f)
                _, ptype, title, aliases = parse_contact_file(file_path, f)
                name_key = f[:-3].lower()
                entities[name_key] = {
                    "path": file_path,
                    "type": ptype,
                    "title": title,
                    "aliases": aliases,
                }

    inbox_dir = os.path.join(vault_path, "inbox")
    if os.path.exists(inbox_dir):
        for f in os.listdir(inbox_dir):
            if f.endswith(".md"):
                file_path = os.path.join(inbox_dir, f)
                is_contact, ptype, title, aliases = parse_contact_file(file_path, f)
                if is_contact:
                    name_key = f[:-3].lower()
                    entities[name_key] = {
                        "path": file_path,
                        "type": ptype,
                        "title": title,
                        "aliases": aliases,
                    }

    projects_dir = os.path.join(vault_path, "Notes", "Projects")
    if os.path.exists(projects_dir):
        for f in os.listdir(projects_dir):
            if f.endswith(".md"):
                file_path = os.path.join(projects_dir, f)
                title, aliases = parse_project_file(file_path, f)
                name_key = f[:-3].lower()
                entities[name_key] = {
                    "path": file_path,
                    "type": "project",
                    "title": title,
                    "aliases": list(dict.fromkeys(aliases)),
                }

    return entities


def build_ambiguous_keys(entities):
    key_to_paths = defaultdict(list)
    for ent_info in entities.values():
        key_to_paths[ent_info["title"].lower()].append(ent_info["path"])
        for alias in ent_info.get("aliases", []):
            key_to_paths[alias.lower()].append(ent_info["path"])
    return {k for k, paths in key_to_paths.items() if len(set(paths)) > 1}


def _normalize_name(name):
    return re.sub(r"\s+", " ", name.strip()).lower()


def _extract_wikilink_titles(text):
    titles = []
    for link in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", text):
        target = link.split("#")[0].strip()
        if target and "/" not in target:
            titles.append(target)
    return titles


def _significant_tokens(text):
    tokens = set()
    for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9-]+", text.lower()):
        if len(word) >= 3 and word not in STOP_WORDS:
            tokens.add(word)
    return tokens


def match_contacts(names, entities, ambiguous_keys=None):
    if ambiguous_keys is None:
        ambiguous_keys = build_ambiguous_keys(entities)

    matched = {}
    unmatched = []
    seen_paths = set()

    for raw_name in names:
        if not raw_name or not str(raw_name).strip():
            continue
        name = str(raw_name).strip()
        key = _normalize_name(name)

        if key in ambiguous_keys:
            unmatched.append(name)
            continue

        hit = None
        for ent_key, ent_info in entities.items():
            if ent_info.get("type") == "project":
                continue
            if ent_info["title"].lower() == key:
                hit = ent_info
                break
            for alias in ent_info.get("aliases", []):
                if alias.lower() == key:
                    hit = ent_info
                    break
            if hit:
                break

        if hit and hit["path"] not in seen_paths:
            matched[hit["path"]] = hit
            seen_paths.add(hit["path"])
        elif not hit:
            unmatched.append(name)

    return list(matched.values()), unmatched


def _project_by_title(title, entities):
    key = _normalize_name(title)
    for ent_info in entities.values():
        if ent_info.get("type") != "project":
            continue
        if ent_info["title"].lower() == key:
            return ent_info
        for alias in ent_info.get("aliases", []):
            if alias.lower() == key:
                return ent_info
    return None


def match_projects(text, entities, channel=None, explicit_project=None, ambiguous_keys=None, channel_map_path=None):
    if ambiguous_keys is None:
        ambiguous_keys = build_ambiguous_keys(entities)

    matched = {}
    candidates = []

    if explicit_project:
        proj_title = explicit_project.strip().strip("[]")
        if "|" in proj_title:
            proj_title = proj_title.split("|")[0]
        hit = _project_by_title(proj_title, entities)
        if hit:
            matched[hit["path"]] = hit
            return list(matched.values()), candidates

    channel_map = load_channel_map(channel_map_path)
    if channel:
        ch_key = channel.lstrip("#").lower()
        mapped = channel_map.get(ch_key)
        if mapped:
            hit = _project_by_title(mapped, entities)
            if hit:
                matched[hit["path"]] = hit
                return list(matched.values()), candidates

    for link_title in _extract_wikilink_titles(text):
        hit = _project_by_title(link_title, entities)
        if hit:
            matched[hit["path"]] = hit

    text_tokens = _significant_tokens(text)
    scored = []
    for ent_info in entities.values():
        if ent_info.get("type") != "project":
            continue
        title = ent_info["title"]
        title_key = title.lower()
        if title_key in ambiguous_keys:
            continue

        names_to_check = [title] + ent_info.get("aliases", [])
        best_overlap = 0
        for pname in names_to_check:
            pname_tokens = _significant_tokens(pname)
            if not pname_tokens:
                continue
            overlap = len(text_tokens & pname_tokens)
            if len(pname_tokens) >= 2 and overlap >= 2:
                best_overlap = max(best_overlap, overlap)
            elif len(pname_tokens) == 1:
                token = next(iter(pname_tokens))
                if len(token) >= 5 and token in text_tokens:
                    best_overlap = max(best_overlap, 1)

        if best_overlap >= 2:
            scored.append((best_overlap, ent_info))
        elif best_overlap == 1 and len(title.split()) == 1 and len(title) >= 5:
            if re.search(rf"\b{re.escape(title)}\b", text, re.IGNORECASE):
                scored.append((1, ent_info))

    if scored:
        scored.sort(key=lambda x: (-x[0], x[1]["title"]))
        top_score = scored[0][0]
        top_hits = [e for s, e in scored if s == top_score]
        if len(top_hits) == 1:
            matched[top_hits[0]["path"]] = top_hits[0]
        else:
            for ent in top_hits:
                candidates.append(ent["title"])

    return list(matched.values()), candidates


def get_contact_entities(entities):
    return {k: v for k, v in entities.items() if v.get("type") != "project"}


def get_project_entities(entities):
    return {k: v for k, v in entities.items() if v.get("type") == "project"}
