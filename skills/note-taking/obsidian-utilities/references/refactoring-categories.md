# Category Refactoring Recipe: Renaming Vault Categories

When renaming an Obsidian category, the change must be applied atomically and systematically across the entire vault and the Hermes skill library.

## Renaming Procedure

### 1. Rename and Update the Category Definition Note
Rename the markdown file representing the category in the vault utilities directory:
- **Path:** `/home/justin.guest/vault/Utilities/Categories/<OldName>.md` $\rightarrow$ `/home/justin.guest/vault/Utilities/Categories/<NewName>.md`
- **Content:** Inside the renamed file, update the main H1 title to match the new category name:
  ```markdown
  # <NewName>
  ```

### 2. Update Subcategory Lists
Check for category hierarchy index files that contain links to the old category and update them.
- **Example:** `/home/justin.guest/vault/Utilities/Categories/Notes.md` contains a list of subcategories. Update `- [[<OldName>]]` to `- [[<NewName>]]`.

### 3. Bulk Update Note Frontmatter
Scan the entire vault directory for all files that carry the category frontmatter property, and replace it.
- **Old property:** `category: "[[<OldName>]]"`
- **New property:** `category: "[[<NewName>]]"`

### 4. Bulk Update Skills
Search for occurrences of the old category name or link inside `~/.hermes/skills/` (excluding unrelated system definitions like CPU memory/RAM references) and update them.

---

## Automation Script

Below is a robust Python template to automate this entire workflow.

```python
import os

vault_path = "/home/justin.guest/vault"
skills_path = "/home/justin.guest/.hermes/skills"

old_name = "Memory"
new_name = "Memories"

# 1. Rename category definition file
old_file = os.path.join(vault_path, f"Utilities/Categories/{old_name}.md")
new_file = os.path.join(vault_path, f"Utilities/Categories/{new_name}.md")

if os.path.exists(old_file):
    with open(old_file, "r") as f:
        content = f.read()
    updated = content.replace(f"# {old_name}", f"# {new_name}")
    with open(new_file, "w") as f:
        f.write(updated)
    os.remove(old_file)
    print(f"Renamed category file: {old_name}.md -> {new_name}.md")

# 2. Update parents or other links in Categories directory
notes_index = os.path.join(vault_path, "Utilities/Categories/Notes.md")
if os.path.exists(notes_index):
    with open(notes_index, "r") as f:
        content = f.read()
    if f"[[{old_name}]]" in content:
        content = content.replace(f"[[{old_name}]]", f"[[{new_name}]]")
        with open(notes_index, "w") as f:
            f.write(content)
        print(f"Updated subcategory link in Notes.md")

# 3. Bulk-update vault notes
notes_dir = os.path.join(vault_path, "Notes")
count = 0
for root, _, files in os.walk(notes_dir):
    for file in files:
        if file.endswith(".md"):
            p = os.path.join(root, file)
            with open(p, "r") as f:
                content = f.read()
            target = f'category: "[[{old_name}]]"'
            if target in content:
                updated = content.replace(target, f'category: "[[{new_name}]]"')
                with open(p, "w") as f:
                    f.write(updated)
                count += 1
print(f"Updated {count} notes in vault/Notes/")

# 4. Bulk-update skill files
skills_to_update = [
    # list of relative paths and replacement pairs here
]
```
