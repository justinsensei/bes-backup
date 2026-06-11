#!/usr/bin/env python3
import os
import sys
import random
import subprocess
import json
import re
from datetime import datetime

# --- Constants ---
VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/home/justin.guest/vault")
INBOX_DIR = os.path.join(VAULT_PATH, "inbox")
READINGS_DIR = os.path.join(VAULT_PATH, "Inputs", "Readings")
SOURCES_DIR = os.path.join(VAULT_PATH, "Notes", "Sources")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# --- State File ---
STATE_FILE = os.path.join(os.path.expanduser("~"), ".hermes", "state", "extract_sources_state.json")

def save_state(data):
    """Saves data to the state file."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(data, f)

def load_state():
    """Loads data from the state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def find_unprocessed_readings():
    """
    Finds Reading notes without a corresponding Source note by checking for a specific
    'reading: "[[...]]"' backlink in the frontmatter of notes in the inbox and sources folder.
    """
    processed_reading_basenames = set()
    source_dirs = [SOURCES_DIR, INBOX_DIR]
    link_regex = re.compile(r'reading:\s*"\[\[([^\]]+)\]\]"')

    for directory in source_dirs:
        if os.path.exists(directory):
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(".md"):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                match = link_regex.search(content)
                                if match:
                                    # Extract the basename from the linked path
                                    linked_path = match.group(1)
                                    processed_reading_basenames.add(os.path.basename(linked_path))
                        except Exception:
                            # Ignore files that can't be read
                            continue

    all_readings = []
    unprocessed_readings = []
    if os.path.exists(READINGS_DIR):
        for root, _, files in os.walk(READINGS_DIR):
            for file in files:
                if file.endswith(".md"):
                    if file not in processed_reading_basenames:
                        unprocessed_readings.append(os.path.join(root, file))
    
    return unprocessed_readings


def generate_and_preview(reading_path):
    """
    Calls the content generation script and prints the proposed content.
    """
    script_path = os.path.join(SCRIPTS_DIR, "generate_source_content.py")
    try:
        result = subprocess.run(
            [sys.executable, script_path, reading_path],
            capture_output=True, text=True, check=True, timeout=300
        )
        proposed_content = result.stdout
        
        state = {'proposed_content': proposed_content}
        save_state(state)
        
        print("--- PROPOSED NOTE ---")
        print(proposed_content)
        
        clarify_payload = {
            "tool": "clarify",
            "question": "Do you want to create this note in your inbox?",
            "choices": ["Yes, create it.", "No, cancel."],
            "__interactive_meta": {"type": "creation_confirmation"}
        }
        print(json.dumps(clarify_payload))

    except subprocess.CalledProcessError as e:
        print(f"Error generating source note content for '{os.path.basename(reading_path)}':", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)

def write_note_to_inbox():
    """
    Writes the content from the state file to a new note in the inbox.
    """
    state = load_state()
    content = state.get('proposed_content')
    if not content:
        print("Error: No proposed content found to write.", file=sys.stderr)
        return

    title_match = re.search(r'^#\s*(.*)', content, re.MULTILINE)
    id_match = re.search(r"id:\s*'(\d+)'", content)
    
    if not title_match or not id_match:
        print("Error: Could not extract title or ID from content. Saving with timestamp name.", file=sys.stderr)
        title = "Source Note"
        note_id = datetime.now().strftime('%Y%m%d%H%M%S')
    else:
        title = title_match.group(1).strip()
        note_id = id_match.group(1).strip()

    sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
    filename = f"{sanitized_title} {note_id}.md"
    filepath = os.path.join(INBOX_DIR, filename)

    try:
        os.makedirs(INBOX_DIR, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully created new Source note in the inbox:\n{filepath}")
    except Exception as e:
        print(f"Error writing note to inbox: {e}", file=sys.stderr)
    finally:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

def handle_selection(user_choice, choice_map):
    if user_choice == "Exit":
        print("Exiting.")
        return
    
    if user_choice == "Show another 5 random readings":
        main_unseeded()
        return

    reading_path = choice_map.get(user_choice)
    if reading_path:
        generate_and_preview(reading_path)
    else:
        print(f"Error: Invalid selection '{user_choice}'.", file=sys.stderr)

def main_unseeded():
    readings = find_unprocessed_readings()
    if not readings:
        print("Congratulations, all readings have been processed!")
        return
    
    sample = random.sample(readings, min(len(readings), 5))
    choices = [os.path.splitext(os.path.basename(r))[0] for r in sample]
    choice_map = {choice: path for choice, path in zip(choices, sample)}
    
    save_state({"choice_map": choice_map})

    clarify_choices = choices + ["Show another 5 random readings", "Exit"]
    clarify_payload = {
        "tool": "clarify",
        "question": "Which reading would you like to process into a Source note?",
        "choices": clarify_choices,
        "__interactive_meta": {"type": "reading_selection"}
    }
    print(json.dumps(clarify_payload))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        main_unseeded()
    elif sys.argv[1] == "--handle-selection":
        state = load_state()
        choice_map = state.get("choice_map", {})
        handle_selection(sys.argv[2], choice_map)
    elif sys.argv[1] == "--confirm-creation":
        write_note_to_inbox()
    else:
        print(f"Error: Unknown argument '{sys.argv[1]}'", file=sys.stderr)
