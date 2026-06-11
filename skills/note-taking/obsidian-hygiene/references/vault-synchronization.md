# Bes Vault Synchronization & Troubleshooting

This document outlines the mechanics and troubleshooting steps for the real-time background sync daemon that keeps Justin's Obsidian vault in sync across machines.

---

## Architecture & Mechanics

### Daemon Name & Service
- **Service Name:** `bes-vault-sync.service` (systemd user unit)
- **Path to Executable:** `/home/justin.guest/.local/bin/bes-vault-sync`
- **Service Definition:** `/home/justin.guest/.config/systemd/user/bes-vault-sync.service`

### How it Works
1. **FSEvents Watcher:** Uses `inotifywait` to watch `/home/justin.guest/vault` recursively for file modifications, creations, deletions, and moves.
2. **Debounce:** Collects file events over a short window (default: 5 seconds) before triggering a single, batch synchronization.
3. **Pull-Rebase-Commit-Push Lifecycle:**
   - Runs `git pull --rebase --autostash origin main` to fetch the latest changes from GitHub and rebase any local agent commits on top of edits Justin pushed from other machines (e.g. Mac).
   - Stages all changes (`git add -A`).
   - If there are changes, commits them with a standardized message (e.g., `bes: 34 files changed` or `bes: Notes/Contacts/Andrew Lawrence.md`).
   - Pushes to the remote repository (`git push origin main`).
4. **Alarms:** If a merge conflict or push failure occurs, parses the error output and sends an alert directly to Justin's Telegram home channel.

---

## Common Failures & Troubleshooting

### 1. Error: "fatal: Cannot rebase onto multiple branches"
- **Symptom:** The daemon logs or outputs `git pull failed` with the error `Cannot rebase onto multiple branches.` during filesystem events.
- **Cause:** This happens when Git is called with a bare `git pull --rebase --autostash` but can't determine the correct upstream target due to multiple tracking/remote-tracking branches or global/system-level pull rebase configurations.
- **Resolution:** Explicitly specify the upstream repository and target branch in the pull command:
  ```bash
  git pull --rebase --autostash origin main
  ```
  This bypasses any ambiguous configuration or multiple matching tracking branches.

### 2. General Git Lock Failures
- **Symptom:** Commit or push fails because another process holds the git lock.
- **Resolution:** The daemon uses an flock file at `~/.local/state/bes-vault-sync/git.lock` to coordinate. If locked up, check for lingering git or sync processes:
  ```bash
  ps aux | grep git
  ```
  Or restart the systemd service:
  ```bash
  systemctl --user restart bes-vault-sync
  ```
