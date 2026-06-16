---
name: kanban-workflows
description: "Master Kanban-based multi-agent coordination: Orchestration plays, decomposition, task graph linking, workspace kinds, and worker handoff formatting."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Kanban, DevOps, Orchestration, Workers, Multi-Agent, Dispatcher]
---

# Kanban-Based Multi-Agent Workflows

This master skill governs the lifecycle and playbook for coordinating, routing, fanning out, and executing tasks through the SQLite-backed Kanban system. It spans two key roles:
1. **Orchestrator Role:** Decomposition, routing, scheduling, and task graph construction.
2. **Worker Role:** Executing, isolating, updating heartbeats, commenting, and complete/block handoffs.

---

## 1. Orchestration & Task Decomposition

The Orchestrator's core directive is: **"Route, don't execute."** Do not do the implementation work yourself — break it down and assign it to available profiles.

### Step 0: Profile Discovery
Assignee profiles are custom-configured on each machine. Discover which profiles are available before spawning tasks:
- Run `hermes profile list` via terminal to see active profiles.
- Cache the discovered names in memory. Never guess or invent assignees, or the dispatcher will silently drop the cards.

### Task Graph Creation
When creating tasks, draft the dependency graph out loud. Link true data dependencies using `parents=[...]` during creation:
1. **Extract Lanes:** Separate independent streams of work.
2. **Assign Owners:** Map lanes to discovered assignee profiles.
3. **Determine Gates:** Check if a lane depends on another lane's output.
4. **Create Cards:** Independent cards are created with no parents (ready for execution). Dependent cards are created with finished parents linked so they remain in `todo` status until parents complete.

### Code Example
```python
# Create parent/independent research task
t1 = kanban_create(
    title="research: api latency specs",
    assignee="researcher-profile",
    body="Gather latency and throughput limits for our third-party provider APIs.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

# Create child task gated by research output
t2 = kanban_create(
    title="impl: api caching layers",
    assignee="engineer-profile",
    body="Implement local caching layer based on the latency specs gathered in task t1.",
    parents=[t1],
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]
```

---

## 2. Worker Execution Guidelines

Workers must execute their assigned tasks in isolated directories and follow strict status guidelines.

### Workspace Kinds & Isolation
Your work folder is specified by `$HERMES_KANBAN_WORKSPACE`:
- `scratch`: Temporary directory. Read and write freely; garbage collected when the task archives.
- `dir:<path>`: Persistent shared directory. Treat files as long-lived state.
- `worktree`: Git worktree. Run `git worktree add <path>` from the main repo if `.git` is missing, commit code directly inside the worktree, and push.

### Tenant Isolation
If `$HERMES_TENANT` is defined, always prefix memory entries or shared database records to prevent data leakage across client scopes:
- **Correct:** `client-acme: database port is 5432`
- **Incorrect:** `database port is 5432`

---

## 3. Worker Handoff and Completion Shapes

How downstream workers or reviewers read your output is determined by how you exit the task.

### Simple Completion (Terminal Tasks)
Use `kanban_complete` only when the task is genuinely complete and has no functional code changes (e.g., research, document writes, typo fixes).
```python
kanban_complete(
    summary="benchmark completed: SGLang showed lowest latency at 12ms",
    metadata={
        "sources_checked": 5,
        "recommended_lib": "SGLang",
        "benchmark_runs": {"sglang": 12.1, "vllm": 15.4}
    }
)
```

### Review-Required Blocking (Code Changes)
For code changes or tasks requiring human alignment, **do not complete**. Post a comment with details and then set the task to blocked using the `review-required: ` reason prefix to highlight it on the dashboard:
```python
import json

# Log detailed metadata as a comment
kanban_comment(
    body="review-required handoff:\n" + json.dumps({
        "changed_files": ["api/routes.py"],
        "tests_run": 8,
        "tests_passed": 8,
        "diff_path": "/path/to/worktree"
    }, indent=2)
)

# Block the task with a review-required reason
kanban_block(
    reason="review-required: routes implemented, all tests passing. Needs eye-ball check on database indices."
)
```
