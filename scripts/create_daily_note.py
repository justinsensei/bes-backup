#!/usr/bin/env python
import os
from datetime import datetime

def create_daily_note():
    vault_path = os.path.expanduser("~/vault")
    template_path = os.path.join(vault_path, "Utilities/Templates/Daily Note Template.md")
    notes_dir = os.path.join(vault_path, "Daily Notes")
    
    os.makedirs(notes_dir, exist_ok=True)

    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekday_str = today.strftime("%A")
    filename = f"{date_str} {weekday_str}.md"
    file_path = os.path.join(notes_dir, filename)

    if os.path.exists(file_path):
        print(f"Note already exists: {file_path}")
        return

    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace placeholders
        note_content = template_content.replace("{{date:YYYY-MM-DD}}", date_str)
        note_content = note_content.replace("{{title}}", f"{date_str} {weekday_str}")

        with open(file_path, 'w') as f:
            f.write(note_content)
        
        print(f"Created daily note: {file_path}")

    except Exception as e:
        print(f"Error creating daily note: {e}")

if __name__ == "__main__":
    create_daily_note()
