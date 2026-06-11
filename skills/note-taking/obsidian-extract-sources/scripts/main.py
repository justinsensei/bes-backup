#!/usr/bin/env python3
import os
import sys
import random
import subprocess
import json
import re

# --- Constants ---
VAULT_PATH = "/home/justin.guest/vault"
SOURCES_DIR = os.path.join(VAULT_PATH, "Notes", "Sources")
READINGS_DIR = os.path.join(VAULT_PATH, "Inputs", "Readings")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def find_unprocessed_readings():
    """
    Finds all Reading notes that do not have a corresponding Source note linking to them.
    Returns a list of absolute paths to the unprocessed reading files.
    """
    all_readings = []
    for root, _, files in os.walk(READINGS_DIR):
        for file in files:
            if file.endswith(".md"):
                all_readings.append(os.path.join(root, file))

    if not os.path.exists(SOURCES_DIR):
        return all_readings

    # This is a simple but effective way to check for backlinks.
    # A more advanced solution might use a pre-built graph, but that's too complex here.
    source_content_cache = ""
    for root, _, files in os.walk(SOURCES_DIR):
        for file in files:
            if file.endswith(".md"):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    source_content_cache += f.read()

    unprocessed = []
    for reading_path in all_readings:
        # Generate the expected wikilink format
        reading_relpath = os.path.relpath(reading_path, VAULT_PATH)
        reading_wikilink_path = reading_relpath.replace(os.sep, '/')
        
        # Check if "[[wikilink/path.md]]" or "[[filename]]" is in any source note
        link_pattern1 = f"[[{reading_wikilink_path}]]"
        link_pattern2 = f"[[{os.path.basename(reading_path)}]]"
        
        if link_pattern1 not in source_content_cache and link_pattern2 not in source_content_cache:
            unprocessed.append(reading_path)

    return unprocessed

def select_reading_interactively(readings, batch_size=5):
    """
    Presents a random batch of readings to the user and asks for a selection.
    Handles requesting a new batch. Returns the path of the selected reading or None.
    """
    if not readings:
        print("No unprocessed readings found.")
        return None

    sample = random.sample(readings, min(len(readings), batch_size))
    
    # Present choices via clarify
    choices = [os.path.splitext(os.path.basename(r))[0] for r in sample]
    choices.append("Show another 5 random readings")
    choices.append("Exit")

    # This is a placeholder for the actual `clarify` tool call.
    # The script will print this JSON, and the agent will execute it.
    clarify_payload = {
        "tool": "clarify",
        "question": "Which reading would you like to process into a Source note?",
        "choices": choices,
        "__interactive_meta": {
            "type": "reading_selection",
            "mapping": {choice: path for choice, path in zip(choices, sample)}
        }
    }
    
    print(json.dumps(clarify_payload))
    return "__INTERACTIVE__"


def run_extraction(reading_path):
    """
    Calls the create_source_note.py script on the selected reading.
    """
    script_path = os.path.join(SCRIPTS_DIR, "create_source_note.py")
    try:
        # We run it and capture output to know the path of the new file.
        result = subprocess.run(
            [sys.executable, script_path, reading_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )
        new_note_path = result.stdout.strip()
        print(f"Successfully created new Source note at:\n{new_note_path}")
        return new_note_path
    except subprocess.CalledProcessError as e:
        print(f"Error during source note creation for '{reading_path}':", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        return None

def main_unseeded():
    """
    Main loop for the unseeded, interactive mode.
    """
    unprocessed_readings = find_unprocessed_readings()
    if not unprocessed_readings:
        print("Congratulations, all readings have been processed into Source notes!")
        return

    # This script doesn't loop itself. The agent will re-run it based on user choice.
    select_reading_interactively(unprocessed_readings)


if __name__ == "__main__":
    # For now, we only have the unseeded mode. We'll add arguments later.
    main_unseeded()
