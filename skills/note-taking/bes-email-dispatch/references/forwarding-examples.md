# Justin's Forwarded Email Examples and Expected Dispatches

This reference provides exact mockups of inputs and output tool calls to guide the agent's reasoning.

## Case 1: File Only (with Context)

### Input `instruction`:
```
File this. I like the idea about the flux capacitor. I wonder if we could use it for the improbablity engine.
```

### Expected Behavior:
- **Intents:** File only.
- **Vault Note Path:** `/home/justin.guest/vault/Inbox/2026-06-05-cool-science-idea.md` (assuming subject was "Cool Science Idea")
- **Context section in markdown:**
  ```markdown
  ## Context
  I like the idea about the flux capacitor. I wonder if we could use it for the improbablity engine.
  ```

---

## Case 2: Task Only (with Context & Due Date)

### Input `instruction`:
```
Task due Friday. Gotta finish the book before the weekend.
```

### Expected Behavior:
- **Intents:** Task only.
- **Todoist Task Creation:**
  - `content`: "Read/Finish book" (actionable name derived from email/context)
  - `dueString`: "Friday"
  - `description`: "Gotta finish the book before the weekend."
  - `projectId`: "6VGcQ7r6HW5r87j9" (Inbox)
- **Todoist Task Comment:**
  - Add a comment containing a summary of the email (sender, recipient, date, core content).

---

## Case 3: Dual Action (File + Task)

### Input `instruction`:
```
File this. I like the idea about the flux capacitor. I wonder if we could use it for the improbablity engine.
Task due Friday. Gotta finish the book before the weekend.
```

### Expected Behavior:
- **Intents:** Both File and Task.
- **Step 1: File Email to Vault:**
  - Save to `/home/justin.guest/vault/Inbox/...`
  - Put "I like the idea about the flux capacitor..." under `## Context`.
- **Step 2: Create Todoist Task:**
  - Create the task in Inbox with `content`: "Finish reading about the improbability engine" (or "Finish the book")
  - Set `dueString`: "Friday"
  - Set `description`: "Gotta finish the book before the weekend."
  - Immediately comment on the task with the email's sender/recipient metadata and a concise summary.
