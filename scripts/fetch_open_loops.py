#!/usr/bin/env python3
import subprocess
import json
import os
from datetime import datetime, timedelta

def run_command(command):
    """Runs a command and returns its stdout."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def get_todoist_loops():
    """Fetches incomplete Todoist tasks due today or overdue."""
    print("Checking Todoist for open loops...")
    command = "hermes tool mcp_todoist_find_tasks_by_date --json --startDate today --overdueOption include-overdue --responsibleUserFiltering unassignedOrMe"
    output = run_command(command)
    if not output:
        return []
    
    try:
        data = json.loads(output)
        tasks = data.get("structuredContent", {}).get("tasks", [])
        return [f"Todoist: {task['content']}" for task in tasks]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing Todoist output: {e}")
        return []

def get_calendar_loops():
    """Fetches calendar events in the next 3 days that might need prep."""
    print("Checking Google Calendar for open loops...")
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
    script_path = "/home/justin.guest/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py"
    command = f"python3 {script_path} --account all calendar list --start {start_date}T00:00:00 --end {end_date}T23:59:59 --max 10"
    
    output = run_command(command)
    if not output:
        return []
        
    try:
        events = json.loads(output)
        loops = []
        for event in events:
            # Simple heuristic: if an event is not an all-day event and not a recurring family thing, it might need prep.
            if 'T' in event.get('start', '') and event.get('summary', '').lower() not in ["jamie music", "sam drums"]:
                 loops.append(f"Calendar: Prepare for '{event['summary']}'")
        return list(set(loops)) # Deduplicate
    except json.JSONDecodeError as e:
        print(f"Error parsing Calendar output: {e}")
        return []

def get_vault_loops():
    """Fetches open loops from vault notes."""
    print("Checking Obsidian vault for open loops...")
    vault_path = "/home/justin.guest/vault"
    loops = []
    
    # Find recent files to check
    find_command = f"find {vault_path}/Notes {vault_path}/inbox -type f -name '*.md' -mtime -3"
    recent_files_output = run_command(find_command)
    if not recent_files_output:
        return []
    
    recent_files = recent_files_output.splitlines()
    
    for f_path in recent_files:
        try:
            with open(f_path, 'r') as f:
                in_open_loops_section = False
                for line in f:
                    if line.strip().lower() == "## open loops":
                        in_open_loops_section = True
                        continue
                    if line.strip().startswith("##"):
                        in_open_loops_section = False
                        
                    if in_open_loops_section and line.strip().startswith('- '):
                        loops.append(f"Vault: {line.strip()[2:]} (from {os.path.basename(f_path)})")
                    
                    if "TODO" in line and not line.strip().startswith('#'):
                         loops.append(f"Vault: {line.strip()} (from {os.path.basename(f_path)})")

        except Exception as e:
            print(f"Error reading file {f_path}: {e}")
            
    return list(set(loops))


def main():
    """Fetches and prints open loops from various sources."""
    all_loops = []
    all_loops.extend(get_todoist_loops())
    all_loops.extend(get_calendar_loops())
    all_loops.extend(get_vault_loops())
    
    if not all_loops:
        print("\nNo open loops found.")
        return

    print("\nFound the following potential open loops:")
    for i, loop in enumerate(all_loops, 1):
        print(f"{i}. {loop}")

if __name__ == "__main__":
    main()
