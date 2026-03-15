---
name: commit-workflow
description: Use when staging, reviewing, and committing changes. Covers the full git commit and push workflow.
---

# Commit Workflow

## Use this skill when

- You have completed a task and are ready to commit
- You need to stage, review, and commit changes
- You need to push a branch (new or existing)

## Do not use this skill when

- You're still writing code or running tests
- You need general git knowledge (see `.github/GIT_WORKFLOW.md`)

---

## Step 1: Pre-Commit Validation

**MANDATORY** — never commit without passing validation.

```bash
python scripts/format_code.py      # Auto-fix formatting
python scripts/validate_code.py    # Full lint + test + coverage
```

Both must pass before proceeding.

## Step 2: Review All Changed Files

```bash
git status                         # See all modified files
git diff --stat                    # Summary of changes
```

For each modified file, review actual changes:

```bash
git diff path/to/file.ext         # View detailed changes
```

Identify: are changes related to the current task, or unrelated?

## Step 3: Stage Relevant Files

```bash
git add path/to/file1.ext path/to/file2.ext
```

Rules:
- **DO NOT** stage unrelated changes — commit them separately
- Use `git add -p` for partial staging if a file has mixed changes
- **DO NOT** stage debug code, `console.log`, or temporary changes

## Step 4: Capture Staged Diff (MANDATORY for AI)

```bash
git diff --cached > temp_diff_output.txt
```

Read `temp_diff_output.txt` to understand ALL staged changes. Use this to write an accurate commit message.

## Step 5: Verify Staged Changes

```bash
git diff --cached --stat              # Summary
git diff --cached path/to/file.ext    # Specific file
```

Confirm: only intended changes are staged.

## Step 6: Write Commit Message

Check recent commits for style:

```bash
git log -n 5 --oneline
```

**Format:** Conventional Commits

```
type(scope): short description (50-72 chars)

Detailed explanation of WHAT changed and WHY.

Files changed:
- path/to/file1.ext (description of change)
- path/to/file2.ext (description of change)

Technical Details:
- Implementation approach
- Patterns used

Testing:
- How changes were verified
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `ci`
**Scopes:** `ui`, `api`, `db`, `planning`, `reporting`, `auth`, `config`

## Step 7: Commit

```bash
git commit -m "type(scope): description

Body text here..."
```

**NOTE:** `git commit` requires user approval — do NOT set `SafeToAutoRun=true`.

## Step 8: Clean Up

```bash
del temp_diff_output.txt
```

## Step 9: Push

Check if your branch is tracked:

```bash
git branch -vv
```

| Branch Status | Action | Command |
|---|---|---|
| **Untracked** (no `[origin/...]`) | Create PR & Push | `gh pr create --base main --head <branch> --fill` |
| **Tracked** (has `[origin/...]`) | Push Updates | `git push` |

**⚠️ NEVER** use `git push -u origin <branch>` for new branches — it creates orphan branches with no PR.

**NOTE:** `git push` requires user approval — do NOT set `SafeToAutoRun=true`.

## Pre-Commit Checklist

- [ ] `format_code.py` passed
- [ ] `validate_code.py` passed
- [ ] All related files staged
- [ ] No unrelated changes staged
- [ ] No debug/temporary code included
- [ ] Commit message follows conventional format
- [ ] Documentation updated if applicable

## Safety

- **NEVER** use `git checkout` or `git restore` — uncommitted work will be lost.
- Only `git commit` and `git push` require user approval. Everything else auto-runs.

---

## Release Automation: Commit Message Requirements

To trigger the release automation (auto_release_hook and release_manager), your commit message **must**:
- Follow the Conventional Commits standard (e.g., `feat(core): add feature ...`).
- Include a `[release:patch]`, `[release:minor]`, or `[release:major]` tag.
- If the commit message does **not** include a `[release:...]` tag, the release will **not** run.
- Always use the commit template or follow the Conventional Commits standard for release automation.
- If the release commit fails due to hooks, fix the issues and re-commit.

**Examples:**
- `git commit -m "fix: bug fix [release:patch]"`        # 1.0.0 → 1.0.1
- `git commit -m "feat: new feature [release:minor]"`   # 1.0.0 → 1.1.0
- `git commit -m "feat!: breaking [release:major]"`     # 1.0.0 → 2.0.0
- `git commit -m "chore: updates [release]"`            # Defaults to patch

The `auto_release_hook.py` pre-push hook detects `[release]` and runs `release_manager.py` automatically.

> **Note:** Always check commit messages for the correct format before pushing. This is required for the release workflow to function.

# Supported Commit Types (Conventional Commits)

The following commit types are supported and recognized by release automation and changelog generation:

- feat
- fix
- chore
- refactor
- perf
- remove
- revert
- docs
- test
- style
- build
- ci

**Use only these types in your commit messages for release automation.**
