---
name: new-feature
description: Use when scaffolding a new feature, adding a new modular app, or implementing a significant new capability.
---

# New Feature Workflow

## Use this skill when

- Adding a new feature to the core CMMS (`src/`)
- Creating a new modular app in `apps/`
- Implementing a significant new capability that spans multiple files

## Do not use this skill when

- Fixing a bug (see Skill: `bug-tracking`)
- Refactoring existing code without adding new functionality
- Making small, isolated changes to a single file

---

## Step 1: Plan Before Coding

1. **Analyze** — state your understanding of the requirement.
2. **Plan** — outline the step-by-step approach (files to create/modify).
3. **Check constraints** — review AGENTS.md boundaries (immutable config, import rules, etc.).
4. **Create a feature branch** — `git checkout -b feat/feature-name`.

## Step 2: Write Tests First

Before implementing:

1. Search for existing tests: `findstr /S "def test_" tests\backend\*.py`
2. Run existing tests to establish baseline: `pytest tests/backend -q`
3. Write test stubs for the new functionality.
4. Tests should fail initially (red-green-refactor).

See Skill: `testing-workflow` for test placement and patterns.

## Step 3: Implement the Feature

### Core Feature (in `src/`)

| Component | Location |
|---|---|
| Routes (API) | `src/routes/api.py` |
| Routes (web) | `src/routes/main.py` |
| Business logic | `src/services/` |
| Templates | `src/templates/` |
| Static assets | `src/static/css/`, `src/static/js/` |
| Configuration | `src/config/` |

### New Modular App (in `apps/`)

```
apps/<app_name>/
├── src/
│   ├── __init__.py
│   ├── app.py              # Flask factory
│   ├── routes/
│   │   └── <app_name>.py   # Blueprint
│   ├── services/           # Business logic
│   ├── templates/
│   └── static/
│       ├── css/
│       └── js/
├── docs/
│   ├── <app_name>_roadmap.md
│   └── <app_name>_bug_tracking.md
├── tests/
├── config/
├── instance/
├── setup.py
└── README.md
```

**Critical rules for new apps:**
- Add toggle to `.env.example`: `<APP_NAME>_ENABLED=False`
- Register blueprint conditionally in `src/app.py` (check env var)
- **NEVER** import `apps/*` at module level in `src/` — use conditional imports inside functions
- Add app tests to `apps/<app_name>/tests/`
- Update `docs/mockCMMS_roadmap.md` with a link to the app roadmap

### Separation of Concerns

- JavaScript → `.js` files only (no inline `<script>` or `onclick=""`)
- CSS → `.css` files only (no `style="..."`)
- HTML → `.html` templates only
- Use event listeners in JS, not inline handlers

## Step 4: Validate

```bash
python scripts/format_code.py      # Auto-fix formatting
python scripts/validate_code.py    # Full lint + test + coverage
```

Ensure coverage threshold is met with the new code.

## Step 5: Document

1. Update relevant roadmap (`docs/mockCMMS_roadmap.md` or `apps/<name>/docs/`)
2. Add/update docstrings for all public functions and classes
3. Create testing guide in `docs/` if the feature affects UI

## Step 6: Commit

Follow Skill: `commit-workflow`.

## Safety

- Always check if the feature touches protected files (see "Key Boundaries" in AGENTS.md).
- New code must include tests — coverage must not drop.
- CSRF tokens required on all new forms.
- No hardcoded values — use `.env` for configuration.
