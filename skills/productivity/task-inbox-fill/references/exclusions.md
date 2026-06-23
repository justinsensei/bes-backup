# Inbox Candidate Exclusions

To prevent clutter in Justin's Todoist Inbox, the following sources and item states must be strictly excluded from all candidate sweeps and inbox-fill suggestions:

1. **iMessages (Family / Personal)**
   - **Rule:** Do not query or parse iMessages as an input source for inbox fills. 
   - **Reason:** Family texts and personal chats are private/conversational and should not be automatically staged into a task-management inbox.

2. **Archived Emails**
   - **Rule:** Only scan the active Gmail Inbox (`in:inbox` filter). Do not capture or suggest tasks from archived messages.
   - **Reason:** Once an email is archived, Justin has already processed it, so suggesting a task from it is redundant.

3. **Assigned Linear Issues with Inactive States**
   - **Rule:** Exclude Linear issues whose status types are `triage`, `backlog`, `completed`, or `canceled`. Only include active execution states (e.g. `unstarted` / To Do, `started` / In Progress, or custom `Monitoring` state).
   - **Reason:** Keeps focus strictly on active, near-term work items Justin is currently executing, filtering out backlog/triage noise.
