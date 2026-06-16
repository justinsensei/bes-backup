---
name: github
description: "Master GitHub workflow skill: auth, repos, issues, PRs, and code review."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, Auth, Issues, Pull-Requests, Code-Review, Repository]
    related_skills: [codebase-inspection, requesting-code-review, test-driven-development]
---

# GitHub Master Workflows

This master skill governs all repository interactions, authentication setups, issue tracking, pull request lifecycles, and code review workflows. Each section is designed to use the GitHub CLI (`gh`) when available, falling back to pure `git` + `curl` API calls.

---

## 1. Authentication Setup

Use this section to configure authentication to allow full programmatic or command-line interaction with GitHub.

### Quick Verification & Detection

```bash
# Check what is installed and current state
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
```

### Method A: Git-Only HTTPS with Personal Access Token (PAT)
For environments without `gh` CLI or sudo access, configure `git` to cache personal access tokens:

1. **Generate Classic Token:** Go to **https://github.com/settings/tokens** and select `repo`, `workflow`, and `read:org` scopes.
2. **Store Credentials:**
```bash
# Configure credential helper to persist token on disk
git config --global credential.helper store

# Trigger a remote check to prompt for credential input
# Username: <GitHub Username>
# Password: <Paste the Personal Access Token, NOT password>
git ls-remote https://github.com/<username>/<repo>.git
```
3. **Embed Token in URL (Alternative):**
```bash
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

### Method B: GitHub CLI (gh) Login
If `gh` is installed, perform authentication via interactive login or token injection:
```bash
# Non-interactive login using token
echo "$GITHUB_TOKEN" | gh auth login --with-token
```

---

## 2. Repository Management

Create, clone, fork, configure, and manage GitHub repositories.

```bash
# 1. Cloning Shorthand
gh repo clone owner/repo-name ./local-dir

# 2. Creating a new repo and cloning it
gh repo create my-new-project --private --clone --description "An amazing utility" --license MIT

# 3. From an existing local directory
cd /path/to/project
git init
gh repo create my-org/my-new-project --private --source=. --remote=origin --push
```

### Fallback API equivalent (curl):
```bash
# Create private repository
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d '{"name":"my-new-project", "private":true, "description":"An amazing utility"}'
```

---

## 3. GitHub Issues

Create, search, triage, and manage GitHub issues.

### Viewing Issues
```bash
# gh CLI
gh issue list --state open --label "bug"
gh issue view 42

# curl API
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open" \
  | jq -r '.[] | "#\(.number) \(.title) [\(.labels[].name)]"'
```

### Creating & Managing Issues
```bash
# gh CLI
gh issue create --title "fix: database connection leak" --body "Leak found in connection pool." --label "bug"

# curl API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{"title":"fix: database connection leak", "body":"Leak found in pool.", "labels":["bug"]}'
```

---

## 4. Pull Request (PR) Lifecycle

From branching to automated merges.

### 1. Branch and Commits
```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/user-auth

# Commit changes using Conventional Commits
git commit -m "feat: add JWT user authentication"
git push -u origin HEAD
```

### 2. Creating the PR
```bash
# gh CLI
gh pr create --title "feat: add user auth" --body-file .github/PULL_REQUEST_TEMPLATE.md --draft

# curl API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d '{"title":"feat: add user auth", "body":"Adds JWT auth", "head":"feat/user-auth", "base":"main"}'
```

### 3. Monitoring CI and Merging
```bash
# Monitor CI checks
gh pr checks --watch

# Merge PR (Squash and Delete Branch)
gh pr merge --squash --delete-branch
```

---

## 5. Code Review Workflows

Review local changes before pushing or review open pull requests.

### Reviewing Local Changes (Pre-Push)
```bash
# Show insertions/deletions statistics per file
git diff main...HEAD --stat

# Look for left-over debugger calls, console logs, or TODOs
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|debugger"

# Check for accidental hardcoded secrets or credentials
git diff main...HEAD | grep -in "password\|secret\|api_key\|token"
```

### Reviewing Open PRs (PR Level)
```bash
# List reviews and view PR diff
gh pr diff 42

# Add single or inline comment review on a PR
gh pr comment 42 --body "LGTM! Ready to merge."
```
