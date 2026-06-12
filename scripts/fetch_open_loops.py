#!/usr/bin/env python3
import subprocess
import json
import os
from datetime import datetime, timedelta

# Note: This script is now designed to be run via `execute_code`
# to have access to the hermes_tools library.

def get_todoist_loops():
    """Fetches incomplete Todoist tasks due today or overdue."""
    print("Checking Todoist for open loops...")
    try:
        from hermes_tools.mcp_todoist import find_tasks_by_date
        tasks_result = find_tasks_by_date(
            startDate='today',
            overdueOption='include-overdue',
            responsibleUserFiltering='unassignedOrMe'
        )
        tasks = tasks_result.get("structuredContent", {}).get("tasks", [])
        return [f"Todoist: {task['content']}" for task in tasks]
    except Exception as e:
        print(f"Error calling Todoist tool: {e}")
        return []

def get_calendar_loops():
    """Fetches calendar events in the next 3 days that might need prep."""
    print("Checking Google Calendar for open loops...")
    try:
        from hermes_tools import terminal
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        
        script_path = "/home/justin.guest/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py"
        command = f"python3 {script_path} --account all calendar list --start {start_date}T00:00:00 --end {end_date}T23:59:59 --max 10"
        
        result = terminal(command)
        output = result.get('output')
        if not output:
            return []
            
        events = json.loads(output)
        loops = []
        for event in events:
            if 'T' in event.get('start', '') and event.get('summary', '').lower() not in ["jamie music", "sam drums"]:
                 loops.append(f"Calendar: Prepare for '{event['summary']}'")
        return list(set(loops)) # Deduplicate
    except Exception as e:
        print(f"Error getting calendar events: {e}")
        return []

def get_vault_loops():
    """Fetches open loops from vault notes."""
    print("Checking Obsidian vault for open loops...")
    try:
        from hermes_tools import terminal
        vault_path = "/home/justin.guest/vault"
        loops = []
        
        find_command = f"find {vault_path}/Notes {vault_path}/inbox -type f -name '*.md' -mtime -3"
        find_result = terminal(find_command)
        recent_files_output = find_result.get('output')

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
    except Exception as e:
        print(f"Error searching vault: {e}")
        return []


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

# This part is for direct execution if needed, but the main entry is via execute_code
if __name__ == "__main__":
    # We can't call hermes_tools from here, so we would need a different path
    # For now, this just serves as a marker that the script is intended
    # to be called by a tool that provides the hermes_tools library.
    print("This script is intended to be run via execute_code.")
