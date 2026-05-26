---
name: todoist
description: "Use whenever Justin asks you to capture, find, complete, schedule, defer, or organize a task — or when you should proactively offer to (e.g. he says 'I need to remember to X', 'follow up on Y next week', 'the next step is Z'). Wraps the 54 `mcp_todoist_*` tools the Doist MCP server exposes. Covers tool selection, write hygiene, the status-project model (Now/Next/Later/Maybe), Obsidian-project linkage, and Justin-specific conventions."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [todoist, task-management, productivity, mcp]
    related_skills: [native-mcp, obsidian]
---

# Todoist (Bes scope — full Todoist)

Justin's task system. Todoist Pro account (uid `49270620`), shared between Hermes and Bes via Doist's official MCP server (`@doist/todoist-mcp`, stdio, env `TODOIST_API_KEY`). **One token, one task list — both agents see the same Todoist, but they have different scopes.** Clio doesn't have it.

Bes's scope: **everything in Todoist**. Hermes is restricted to tasks labeled `hermes`; Bes operates across the full task list.

## Justin's Todoist model (the new shape — read this twice)

As of May 2026, Justin uses **simple Projects to represent statuses**. The structure is:

- **Top-level Projects represent status-based buckets:**
  - **Inbox** (id `6VGcQ7r6HW5r87j9`) — capture/triage bucket; tasks with no project go here
  - **Now** (id `6gj6m9W3hQMgpWFp`) — actionable now
  - **Next** (id `6gj6mxchHhffC7h9`) — review daily & move as appropriate
  - **Soon** (id `6gj6mCC4GffrVfwJ`) — review weekly & move as appropriate
  - **Maybe Later** (id `6gj6mGwQ95rW9Hw8`) — review monthly & move as appropriate
  - **Shopping** (id `6gh9QhMVFjJpMPr9`) — shopping list items
- **No Work/Home/Other top-level projects or GTD sub-projects** are used under this model.
- **Labels carry context** (area, location, person, status). Infer them from conversation even if not stated explicitly.

| Label | Type | Meaning |
|---|---|---|
| `work` | Area | Work tasks |
| `home` | Area | Home / personal tasks |
| `@<location>` | Location | Where the task needs to happen, e.g. `@costco`, `@office` |
| `<person>+` | Person | Person the task involves, e.g. `nana+`, `sam+`. Suffix `+`, not prefix — name comes first. (Mnemonic: Japanese "nana-to" = "with nana".) |
| `waiting` | Special | Delegated or blocked — waiting on someone/something |
| `hermes` | Special | Hermes-originated tasks — **do not touch** |

**Label deduction:** When Justin asks Bes to add a task, infer labels from context even if not explicitly stated. A task clearly about work gets `work`; one about picking something up at a specific store gets `@store-name`; one involving a specific person gets `+person`. If ambiguous, leave unlabeled — don't guess. Never infer `hermes` or add it to any task.

- **The `hermes` label** (id `2183843700`, teal) is reserved for Hermes-originated tasks. Bes should not apply, remove, or modify it. If you see it on a task, that means Hermes created it; treat it as a read signal, not something to manage.

## When to use

**Reactive (Justin asks):**

- "Add a task to…" / "remind me to…" / "put X on my list" → `add-tasks` (default to Inbox)
- "What's on my plate / due today / overdue?" → `find-tasks-by-date` (start with `today`, include overdue)
- "What's in Now / Next / Soon?" → `find-tasks(projectId="<status-project-id>")`
- "Mark X done" → `complete-tasks`
- "Reschedule X to Friday" → `reschedule-tasks` (NOT `update-tasks` — see Pitfalls)
- "Move X to Soon" / "this is blocked, push it to Soon" → `update-tasks(tasks=[{id, projectId: "6gj6mCC4GffrVfwJ"}])`
- "What did I get done this week?" → `find-completed-tasks` or `get-productivity-stats`
- "Add a note to that task" → `add-comments` (on the task, not the project)
- "What projects do I have?" → `find-projects` or `get-overview` (no projectId)

**Proactive (offer, then act if confirmed):**

