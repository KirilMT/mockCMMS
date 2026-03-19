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

## Step 1: Pre-Commit Formatting & Validation

**MANDATORY** — never commit without formatting and passing validation.

**Format first, validate second:**

```bash
python scripts/format_code.py      # Format ALL code (must be the LAST edit before commit)
python scripts/validate_code.py    # Full repo scan (lint + test + coverage)
```

> ⚠️ **CRITICAL RULE:** `format_code.py` must be the **very last thing** you run before `git add` and `git commit`. If you edit ANY file after formatting, you MUST re-run `format_code.py` before committing. The pre-commit hook will catch unformatted code and reject the commit.

**What the pre-commit hook does automatically:**

- Runs `validate_code.py --quick` on only your **staged** files (with `require_serial: true` for clean output).
- Ensures your specific changes pass lint/test even if other stashed files are messy.

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

**Types:** `feat`, `fix`, `chore`, `refactor`, `perf`, `remove`, `revert`, `docs`, `test`, `style`, `build`, `ci`
**Scopes:** `ui`, `api`, `db`, `planning`, `reporting`, `auth`, `config`

## Step 7: Commit

```bash
git commit -m "type(scope): description

Body text here..."
```

**NOTE:** `git commit` requires user approval — do NOT set `SafeToAutoRun=true`.

**Commit-msg hook enforcement:** The `.git/hooks/commit-msg` hook will reject commits that don't follow Conventional Commits format. All commits must start with `type(scope): description`.

## Step 8: Clean Up

```bash
del temp_diff_output.txt
```

## Step 9: Push

Check if your branch is tracked:

```bash
git branch -vv
```

| Branch Status                     | Action           | Command                                           |
| --------------------------------- | ---------------- | ------------------------------------------------- |
| **Untracked** (no `[origin/...]`) | Create PR & Push | `gh pr create --base main --head <branch> --fill` |
| **Tracked** (has `[origin/...]`)  | Push Updates     | `git push`                                        |

**⚠️ NEVER** use `git push -u origin <branch>` for new branches — it creates orphan branches with no PR.

**NOTE:** `git push` requires user approval — do NOT set `SafeToAutoRun=true`.

## Pre-Commit Checklist

- [ ] All code changes are complete — no more edits after this point
- [ ] `format_code.py` passed (run LAST, after all edits)
- [ ] `validate_code.py` passed
- [ ] All related files staged
- [ ] No unrelated changes staged
- [ ] No debug/temporary code included
- [ ] Commit message follows Conventional Commits: `type(scope): description`
- [ ] Documentation updated if applicable

## Safety

- **NEVER** use `git checkout` or `git restore` — uncommitted work will be lost.
- Only `git commit` and `git push` require user approval. Everything else auto-runs.

---

## Release Process (Do Not Trigger)

Releases are handled automatically by Google Release Please via the CI/CD pipeline (`release.yml`). AI agents should **never** trigger releases manually, update `CHANGELOG.md`, or modify version tags. Release Please generates all changelogs and version bumps automatically based on Conventional Commit types (`feat` → minor, `fix` → patch).

## Commit-Msg Hook

The `.git/hooks/commit-msg` hook enforces Conventional Commits format. It accepts all standard types: `feat`, `fix`, `chore`, `refactor`, `perf`, `remove`, `revert`, `docs`, `test`, `style`, `build`, `ci`.

## Supported Commit Types (Conventional Commits)

The following commit types are supported and recognized by changelog generation:

- feat, fix, chore, refactor, perf, remove, revert, docs, test, style, build, ci

**Use only these types in your commit messages.**
