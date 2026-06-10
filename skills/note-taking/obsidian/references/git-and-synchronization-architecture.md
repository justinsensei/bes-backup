# Git and Synchronization Architecture

This reference document outlines the exact architecture, scripts, and behaviors of the file synchronization and backup daemons running on Justin's Hermes VM.

---

## 1. Obsidian Vault Synchronization (`bes-vault-sync`)

The Obsidian vault is configured as a fully bidirectional, real-time synced git repository.

- **Local Path:** `/home/justin.guest/vault`
- **Remote Repo:** `obsidian-vault` on GitHub
- **Watcher Script:** `/home/justin.guest/.local/bin/bes-vault-sync`
- **Daemon Service:** `bes-vault-sync.service` (systemd-user service)
- **Log Source:** `journalctl --user -u bes-vault-sync`

### Sync Mechanism
1. **Trigger:** `inotifywait` monitors the vault directory recursively (ignoring `.git/`, `.obsidian/workspace`, and temporary/trash directories).
2. **Debounce:** Accumulates filesystem events for **5 seconds** before initiating a sync loop to avoid commit storms.
3. **Rebase-first Sync:**
   - Runs `git pull --rebase --autostash` first to fetch changes pushed from Justin's Mac/devices, rebasing local changes on top.
   - If a merge conflict or network failure occurs during the pull phase, it aborts the rebase and sends a Telegram alarm to Justin.
4. **Auto-commit & Push:**
   - If files are modified locally, it auto-commits with the subject format `bes: <filename>` or `bes: N files changed` and pushes them to GitHub.

### Critical Pitfalls & Rules
- **Do NOT manually run git commands inside `/home/justin.guest/vault`:** The background daemon races with manual git operations and will cause spurious commits, locked trees, or rebase loops.
- **Merge Conflicts:** If the daemon alerts about a merge conflict, it pauses until resolved. Resolve it by SSHing into the VM, executing manual rebase fixes in `~/vault`, committing, and restarting the service:
  ```bash
  systemctl --user restart bes-vault-sync
  ```

---

## 2. Hermes Configuration Backup (`bes-autocommit` / `bes-backup`)

The Hermes configuration, custom skills, custom scripts, cron jobs, and memory stores are backed up into a dedicated Git repository.

- **Local Source Paths:** Subset of `/home/justin.guest/.hermes/`
  - *Tracked Files:* `SOUL.md`, `config.yaml`
  - *Tracked Folders:* `skills/`, `hooks/`, `cron/`, `memories/`, `scripts/`
- **Local Git Repository:** `/home/justin.guest/bes-backup`
- **Remote Repo:** `https://github.com/justinsensei/bes-backup.git`
- **Watcher Script:** `/home/justin.guest/.local/bin/bes-autocommit`
- **Daemon Service:** `bes-autocommit.service` (systemd-user service)
- **Log Source:** `journalctl --user -u bes-autocommit`

### Sync Mechanism
1. **Trigger:** `inotifywait` monitors the tracked subset of `~/.hermes/` recursively.
2. **Debounce:** Accumulates events for **5 seconds**.
3. **One-way Copy & Push (Unidirectional):**
   - Re-mirrors files using `cp -p` and directories using `rsync -a --delete` to propagate file removals cleanly into `~/bes-backup/`.
   - Forces the addition of custom/diverged user skills (overriding standard `.gitignore` rules) by comparing local hashes with the default bundled twins.
   - Commits with the subject `auto: <filename>` or `auto: N files changed` and pushes to GitHub.

### Critical Pitfalls & Rules
- **No Remote Pulling (Strictly Push-Only):** The `bes-autocommit` daemon **does NOT** pull or fetch changes from GitHub automatically. There is no git pull mechanism.
- **Editing Configs Elsewhere:** If you edit files inside the `bes-backup` remote repository elsewhere (e.g., via the GitHub UI, another clone, or on another machine) and push them, the local VM will **not** receive those updates automatically.
- **Handling Push Conflicts:** The next time a local modification triggers an autocommit, the `git push` on the VM will fail with a push conflict due to the remote being ahead. To recover, you must manually navigate to the backup repository on the VM and pull:
  ```bash
  cd ~/bes-backup
  git pull --rebase
  ```
- **Syncing Manual VM Changes:** If you manually update or create files under the tracked `~/.hermes` directories, the daemon will automatically detect, rsync, and push them within 5 seconds.
