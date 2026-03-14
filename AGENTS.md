# AGENTS.md — mockCMMS

> Single source of truth for all AI coding assistants (Antigravity, Gemini CLI, Claude Code, GitHub Copilot, Jules).
> Tool-specific overrides live in `GEMINI.md`, `CLAUDE.md`, `.github/copilot-instructions.md`.
> Workflow-heavy procedures live in `.agents/skills/`.

---

## Project Overview

mockCMMS is a **Computerized Maintenance Management System** — a Flask web app for tracking maintenance orders, assets, and users. It uses a modular monorepo architecture: core CMMS in `src/`, optional apps in `apps/`.

**Login:** `admin` / `admin123` (source: `test_data/dummy_data.json`)

---

## Stack

| Layer             | Technology                                     | Version            |
| ----------------- | ---------------------------------------------- | ------------------ |
| Language          | Python                                         | 3.12 (target ≥3.9) |
| Framework         | Flask, SQLAlchemy, Jinja2                      | —                  |
| Frontend          | Vanilla JS (ES6+), CSS3                        | —                  |
| Database          | SQLite (dev), PostgreSQL (prod-ready)          | —                  |
| Python Linting    | Ruff, Flake8, Mypy, Pylint                     | —                  |
| Python Formatting | isort → Black → docformatter (strict order)    | —                  |
| JS Linting        | ESLint 9                                       | —                  |
| JS/CSS Formatting | Prettier, Stylelint                            | —                  |
| Backend Tests     | Pytest (coverage ≥85%)                         | —                  |
| Frontend Tests    | Jest 30 (coverage ≥80%), Playwright (E2E)      | —                  |
| Package Managers  | pip (`requirements.txt`), npm (`package.json`) | —                  |

---

## Repository Structure

```
mockCMMS/
├── src/                        # Core CMMS application
│   ├── app.py                  # Flask factory (entry point for config)
│   ├── routes/                 # API (api.py) and web routes (main.py)
│   ├── services/               # Business logic (db_utils.py, seed.py)
│   ├── static/                 # CSS, JS, images
│   ├── templates/              # Jinja2 templates
│   └── config/                 # App configuration
├── apps/                       # Modular extensions (each is a Flask blueprint)
│   ├── planning/               # Skill-based technician task assignment
│   └── reporting/              # Report generation (PDF, Markdown)
├── tests/
│   ├── backend/                # Pytest: unit/, functional/, integration/,
│   │                           #         security/, performance/, reliability/
│   └── frontend/               # Jest unit tests + Playwright E2E
├── scripts/                    # Automation (see Key Scripts below)
├── docs/                       # Project documentation
├── test_data/                  # Fixtures, dummy_data.json
├── run.py                      # Application entry point
├── pyproject.toml              # Python tooling config (pytest, ruff, black, mypy)
├── package.json                # JS tooling config (jest, eslint, prettier)
├── .env                        # Environment config (PLANNING_ENABLED, REPORTING_ENABLED)
└── .pre-commit-config.yaml     # Pre-commit hooks
```

---

## Setup

```powershell
# Production dependencies + venv
.\scripts\setup.ps1

# Dev dependencies (testing, linting)
.\scripts\setup-dev.ps1

# Start the server
python run.py
```

**Modular apps** — toggle in `.env`:

```dotenv
PLANNING_ENABLED=True    # apps/planning
REPORTING_ENABLED=True   # apps/reporting
```

---

## Key Scripts

| Script                             | Purpose                                                        | Usage                                                  |
| ---------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------ |
| `scripts/format_code.py`           | Auto-fix all formatting (isort, black, docformatter, prettier) | `python scripts/format_code.py`                        |
| `scripts/validate_code.py`         | Full CI simulation (lint, test, coverage)                      | `python scripts/validate_code.py`                      |
| `scripts/validate_code.py --quick` | Fast mode: honors `.env`, skips slow tests                     | `python scripts/validate_code.py --quick`              |
| `scripts/generate_tests.py`        | Generate test stubs for new modules                            | `python scripts/generate_tests.py src/services/foo.py` |
| `scripts/release_manager.py`       | Semantic version bump + changelog                              | `python scripts/release_manager.py minor`              |

---

## Testing

### Commands

```bash
# Backend
pytest tests/backend                           # Run all backend tests
pytest --cov=src --cov=apps tests/backend      # With coverage

# Frontend
npm test                                        # Jest unit tests
npm run test:coverage                           # Jest with coverage
npm run test:e2e                                # Playwright E2E

# Full validation (recommended before commit)
python scripts/format_code.py                   # Step 1: auto-fix formatting
python scripts/validate_code.py                 # Step 2: lint + test + coverage
```

### Coverage Thresholds (IMMUTABLE)

- **Backend (pytest):** ≥85% (`pyproject.toml` → `--cov-fail-under=85`)
- **Frontend (jest):** ≥80% branches, functions, lines, statements (`package.json`)
- 80% is the **floor**. If coverage drops even to 79.9%, it is a failure.
- Fix by adding tests, not by lowering thresholds.

### Test Organization

Tests live in `tests/backend/` organized by category: `unit/`, `functional/`, `integration/`, `security/`, `performance/`, `reliability/`. See `tests/README.md`.

### Test-Driven Development

1. Write/update tests **before** implementing code.
2. Run tests before AND after changes.
3. If a test fails after a code change: fix the **code** (tests define correct behavior), unless requirements genuinely changed.
4. Search for existing tests before creating new ones to avoid duplicates.

---

## Code Conventions

### Architecture