- He says "I need to remember…" / "follow up next week…" / "next step is…" → offer to capture as a task. Don't silently create — confirm with one short clarifying line ("Want me to drop this in Todoist as 'X' due Friday?") unless the ask is unambiguous.
- After a long planning conversation produces a list of next actions → offer to batch-add them (`add-tasks` accepts an array up to 25).
- A meeting note in Obsidian generates obvious action items → offer to mirror them to Todoist (do not auto-sync; Justin sorts manually).
- An Obsidian project note acquires a clear "next action" that isn't yet in Todoist → offer to create the task with the project linked in the description.

**Don't use Todoist for:**

- Long-form planning, project briefs, meeting notes, research → that's **Obsidian** (use the `obsidian` skill). Todoist holds *atomic actionable items with a state*; Obsidian holds knowledge and project context.
- Recurring habits you'd track in a habit tracker (sleep, exercise) → recurring Todoist tasks work for these but Justin hasn't asked for that pattern; don't impose it.
- Anything Clio-related — Clio doesn't have the integration.

## Capture conventions (important)

- **Actions only.** Todoist is for atomic actionable items with a state. No informational notes, FYIs, or "heads up" entries. If it isn't something Justin will do, don't add it.
- **One concrete next action per task.** No sub-tasks-as-project-decomposition. If the work is multi-step, either (a) capture only the next concrete action and let the rest stay in Obsidian, or (b) batch-add several atomic tasks each pointing back at the same Obsidian project.
- **Descriptions must enable getting started.** The description should give Justin everything he needs to begin the task without hunting: where the details live (email thread, Slack channel, Linear issue), direct links or URLs, relevant phone numbers or contact info, deadline if known, and Obsidian project link if applicable. One line per piece of context. If the source has a URL or permalink, always include it. The bar: could Justin open the task cold and immediately know where to go and what to do?
- **Default project is Inbox** unless Justin names a status project (Now/Next/Soon/Maybe Later) or the task obviously belongs in one. He sorts manually from Inbox. When in doubt, default to Inbox — being too helpful with auto-routing is worse than being too conservative.
- **No App Store Connect issue emails.** Justin doesn't handle those — engineering does. Skip them when scanning email.

## Obsidian linkage convention

Bes is the agent that bridges Todoist and Obsidian. When linking the two:

- **Todoist task → Obsidian:** include the linkage in the task `description`. Use one of:
  - `Project: [[Project-Note-Name]]` — for tasks tied to a multi-step Obsidian project
  - `From: Meetings/2026-05-20 X.md` — for action items born out of a meeting note
  - `Source: <path or [[wikilink]]>` — for tasks generated from any other Obsidian context

  Keep the linkage on its own line so it's easy to scan in the Todoist UI.

- **Obsidian project note → Todoist:** when you're working in an Obsidian project note and need to track its open actions, query Todoist with a `searchText` matching the project name (e.g. `find-tasks(searchText="Project-Note-Name")`). This finds tasks whose descriptions reference the project. There is no formal back-link; the prose reference is the link.

- **Following a link:** if a task description mentions an Obsidian note and you need context to complete the work, load that note via your Obsidian skill. The agent that follows the link is the agent that does the work — don't try to push Todoist context out to Justin and ask him to look up the note.

## Capture from daily notes / email

When scanning Obsidian daily notes or email for action items:

