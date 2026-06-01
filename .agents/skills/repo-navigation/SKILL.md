---
name: repo-navigation
description: Use BEFORE reading files when a mockCMMS task requires finding, understanding, or editing code. Maps task domains to their start-here files and defines intent-driven, token-efficient file targeting. Do not scan the repo or read files speculatively.
---

# Repo Navigation — Token-Efficient File Targeting

## Use this skill when

- You need to locate the right file(s) for a task without scanning the whole repo
- You are about to read code and want to target only what is relevant
- Many files (or the full repo) are in context and you must navigate with intent

## Do not use this skill when

- You already know the exact file and just need to open it
- You need shell syntax — see Skill: `shell-compatibility`
- You are about to edit — also run Skill: `file-locking` first

---

## Principle: navigate with intent

Open a file only when you can state why. Before reading anything, classify it:

| The file is…                    | Action                                           |
| ------------------------------- | ------------------------------------------------ |
| Already in context this session | Do not re-read — reuse what you already have     |
| Directly required by the task   | Read the relevant range                          |
| Only possibly relevant          | Search it first, then read just the matched part |
| Unrelated to the task           | Skip                                             |

Never read files to "get a feel" for the repo.

---

## Step 1 — Map the task to its start-here files

| Task domain                       | Start here first                                                           |
| --------------------------------- | -------------------------------------------------------------------------- |
| CI/CD, releases, GitHub Actions   | `.github/workflows/`, `.github/CONTRIBUTING.md`, `.github/GIT_WORKFLOW.md` |
| Python lint / format / validation | `pyproject.toml`, `scripts/format_code.py`, `scripts/validate_code.py`     |
| Flask routes / API endpoints      | `src/routes/api.py`, `src/routes/main.py`                                  |
| Business logic / database         | `src/services/db_utils.py`, `src/services/db_seeding.py`                   |
| Flask app config / startup        | `src/app.py`, `src/config/`, `run.py`                                      |
| Frontend JS behaviour             | `src/static/js/` — search for the function                                 |
| Frontend CSS / layout             | `src/static/css/` — search for the selector                                |
| Jinja2 templates / HTML           | `src/templates/` — search for the template                                 |
| Backend test failures             | `tests/backend/<category>/` — match category to test type                  |
| Frontend test failures            | `tests/frontend/unit/` or `tests/frontend/e2e/`                            |
| Coverage gaps                     | Run `pytest --cov-report=term-missing` for exact uncovered lines           |
| Planning app                      | `apps/planning/`                                                           |
| Reporting app                     | `apps/reporting/`                                                          |
| Project docs / roadmap            | `docs/mockCMMS_roadmap.md`                                                 |
| Bug tracking                      | `docs/bug_tracking.md` or the app-specific tracker                         |
| Dependency / package issues       | `requirements.txt`, `requirements-dev.txt`, `package.json`                 |
| Pre-commit / git hook issues      | `.pre-commit-config.yaml`, `scripts/hooks/`                                |
| Environment / feature flags       | `.env`, `.env.example`                                                     |
| File locking / collab runtime     | Skill: `file-locking`, `scripts/hooks/`                                    |
| Portable distribution build       | `scripts/build_portable.py`                                                |

For tooling/config questions, confirm the tool's actual behaviour against its official documentation first (see `AGENTS.md` → "Root-Cause Resolution").

---

## Step 2 — Search with the right tool, then open

Use the agent's search tools rather than shell text utilities (raw shell scanning conflicts with Skill: `shell-compatibility`):

| Goal                                   | Tool             |
| -------------------------------------- | ---------------- |
| Find by meaning ("how does X work?")   | `SemanticSearch` |
| Find an exact symbol, string, or route | `Grep`           |
| Find files by name or glob pattern     | `Glob`           |
| Read a known file (optionally a range) | `Read`           |

Open only the files a search confirms are relevant.

---

## Step 3 — Read sections, not whole files

For large files, read the matched range instead of the entire file: `Grep` for the symbol, then `Read` around the reported line. Files that are usually large — target a section: `src/routes/api.py`, `src/static/js/*.js`, big test modules, and `AGENTS.md`.

---

## Step 4 — Avoid re-reads

Track what you have already read this session. Reuse content already in context instead of re-fetching it.

---

## Anti-patterns (never do these)

| Anti-pattern                                            | Why it wastes effort                   |
| ------------------------------------------------------- | -------------------------------------- |
| Reading a whole file when only a few lines are relevant | Loads irrelevant content               |
| Opening a file outside the task's domain                | Unrelated to the task (see Step 1 map) |
| Opening every file in a directory "to understand it"    | Use `Glob` + `Grep` to target instead  |
| Re-reading a file already read this session             | Content is already in context          |
| Reading `AGENTS.md` on every subtask                    | Read it once per session at the start  |

_Updated June 1, 2026_