- **NEVER import `apps/*` at module level in `src/`.** Use conditional imports inside functions to avoid `UnboundExecutionError`.
- Separation of concerns: JS in `.js`, CSS in `.css`, HTML in `.html`. No inline styles, scripts, or event handlers.
- SOLID, DRY, KISS. No over-engineering.
- Comments explain **why**, not what. Never reference bug/issue numbers in comments.
- All public functions/classes must have docstrings.
- No hardcoded secrets — use `.env`.

### Formatting (STRICT ORDER for Python)

1. `isort` — sort imports
2. `black` — format code
3. `docformatter` — format docstrings

Or just run: `python scripts/format_code.py`

### Error Handling

- No silent failures. Catch, log, and handle errors.
- CSRF tokens required on all forms — check templates before modifying.

---

## Key Boundaries (DO NOT TOUCH)

| Item                                                                                                    | Rule                                                                                                                       |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `tests/frontend/e2e/__screenshots__/`                                                                   | **SACRED.** Never update unless you intentionally modified UI/CSS. Failing visual tests = bug in code, not in screenshots. |
| `pyproject.toml`, `jest.config.js`, `playwright.config.js`, `pytest.ini`, `.flake8`, `eslint.config.js` | **IMMUTABLE.** Never modify to make tests pass. Fix the code, not the config.                                              |
| `.github/workflows/`                                                                                    | **IMMUTABLE.** Never modify CI to skip failing checks.                                                                     |
| `docs/bug_tracking.md`                                                                                  | **ASK user** before adding bugs. Never add without confirmation.                                                           |
| `test_data/dummy_data.json`                                                                             | Seed data source. Do not remove or restructure without approval.                                                           |

---

## Documentation Structure (Modular)

- **Core docs:** `docs/mockCMMS_roadmap.md`, `docs/bug_tracking.md`
- **App docs:** `apps/<name>/docs/<name>_roadmap.md`, `apps/<name>/docs/<name>_bug_tracking.md`
- Core docs link to app docs — never duplicate content.
- Documentation must be clean, current, and concise. Remove outdated content.

### Living Document Rules

- Mark items as `[x]` when complete — never delete historical entries.
- Before adding new items, search to avoid duplicates.
- Update timestamps and status fields when progress changes.
- Synchronize related docs (e.g., roadmap ↔ bug tracker) when phases complete.

---

## Git & Commit Standards

- **Conventional Commits:** `type(scope): description` (e.g., `fix(ui): resolve overflow in MO modal`)
- **Feature branches:** Never commit to `main`. Use `type/feature-name`.
- **New branches:** Always use `gh pr create` to push. NEVER `git push -u`.
- **Tracked branches:** Use `git push` normally.
- **Pre-commit hooks** are enabled: isort, black, docformatter, ruff, prettier.

> For the full commit workflow procedure, see **Skill: `commit-workflow`**.

---

## Agent Behavior Rules

### Autonomy

- Operate autonomously until the final `git commit`. The user should be able to leave for 20+ minutes and return to completed work.
- `SafeToAutoRun=true` for ALL standard operations: python, pytest, npm, ruff, black, isort, mypy, prettier, eslint, PowerShell.
- Only `git commit` and `git push` require user approval.
- Never pause for "Should I proceed?" during lint/format/test loops.

### Decision Making

- Verify things yourself before asking the user.
- Ask only when genuinely blocked: missing requirements, design decisions, user preferences.
- If validation fails, self-correct up to 3 attempts before reporting to the user.
- **When unsure what to do next:** Run tests first. If tests pass, audit code quality. If quality is good, look at the roadmap for the next task.

### Task Completion

- Complete the **full scope**. If asked for A, B, and C — do all three.
- No partial submissions unless fully blocked.
- Always run `python scripts/format_code.py` then `python scripts/validate_code.py` before finishing any significant task.

### File Safety

- **NEVER** use `git checkout` or `git restore` to fix corrupted files — uncommitted work will be lost.
- Make small, targeted edits. For large files (>1000 lines), split into modules first.
- Never create temporary files in the project directory — use artifacts or `/tmp/`.

### Version Management

Use `python scripts/release_manager.py <patch|minor|major>` after significant changes.

**Automated release via commit message** — include `[release:TYPE]` in your commit:

```bash
git commit -m "feat: new feature [release:minor]"   # 1.0.0 → 1.1.0
git commit -m "fix: bug fix [release:patch]"         # 1.0.0 → 1.0.1
git commit -m "feat!: breaking [release:major]"      # 1.0.0 → 2.0.0
git commit -m "chore: updates [release]"             # Defaults to patch
```

The `auto_release_hook.py` pre-push hook detects `[release]` and runs `release_manager.py` automatically.

See `.github/CONTRIBUTING.md` and `.github/GIT_WORKFLOW.md` for full details.

---

## Key References

| Document                   | Purpose                                               |
| -------------------------- | ----------------------------------------------------- |
| `.github/CONTRIBUTING.md`  | Contribution process, commit conventions, PR workflow |
| `.github/GIT_WORKFLOW.md`  | Branching strategy, push vs PR rules                  |
| `tests/README.md`          | Test suite organization and strategy                  |
| `docs/mockCMMS_roadmap.md` | Project status and active sprints                     |

---

## Skills (Workflow Procedures)

Complex, multi-step workflows are documented as Skills in `.agents/skills/`:

| Skill              | Trigger                                               |
| ------------------ | ----------------------------------------------------- |
| `testing-workflow` | Writing tests, debugging coverage, running validation |
| `commit-workflow`  | Staging, reviewing, and committing changes            |
| `bug-tracking`     | Discovering, reporting, and fixing bugs               |
| `new-feature`      | Scaffolding a new feature or modular app              |

> **To use a Skill:** Read `.agents/skills/<name>/SKILL.md` before starting the workflow.