1. **Daily notes**: check vault root (today's note) AND `Daily Notes/` archive (past days). Read the last 7 days.
2. **Skip completed items**: in daily notes, tasks marked `[x]` in the Things Log are done — skip them.
3. **Skip decisions-already-made**: entries in "Decisions Made" sections are not action items.
4. **Capture from Open Questions / Blockers**: these are the richest source of genuine open actions.
5. **Email noise to filter**: automated notifications, shipping/delivery, marketing newsletters, payment receipts, parking receipts, calendar invite confirmations, Todoist onboarding emails, App Store Connect issue alerts, Readwise summaries, Substack newsletters.
6. **Add descriptions**: include context (who to follow up with, relevant issue numbers, deadlines, Obsidian project link) in the task description — not in the content.
7. **Batch-add to Inbox**: use a single `add-tasks` call for all captured items, all routed to Inbox. Confirm with Justin first only if the list is large and contains uncertain items.

## Justin-specific conventions

1. **Don't over-create.** One well-shaped task beats five fragmented sub-bullets. When in doubt, ask. Justin would rather get one clarifying question than discover 8 micro-tasks in his Inbox.
2. **Inbox is the default destination.** Justin sorts manually into Now/Next/Soon/Maybe Later. Don't try to be helpful by routing for him.
3. **Priorities default to `p4`** (Todoist's lowest / unflagged). Only set `p1`/`p2` when Justin explicitly says "urgent", "high priority", "today", or similar. P3 is mid; P4 is the unspecified default.
4. **Create tasks when asked, no friction.** If Justin says "add X to my list", "create a task for Y", "remind me to Z" — just do it. Default destination is Inbox unless he specifies a status project. Infer labels from context (area, location, people) even if not mentioned explicitly. Don't ask for confirmation on straightforward captures — act, then confirm with one line.
5. **Be conservative with deletes.** Use `complete-tasks` to finish a task, NOT `delete-object`. The completed-task history is useful for retrospectives.
6. **Use natural-language dates.** `dueString: "tomorrow at 3pm"`, `"every monday"`, `"in 2 weeks"` — Todoist parses these correctly and preserves Justin's timezone (America/New_York). Don't construct ISO timestamps unless you have a specific reason.
7. **Don't touch the `hermes` label.** It's Hermes's identity marker. If a task is labeled `hermes`, that means the other agent created it. Leave the label alone; otherwise the task is fully in Bes's scope.

## The tool surface (54 tools, organized)

The MCP server registers these as `mcp_todoist_<name>` (hyphens become underscores). Don't try to memorize all of them — load this skill and reach for the ones below.

### Daily-use core

| Tool | Use for |
|---|---|
| `find-tasks-by-date` | "What's on my plate today / this week / overdue" — accepts `startDate='today'` to include overdue. Default `responsibleUserFiltering='unassignedOrMe'` is correct for a personal account. |
| `find-tasks` | Text search, project/section/label filtering, or a saved-filter ID. Don't pass both `searchText` and `filter` — pick one. For "what's in Now/Next/Soon/Maybe Later" use `projectId=<status-project-id>`. |
| `add-tasks` | Single task or batch of up to 25. Required: `content`. Common: `dueString` (natural language), `priority`, `projectId` (omit → Inbox), `description`, `labels`. |
| `complete-tasks` | Pass `ids: [...]`. Preserves recurrence (next occurrence auto-scheduled). |
| `reschedule-tasks` | Preserves recurrence. **Use this, NOT `update-tasks`, when moving a recurring task** (see Pitfall 1). |
| `update-tasks` | Edit content, description, priority, labels, project moves. Avoid using it to change due date on recurring tasks. Use `projectId` to move tasks between status projects. |

### Reading / overview

| Tool | Use for |
|---|---|
| `get-overview` | Markdown overview. No `projectId` = all projects + hierarchy. With `projectId` = that project's full task tree. Great for "show me Now" or "show me Maybe." |
| `user-info` | Confirm which Todoist account is connected (sanity check). Returns current local time, daily/weekly goal progress, plan. |
| `find-projects` | List projects. Search by name with `searchText`. Confirms the status-project IDs haven't changed. |
| `find-completed-tasks` | Default 7-day window. Set `since`/`until` for a custom range. For "what did I get done this week" use `responsibleUser` = current user from `user-info`. |
| `get-productivity-stats` | Daily/weekly completion counts, goal streaks, karma. The "am I actually moving" stat. |
| `find-activity` | Audit log — added/updated/deleted/completed events. Useful for retro questions like "when did I create this?" |

### Organizing

| Tool | Use for |
|---|---|
| `add-projects` / `update-projects` / `project-management` | **Don't restructure the Now/Next/Soon/Maybe Later scheme.** Justin owns the top-level project structure. Adding a project to that hierarchy needs explicit direction. |
| `add-sections` / `update-sections` / `find-sections` | Justin doesn't use sections. Do not add them. |
| `add-labels` / `update-labels` / `find-labels` | Labels are cross-project tags. Use the existing label scheme (above); don't invent new labels without confirming with Justin. Never touch the `hermes` label. |
| `add-filters` / `update-filters` / `find-filters` | Saved queries. Check `find-filters` for what Justin has set up. |

### Comments / notes on tasks

| Tool | Use for |
|---|---|
| `add-comments` | Per-task discussion thread. Use this when you want to leave context on a task that doesn't belong in the description ("Justin said in chat he wants this delayed until Q3", paste from an external source). One comment per task per interaction is the right cadence; don't spam. |
| `find-comments` | Read existing comments. Provide ONE of `taskId`, `projectId`, or `commentId`. |
| `update-comments` | Edit a comment. |

### Reminders (Pro feature, available on Justin's account)

| Tool | Use for |
|---|---|
| `add-reminders` | Three types: `relative` (minutes before due), `absolute` (specific time), `location` (geofence). Justin's timezone is America/New_York; let Todoist parse natural language. |
| `find-reminders` / `update-reminders` | CRUD. |

### Advanced (use rarely)

| Tool | When |
|---|---|
| `get-project-health` / `analyze-project-health` | Limited value under the status-project model (Now/Next/Soon/Maybe Later are buckets, not goal-bearing projects). Don't volunteer. |
| `get-project-activity-stats` | Daily completion counts per project, 1-12 week window. |
| `get-workspace-insights` | Workspace-level aggregation. Justin is on personal Pro; workspace tools are inert. |
| `add-goals` / `find-goals` / `complete-goals` / `link-goal-tasks` | Todoist's goals layer. Don't use unless Justin asks. |
| `find-project-collaborators` / `manage-assignments` / `list-workspaces` | Multi-user features. Justin is solo; mostly empty results. |
| `delete-object` | Destructive. ASK before using. Polymorphic: takes a `type` + `id`. |
| `fetch` / `fetch-object` / `search` | OpenAI-MCP-compat tools. `find-tasks` etc. are usually more useful. |
| `view-attachment` | View a file attached to a comment. |
| `list-resources` / `read-resource` / `list-prompts` / `get-prompt` | MCP protocol primitives. Almost never directly useful. |
| `reorder-objects` | Manual order changes. Justin orders manually; don't reorder. |
| `project-move` | Move project between personal and workspace. Inert for Justin's solo Pro setup. |

## Workflow patterns

### Pattern: capture a task mid-conversation

User says: "I need to follow up with Alex about the proposal next Tuesday."

1. Don't silently create. Confirm shape (and offer to link to an Obsidian project if relevant):
   > Want me to add "Follow up with Alex about the proposal" to Inbox, due next Tuesday? I can link it to [[Acme Proposal]] in the description if useful.
2. On confirm, call:
   ```
   add-tasks(tasks=[{
     content: "Follow up with Alex about the proposal",
     dueString: "next Tuesday",
     priority: "p4",
     description: "Project: [[Acme Proposal]]"
   }])
   ```
   Omit `projectId` → Inbox. Justin triages.
3. Immediately after creating, call `add-comments` with a one-sentence comment on the new task ID. Explain where it came from and why it was captured. Example: "From chat — Justin mentioned he needs to follow up with Alex before the proposal deadline." Keep it terse — one sentence, for future-Justin scanning his inbox.
4. Reply with one-line confirmation that includes the task ID (so Justin can ask "complete that one" later without re-searching).

### Pattern: "what's on my plate?"

```
find-tasks-by-date(startDate="today", daysCount=1, overdueOption="include-overdue")
```

Return a compact markdown list. Group by overdue / today, then by priority. Don't dump the full JSON; just `content • due • priority`. If the task description has a `Project: [[...]]` line, surface that.

For a weekly view: `startDate="today", daysCount=7`.

For "what's in Now specifically":
```
find-tasks(projectId="6gj6m9W3hQMgpWFp", limit=50)
```

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

One MCP call for all of them — `add-tasks` accepts up to 25 in a single batch. Re-confirm the list with Justin before sending. All to Inbox.

### Pattern: defer / reschedule

User says "push that to next week."

Use `reschedule-tasks`, NOT `update-tasks`:
```
reschedule-tasks(tasks=[{id: "<id>", date: "2026-05-27"}])
```

If Justin says "this is blocked — move it to Soon / Maybe Later" rather than rescheduling, that's a status-project move:
```
update-tasks(tasks=[{id: "<id>", projectId: "6gj6mGwQ95rW9Hw8"}])
```

`reschedule-tasks` preserves recurrence patterns; `update-tasks` with `dueString` can silently strip them (Pitfall 1).

### Pattern: bootstrap a new project (Todoist Project + Obsidian note)

Use the `manage-projects` skill for the full workflow. Summary:

1. Create a Todoist **Project** (capital P) nested under Work or Home.
2. Add flat tasks directly into that project (no sub-tasks, no `parentId`).
3. Create an Obsidian project note with `category: "[[Projects]]"` and `Todoist: <project URL>` in the body.

The link is bidirectional: Obsidian note body links to Todoist project URL; Todoist project name matches the Obsidian note filename. See `manage-projects` for exact steps and pitfalls.

### Pattern: capture already-completed items

When Justin says a task is already done, or "I think it's done?":

1. If there's any uncertainty, **verify first** before creating and completing. For tool/integration access tasks, run a smoke test (e.g. `slack whoami`, Linear `{ viewer { name } }` query, `ls ~/.hermes/google_tokens/`).
2. Create the task normally.
3. Call `complete-tasks` on it immediately.

Don't skip verification when Justin hedges — "I think it's done" is an invitation to check. The smoke test takes seconds and prevents a completed task from masking a broken integration.

### Pattern: mirror open actions from an Obsidian project

You're working in an Obsidian project note that has 3 obvious open actions in its "Next Steps" section. Justin asks: "What of this is actually on my Todoist?"

1. Query Todoist for tasks referencing the project:
   ```
   find-tasks(searchText="<project-note-name>", limit=20)
   ```
2. Compare against the project note's Next Steps section.
3. Surface to Justin: "These N are in Todoist; these M are in the note but not in Todoist. Want me to add the missing ones to Inbox?"
4. On confirm, batch-add the missing ones with `description: "Project: [[<project-note-name>]]"`.

## Filters (saved views)

Justin has four saved filters for temporal visibility:

| Filter | Query | ID |
|---|---|---|
| Now | `today \| overdue` | 2370421908 |
| Inbox | `#Inbox` | 2370421909 |
| This Week | `due before: sun` | 2370421613 |
| Next Week | `(due: next week \| due after: next week) & due before: 1 week after next week` | 2370421614 |
| This Month | `due before: first day & !due before: sun & !(due: next week \| due after: next week) & due before: 1 week after next week` | 2370421615 |
| Next Month | `due after: last day & due before: 1 month after first day` | 2370421861 |
| Later | `due after: 1 month after first day` | 2370421618 |
| No Date | `no date` | 2370421711 |

**Note:** `due: this week` is NOT valid Todoist filter syntax. Use `due before: sat` for this week. The `deadline:` keyword is also not supported in filter queries — filters are due-date only.

**Important:** Todoist's filter API does not support `deadline:` queries — only `due:` works. These filters are due-date only.

**Convention:** When a task has a deadline and needs to appear in these filters, set **both** a `deadlineDate` and a `dueString`. The deadline is the hard constraint; the due date is the "work on it by" date and what drives filter visibility.

## Pitfalls

1. **Don't use `update-tasks` to change due date on recurring tasks.** It replaces the entire due-string blob and can wipe the recurrence pattern. Use `reschedule-tasks` for date changes — it preserves recurrence. `update-tasks` is fine for content/description/priority/labels/projectId.

2. **Priorities are strings (`"p1"`–`"p4"`), not integers.** `priority: 1` or `priority: "1"` will error or silently default. Use `"p1"` / `"p2"` / `"p3"` / `"p4"`.

3. **Project IDs are strings, not numbers.** Todoist v1 API uses string IDs (e.g. `"6ggx3MPrfF5mj5PQ"`). Reference the IDs listed at the top of this skill, or read them back from `find-projects`.

4. **"Inbox" is a special project ID.** When adding to inbox, pass `projectId: "inbox"` — the MCP server resolves it. You can also omit `projectId` and most operations default correctly.

5. **`find-tasks` requires at least one filter.** Calling it with no args errors. Use `find-tasks-by-date` instead for "everything for today" — that one works with just `startDate`.

6. **Natural language dates default to noon ET.** `dueString: "tomorrow"` produces a date-only task. `dueString: "tomorrow at 3pm"` produces a specific time. If Justin wants a specific time, include it.

7. **`complete-tasks` on recurring tasks advances to the next occurrence, not completes-and-deletes.** Counter-intuitive: a daily task "completed" today reappears tomorrow. To stop a recurring task entirely, use `update-tasks` with `dueString: "remove"` then complete it, or `delete-object` (ask Justin first).

8. **Don't echo task descriptions back wholesale.** Descriptions may contain dense agent-oriented context. When summarizing tasks for him, default to `content` only; surface description lines only if they're directly relevant (Obsidian project link, blocker note, etc.).

9. **The MCP server runs as a subprocess of the Hermes gateway** (`npm exec @doist/todoist-mcp`). If tools start returning errors, check that the subprocess didn't die: `ps -ef | grep todoist-mcp`. A gateway restart respawns it. If tool registration is showing 0 tools in the agent log, the `TODOIST_API_KEY` env var didn't load — verify with `grep -c '^TODOIST_API_KEY=' ~/.hermes/.env`.

10. **One token, two clients (Hermes + Bes).** Both agents see the same task list. If Hermes adds a task (labeled `hermes`), Bes can find it and vice versa. Treat the task list as shared state. **Never apply, remove, or modify the `hermes` label** — that's Hermes's identity marker, not a shared signal.

11. **Don't reorganize the status-project structure.** Now/Next/Soon/Maybe Later is Justin's framework. Adding a fifth top-level project, archiving one of the four, or renaming them needs explicit direction. The same goes for sections: Justin doesn't use them under this model; don't add them.

12. **The Hermes agent has a deliberately narrower scope.** Hermes only writes to Inbox with the `hermes` label, and only reads tasks tagged `hermes`. If you see something in Now/Next/Soon/Maybe Later without the `hermes` label, that's Justin's or yours. Don't assume an unlabeled task is unattended — it may be Justin's manual entry that you shouldn't touch unless directed.

## Configuration (reference)

In `~/.hermes/config.yaml`:

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

## Reference IDs (as of May 2026)

```
Projects:
  Inbox        6VGcQ7r6HW5r87j9
  Now          6gj6m9W3hQMgpWFp
  Next         6gj6mxchHhffC7h9
  Soon         6gj6mCC4GffrVfwJ
  Maybe Later  6gj6mGwQ95rW9Hw8
  Shopping     6gh9QhMVFjJpMPr9

Labels:
  hermes  2183843700  (teal — Hermes's identity marker; do not touch)
  <!-- TODO: list the rest of the label scheme once settled with Justin -->
```

If any of these stop resolving, re-fetch via `find-projects` / `find-labels` and update this skill.

## Notes

- The MCP server is npm-distributed (`@doist/todoist-mcp`), maintained by Doist directly. It's the same tool surface that powers their Claude Desktop / Cursor / Claude Code integrations.
- The hosted alternative is `https://ai.todoist.net/mcp` with OAuth, but we chose the local stdio + API-token path because (a) Bes runs in a VM with no browser for OAuth, (b) one token works for multiple Hermes instances, (c) Justin already manages token-in-`.env` workflows fluently.
- Justin's quick-entry hotkey setup is out of scope for the agent. He handles client-side capture; agent-side Todoist is for tasks born in conversation with the agent.
- Hermes has a deliberately narrower version of this skill (scope: tasks labeled `hermes` only). The two skills are intentionally divergent.
