---
name: runtime-debugging
description: Interactive runtime debugging and breakpoint stepping for Python (pdb, debugpy, remote-pdb) and Node.js (node inspect, CDP via chrome-remote-interface, vitest).
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, node-inspect, cdp, breakpoints, step]
    related_skills: [systematic-debugging, test-driven-development]
---

# Runtime Debugging: Python & Node.js

This skill provides comprehensive instructions for terminal-based interactive runtime debugging, breakpoint injection, and step-through inspection in both Python and Node.js environments.

---

## 1. Python Debugging (pdb + debugpy)

Three primary interfaces are available, chosen by situation:

| Tool | When | Usage |
|---|---|---|
| **`breakpoint()` + pdb** | Local, interactive, simplest. | Add `breakpoint()` in source, run normally. |
| **`python -m pdb`** | Launch a script under pdb with no source edits. | `python -m pdb script.py` |
| **`remote-pdb` / `debugpy`** | Headless or attaching to an already-running process. | Inject remote listeners for external connection. |

### pdb Quick Reference
Inside any pdb prompt (`(Pdb)`):
- `n` (next / step over), `s` (step into), `r` (return), `c` (continue)
- `l` / `ll` (list source around current line / full function)
- `w` (where / show call stack), `u` / `d` (move up / down stack frames)
- `p expr` / `pp expr` (print / pretty-print expression)
- `!stmt` (execute arbitrary Python statement / assign values)
- `interact` (drop into full Python REPL in current scope; Ctrl+D to exit)

### Recipe A: Local Breakpoint
1. Insert `breakpoint()` directly before the target code.
2. Run code via terminal normally.
3. Clean up before committing: `rg -n 'breakpoint\(\)' --type py`.

### Recipe B: Debugging Pytest
Add `-p no:xdist` or `-n 0` when running tests so that `pdb` is not suppressed by parallel execution wrappers:
```bash
python -m pytest tests/test_file.py::test_name --pdb
```

### Recipe C: Remote Debug with `remote-pdb`
The cleanest terminal-agent friendly remote attachment tool:
```python
# In your python code:
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```
Connect to the process in another terminal shell:
```bash
nc 127.0.0.1 4444
```

---

## 2. Node.js Debugging (node inspect + CDP)

Interactive stepping and V8 inspector control from the terminal.

| Tool | When | Usage |
|---|---|---|
| **`node inspect`** | Built-in, zero install, CLI REPL. | `node inspect script.js` |
| **Chrome DevTools Protocol (CDP)** | Scriptable automation (e.g., `chrome-remote-interface`). | Control breakpoints programmatically via JS. |

### `node inspect` Quick Reference
The `debug>` prompt accepts:
- `c` (continue), `n` (next), `s` (step), `o` (out)
- `sb('file.js', 42)` (set breakpoint), `cb('file.js', 42)` (clear breakpoint)
- `bt` (backtrace), `list(5)` (show current line context)
- `repl` (drop into interactive scope-eval REPL; Ctrl+C to exit)
- `exec expr` (evaluate expression once)

### Recipe A: TSX / TypeScript Breakpoint on Entry
```bash
node --inspect-brk --import tsx script.ts
```
In another terminal, attach to inspect: `node inspect -p <node pid>` or `node inspect ws://127.0.0.1:9229/<uuid>`.

### Recipe B: Debugging Vitest Tests
Run a single test file paused on entry with file-parallelism disabled:
```bash
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

### Recipe C: Attaching to a Running Process
1. Enable the inspector on an active Node PID: `kill -SIGUSR1 <pid>`
2. Attach via: `node inspect -p <pid>`

---

## Guidelines & Best Practices

- **Never Commit Breakpoints:** Always check diffs and verify no leftover `breakpoint()`, `set_trace()`, or `debugger` statements exist before committing code.
- **Port Conflicts:** The default port for both `debugpy` and V8 inspector is `9229`. When debugging multiple processes in parallel, pass explicit ports (e.g. `--inspect=9230` or `port=4445`).
- **Interactive Mode:** When driving debuggers from Hermes Agent, ensure terminal calls are interactive (e.g. `pty=true` or run in foreground with precise inputs submitted).
