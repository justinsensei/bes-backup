---
name: todoist
description: "Use whenever Justin asks you to capture, find, complete, schedule, defer, or organize a task — or when you should proactively offer to (e.g. he says 'I need to remember to X', 'follow up on Y next week', 'the next step is Z'). Wraps the 54 `mcp_todoist_*` tools the Doist MCP server exposes. Covers tool selection, write hygiene, default routing, recurring vs one-shot, and Justin-specific conventions."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [todoist, task-management, productivity, mcp]
    related_skills: [native-mcp, obsidian]
---

# Todoist (shared with Bes)

Justin's task system. Todoist Pro account (uid `49270620`), shared between this Hermes and Bes via Doist's official MCP server (`@doist/todoist-mcp`, stdio, env `TODOIST_API_KEY`). **One token, one task list — both agents see the same Todoist.** Clio doesn't have it; don't try to use these tools from Clio.

## When to use

**Reactive (Justin asks):**

- "Add a task to…" / "remind me to…" / "put X on my list" → `add-tasks`
- "What's on my plate / due today / overdue?" → `find-tasks-by-date` (start with `today`, include overdue)
- "Mark X done" → `complete-tasks`
- "Reschedule X to Friday" → `reschedule-tasks` (NOT `update-tasks` — see Pitfalls)
- "What did I get done this week?" → `find-completed-tasks` or `get-productivity-stats`
- "Add a note to that task" → `add-comments` (on the task, not the project)
- "What projects do I have?" → `find-projects` or `get-overview` (no projectId)

**Proactive (offer, then act if confirmed):**

- He says "I need to remember…" / "follow up next week…" / "next step is…" → offer to capture as a task. Don't silently create — confirm with one short clarifying line ("Want me to drop this in Todoist as 'X' due Friday?") unless the ask is unambiguous.
- After a long planning conversation produces a list of next actions → offer to batch-add them (`add-tasks` accepts an array up to 25).
- A meeting note in Obsidian generates obvious action items → offer to mirror them to Todoist (do not auto-sync; Justin sorts manually).

**Don't use Todoist for:**

- Long-form planning, project briefs, meeting notes, research → that's **Obsidian** (use the `obsidian` skill). Todoist is for *actionable items with a state*; Obsidian is for knowledge.
- Recurring habits you'd track in a habit tracker (sleep, exercise) → recurring Todoist tasks work for these but Justin hasn't asked for that pattern; don't impose it.
- Anything Clio-related — Clio doesn't have the integration, so don't tell Justin "I'll add this to Clio's Todoist."

## Justin's GTD structure

Justin uses Todoist as a GTD system. The full structure is in `references/justin-gtd-structure.md`. Key facts for daily use:

- **Projects = areas of focus**: Work (blue), Personal (green). `#Hermes` is a sub-Project under Work — tasks there are actioned BY the Hermes infra agent, not Justin.
- **Someday Maybe** is a section inside each Project (not a separate Project). Any task dropped there **must also get the `@someday` label** — this is how the Next Actions filters exclude them (Todoist can't filter by section).
- **`@waiting`** = delegated or blocked. **`@someday`** = Someday Maybe. Both labels must be applied manually at capture time.
- **Default routing**: Inbox, unless Justin names a project or it obviously belongs in Work/Personal.
- **Filters**: "Next Actions — Work", "Next Actions — Personal", "Waiting For" — already created, don't recreate.

## Capture from daily notes / email

When scanning Obsidian daily notes or email for action items:

1. **Daily notes**: check vault root (today's note) AND `Daily Notes/` archive (past days). Read the last 7 days.
2. **Skip completed items**: in daily notes, tasks marked `[x]` in the Things Log are done — skip them.
3. **Skip decisions-already-made**: entries in "Decisions Made" sections are not action items.
4. **Capture from Open Questions / Blockers**: these are the richest source of genuine open actions.
5. **Email noise to filter**: automated notifications, shipping/delivery, marketing newsletters, payment receipts, parking receipts, calendar invite confirmations, Todoist onboarding emails, App Store Connect issue alerts (Justin is not the one who handles those), Readwise summaries, Substack newsletters.
6. **Add descriptions**: include context (who to follow up with, relevant issue numbers, deadlines) in the task description — not in the content.
7. **Batch-add**: use a single `add-tasks` call for all captured items. Confirm with Justin first only if the list is large and contains uncertain items.

## Justin-specific conventions

1. **Don't over-create.** One well-shaped task beats five fragmented sub-bullets. When in doubt, ask. Justin would rather get one clarifying question than discover 8 micro-tasks in his inbox.
2. **Default project is Inbox** unless Justin names one or the task obviously belongs elsewhere. He sorts manually, like with Obsidian root-folder notes.
3. **Priorities default to `p4`** (Todoist's lowest / unflagged). Only set `p1`/`p2` when Justin explicitly says "urgent", "high priority", "today", or similar. P3 is mid; P4 is the unspecified default.
4. **Don't pre-empt his hotkey workflow.** Justin has his own quick-entry tooling for the casual case. Hermes-side Todoist is for tasks that arise IN conversation with the agent — meeting summaries, follow-ups discovered while researching, etc.
5. **Be conservative with deletes.** Use `complete-tasks` to finish a task, NOT `delete-object`. Justin's secrets-in-chat rule generalizes: when destructive, ask first. The completed-task history is useful for retrospectives.
6. **Use natural-language dates.** `dueString: "tomorrow at 3pm"`, `"every monday"`, `"in 2 weeks"` — Todoist parses these correctly and preserves Justin's timezone (America/New_York). Don't construct ISO timestamps unless you have a specific reason; natural language is more readable in his inbox.
7. **Pre-paired with Obsidian.** A meeting in Obsidian that produces action items can link the source: include the Obsidian note path in the task `description` (e.g. `"From: Meetings/2026-05-20 Catchup with X.md"`). When Justin completes the task he has provenance.

## The tool surface (54 tools, organized)

The MCP server registers these as `mcp_todoist_<name>` (hyphens become underscores). Don't try to memorize all of them — load this skill and reach for the ones below.

### Daily-use core

| Tool | Use for |
|---|---|
| `find-tasks-by-date` | "What's on my plate today / this week / overdue" — accepts `startDate='today'` to include overdue. Default `responsibleUserFiltering='unassignedOrMe'` is correct for a personal account. |
| `find-tasks` | Text search, project/section/label filtering, or a saved-filter ID. Don't pass both `searchText` and `filter` — pick one. |
| `add-tasks` | Single task or batch of up to 25. Required: `content`. Common: `dueString` (natural language), `priority`, `projectId`, `description`, `labels`. |
| `complete-tasks` | Pass `ids: [...]`. Preserves recurrence (next occurrence auto-scheduled). |
| `reschedule-tasks` | Preserves recurrence. **Use this, NOT `update-tasks`, when moving a recurring task** (see Pitfall 1). |
| `update-tasks` | Edit content, description, priority, labels, project/section moves. Avoid using it to change due date on recurring tasks. |

### Reading / overview

| Tool | Use for |
|---|---|
| `get-overview` | Markdown overview. No `projectId` = all projects + hierarchy. With `projectId` = that project's full task tree. Great for "show me my Todoist." |
| `user-info` | Confirm which Todoist account is connected (sanity check on multi-account setups). Returns current local time, daily/weekly goal progress, plan. |
| `find-projects` | List projects. Search by name with `searchText`. |
| `find-completed-tasks` | Default 7-day window. Set `since`/`until` for a custom range. For "what did I get done this week" use `responsibleUser` = current user from `user-info`. |
| `get-productivity-stats` | Daily/weekly completion counts, goal streaks, karma. The "am I actually moving" stat. |
| `find-activity` | Audit log — added/updated/deleted/completed events. Useful for retro questions like "when did I create this?" |

### Organizing

| Tool | Use for |
|---|---|
| `add-projects` / `update-projects` / `project-management` | CRUD on projects. `project-management` is for archive/unarchive. Justin organizes manually — don't restructure projects without asking. |
| `add-sections` / `update-sections` / `find-sections` | Sections live inside projects. |
| `add-labels` / `update-labels` / `find-labels` | Labels are cross-project tags. |
| `add-filters` / `update-filters` / `find-filters` | Saved queries (Todoist's killer feature). Justin may have custom filters; check `find-filters` before building one. |

### Comments / notes on tasks

| Tool | Use for |
|---|---|
| `add-comments` | Per-task discussion thread. Use this when Hermes wants to leave context on a task ("Created from chat session 20260520; the Linear issue is #1234"). One comment per task per Hermes interaction is the right cadence; don't spam. |
| `find-comments` | Read existing comments. Provide ONE of `taskId`, `projectId`, or `commentId`. |
| `update-comments` | Edit a comment. |

### Reminders (Pro feature, available on Justin's account)

| Tool | Use for |
|---|---|
| `add-reminders` | Three types: `relative` (minutes before due), `absolute` (specific time), `location` (geofence). Justin's timezone is America/New_York; let Todoist parse natural language and don't construct UTC by hand. |
| `find-reminders` / `update-reminders` | CRUD. |

### Advanced (use rarely)

| Tool | When |
|---|---|
| `get-project-health` / `analyze-project-health` | Project-status assessment — "is this project actually moving." Real value, but ask before triggering on Justin's projects. `analyze-` triggers a fresh analysis (may take time); `get-` returns the cached result. |
| `get-project-activity-stats` | Daily completion counts per project, 1-12 week window. |
| `get-workspace-insights` | Workspace-level aggregation. Justin is on personal Pro; workspace tools are inert unless he's added to one. |
| `add-goals` / `find-goals` / `complete-goals` / `link-goal-tasks` | Todoist's goals layer. Don't use unless Justin asks — overhead exceeds value for a personal task list. |
| `find-project-collaborators` / `manage-assignments` / `list-workspaces` | Multi-user features. Justin is solo; these will mostly return empty results. |
| `delete-object` | Destructive. ASK before using. Polymorphic: takes a `type` (task/project/section/comment/label/filter/goal/reminder/location_reminder) + `id`. |
| `fetch` / `fetch-object` / `search` | OpenAI-MCP-compat tools. `find-tasks` etc. are usually more useful; reach for these only if a tool result references a `task:<id>` / `project:<id>` URI. |
| `view-attachment` | View a file attached to a comment. |
| `list-resources` / `read-resource` / `list-prompts` / `get-prompt` | MCP protocol primitives. Almost never directly useful. |
| `reorder-objects` | Manual order changes. Justin orders manually; don't reorder without being asked. |
| `project-move` | Move project between personal and workspace. Inert for Justin's solo Pro setup. |

## Workflow patterns

### Pattern: capture a task mid-conversation

User says: "I need to follow up with Alex about the proposal next Tuesday."

1. Don't silently create. Confirm shape:
   > Want me to add "Follow up with Alex about the proposal" to Todoist, due next Tuesday?
2. On confirm, call:
   ```
   add-tasks(tasks=[{
     content: "Follow up with Alex about the proposal",
     dueString: "next Tuesday",
     priority: "p4",
   }])
   ```
3. Reply with one-line confirmation that includes the task ID (so Justin can ask "complete that one" later without re-searching).

### Pattern: "what's on my plate?"

```
find-tasks-by-date(startDate="today", daysCount=1, overdueOption="include-overdue")
```

Return a compact markdown list. Group by overdue / today, then by priority. Don't dump the full JSON; just `content • due • priority`.

For a weekly view: `startDate="today", daysCount=7`.

### Pattern: end-of-week / retrospective

```
find-completed-tasks(
  since="<monday>",
  until="<today>",
  responsibleUser="<user_id from user-info>"
)
```

Pair with `get-productivity-stats` for the streak + karma context. Render as a short markdown summary, NOT a full enumeration of every completed task.

### Pattern: batch-capture from a meeting note

If Justin reviewed a meeting in Obsidian and produced 4 action items:

```
add-tasks(tasks=[
  {content: "...", dueString: "...", description: "From: Meetings/2026-05-20 X.md"},
  {content: "...", dueString: "...", description: "From: Meetings/2026-05-20 X.md"},
  ...
])
```

One MCP call for all of them — `add-tasks` accepts up to 25 in a single batch. Re-confirm the list with Justin before sending.

### Pattern: defer / reschedule

User says "push that to next week."

Use `reschedule-tasks`, NOT `update-tasks`:

```
reschedule-tasks(tasks=[{id: "<id>", date: "2026-05-27"}])
```

`reschedule-tasks` preserves recurrence patterns; `update-tasks` with `dueString` can silently strip them on recurring tasks (Pitfall 1).

## Justin's GTD setup

Justin runs a lightweight GTD structure in Todoist. See `references/gtd-setup.md` for full detail. Key facts:

- **Projects (areas):** `#Work` (blue), `#Personal` (green). Sub-project: `#Hermes` under `#Work` (Hermes Agent infra work, actioned by Hermes agent — not Bes).
- **GTD projects** = tasks with subtasks inside those Projects. Not separate Todoist Projects.
- **Someday Maybe** = a section inside each Project (contextualizes by area). Items in those sections get `@someday`.
- **Labels:** `@waiting` (orange) for delegated/blocked; `@someday` (grey) for Someday Maybe items.
- **Filters:** "Next Actions — Work" (`#Work & !@waiting & !@someday`), "Next Actions — Personal" (`#Personal & !@waiting & !@someday`), "Waiting For" (`@waiting`).
- **Inbox** = default Todoist inbox, no special conventions yet.
- Naming: "Someday Maybe" (no slash).

## Pitfalls

11. **Todoist filters cannot filter by section.** A filter like `#Work & !@someday` works; `#Work & !/Someday Maybe` does not — section-based exclusion isn't supported. Workaround: pair every organizational section with a label and filter on the label. This is why Justin's Someday Maybe sections require the `@someday` label on every item dropped into them.

1. **Don't use `update-tasks` to change due date on recurring tasks.** It replaces the entire due-string blob and can wipe the recurrence pattern. Use `reschedule-tasks` for date changes — it preserves recurrence. `update-tasks` is fine for content/description/priority/labels/projectId.

2. **Priorities are strings (`"p1"`–`"p4"`), not integers.** `priority: 1` or `priority: "1"` will error or silently default. Use `"p1"` / `"p2"` / `"p3"` / `"p4"`.

3. **Project IDs are strings, not numbers.** Todoist v1 API uses string IDs (e.g. `"6VGcQ7r6HW5r87j9"`). Don't try to construct them; always read them back from `find-projects` or a previous `add-tasks` response.

4. **"Inbox" is a special project ID.** When adding to inbox, pass `projectId: "inbox"` — the MCP server resolves it. You can also omit `projectId` and most operations default correctly.

5. **`find-tasks` requires at least one filter.** Calling it with no args errors. Use `find-tasks-by-date` instead for "everything for today" — that one works with just `startDate`.

6. **Natural language dates default to noon ET.** `dueString: "tomorrow"` produces a date-only task. `dueString: "tomorrow at 3pm"` produces a specific time. If Justin wants a specific time, include it; otherwise leave it date-only and let his Todoist preferences handle defaults.

7. **`complete-tasks` on recurring tasks advances to the next occurrence, not completes-and-deletes.** This is correct behavior, but counter-intuitive: a daily task "completed" today reappears tomorrow. To stop a recurring task entirely, use `update-tasks` with `dueString: "remove"` then complete it, or `delete-object` (ask Justin first).

8. **Don't echo task descriptions back wholesale.** Descriptions may contain notes Justin wants kept private. When summarizing tasks for him, default to `content` only; surface `description` only if it's directly relevant to the question.

9. **The MCP server runs as a subprocess of the Hermes gateway** (`npm exec @doist/todoist-mcp`). If tools start returning errors, check that the subprocess didn't die: `ps -ef | grep todoist-mcp`. A gateway restart respawns it. If tool registration is showing 0 tools in the agent log, the `TODOIST_API_KEY` env var didn't load — verify with `grep -c '^TODOIST_API_KEY=' ~/.hermes/.env`.

10. **One token, two clients (Hermes + Bes).** Both agents see the same task list. If Bes adds a task, this Hermes can find it and vice versa. Treat the task list as shared state; don't assume "I didn't create it" means it doesn't exist.

## Configuration (reference)

In `~/.hermes/config.yaml` on each instance that should have Todoist:

```yaml
mcp_servers:
  todoist:
    command: "npx"
    args: ["-y", "@doist/todoist-mcp"]
    env:
      TODOIST_API_KEY: "${TODOIST_API_KEY}"
    timeout: 120
    connect_timeout: 60
```

Token via `hermes config set TODOIST_API_KEY '...'` (writes to `~/.hermes/.env`, never committed).

On restart, look for `MCP server 'todoist' (stdio): registered 54 tool(s)` in `~/.hermes/logs/agent.log`. If you see anything less than 54, something's wrong with the env var or the package version.

## Reference files

- `references/justin-gtd-structure.md` — Justin's full GTD project/label/filter structure with design rationale. Load this before restructuring anything or setting up new Projects/filters.

## Notes

- The MCP server is npm-distributed (`@doist/todoist-mcp`), maintained by Doist directly. It's the same tool surface that powers their Claude Desktop / Cursor / Claude Code integrations. Read the [GitHub repo](https://github.com/Doist/todoist-mcp) for upstream updates and new tools.
- The hosted alternative is `https://ai.todoist.net/mcp` with OAuth, but we chose the local stdio + API-token path because (a) Bes runs in a VM with no browser for OAuth, (b) one token works for multiple Hermes instances, (c) Justin already manages token-in-`.env` workflows fluently.
- Justin's quick-entry hotkey setup is out of scope for the agent. He handles client-side capture; Hermes-side Todoist is for tasks born in conversation with the agent.
