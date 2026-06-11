---
name: hermes-vm-safety-and-stability
description: Audit and harden the Hermes VM configuration, active cron jobs, and background scripts for safety, autonomy boundaries, and stability.
category: autonomous-ai-agents
tags:
  - safety
  - autonomy
  - system-administration
  - cron-jobs
  - auditing
---

# Hermes VM Safety & Stability Auditing

For a copy of Justin's complete Safety & Autonomy Guidance, see [references/guidance.md](references/guidance.md).

Use this skill when auditing or adjusting the Hermes VM environment, configuring credentials/tool limits, debugging background cron-job failures, or ensuring alignment with Justin's "VM Safety & Autonomy Guidance."

## 1. Safety & Autonomy Checklists

Always audit the primary configuration file (`~/.hermes/config.yaml`) for compliance with safety principles:

### A. Security & Boundary Settings
* **Tirith Policy Engine:** Verify that `security.tirith_fail_open` is set to `false`. Enforce fail-closed verification so unauthorized or failed verification shuts down the action.
* **Lazy Installs:** Verify that `security.allow_lazy_installs` is set to `false`. Do not allow the agent to install random external packages (npm, pip) on-the-fly without confirmation.
* **Sandbox Verification:** Ensure private URLs and network fetches conform to `security.allow_private_urls: false` unless explicitly overridden for internal tools.

### B. Background Job Hardening
* **Least Privilege:** Background or cron jobs (like `Daily Work Log`) must not run with unrestricted toolsets. Check active job definitions and explicitly restrict `enabled_toolsets` to the bare minimum (e.g. `['terminal', 'file']`).
* **Silent Execution:** For script-only pings (watchdogs, checkers), prefer `no_agent: true` with a silent script that only calls the LLM via `hermes run` when actionable conditions are met. Avoid active LLMs polling empty states every 30 minutes.

---

## 2. Resource & Stability Constraints

To prevent VM crashes, disk exhaustion, or hung background tasks, enforce these system-level constraints:

### A. Concurrency and Memory
* **Max Parallel Jobs:** Limit `cron.max_parallel_jobs` to a low integer (e.g., `2` or `3`) instead of leaving it `null` (unbounded), preventing multi-job execution from triggering Out-Of-Memory (OOM) faults.
* **Disk Space Management:** Always configure `sessions.auto_prune: true` with a reasonable retention window (e.g. `90` days) to prevent JSON logs and terminal snapshots from consuming all available VM disk storage.

### B. Timeout Alignment
* **Subprocess Timeouts:** Every background python or bash script must define internal subprocess timeouts. Never let `subprocess.run` run without a `timeout=` parameter.
* **Scheduler Sync:** Ensure subprocess timeouts are strictly smaller than the scheduler's task timeout limit. If the scheduler kills a task at 120s, the inner script should timeout at 100s to allow graceful reporting and logging.
* **Decouple Heavy Workloads:** Long-running processes like semantic indexing (`semantic_pointer.py index`) should never be embedded directly inside high-frequency cron scripts. Decouple them into separate, lower-priority standalone crons.

---

## 3. Audit Execution Guidelines

* **Model Selection:** Always execute system-wide audits and multi-file reasoning reviews on high-reasoning models (such as `gemini-2.5-pro` or equivalent). Do not use flash/lightweight models, as they consistently fail by exceeding maximum turn counts (`max_iterations`) and frequently overlook subtle safety violations.
* **Live Model Discovery:** When switching models programmatically or modifying configs, verify live model availability from the provider list using the API or a fast Python request to avoid 404 Model Not Found errors.
* **Verification over Description:** Never merely assume a configuration has been corrected. After writing to `config.yaml`, run syntax validation or test command execution to verify VM stability.
