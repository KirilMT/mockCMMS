# Troubleshooting App — Concept & Modular Architecture

_Updated March 12, 2026_

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**This document defines the architectural foundation for the Troubleshooting app. Treat it as a
design specification, not a task list.**

- **Do NOT modify design decisions** without discussing them first — they have dependencies
- **Update the "Domain Model" section** if the schema changes during Phase 0 review
- **Keep integration patterns in sync** with `src/app.py` as the core app evolves
- **Update "Last Updated" date** at the top when making any changes

> [!NOTE]
> For the phased implementation plan, see
> [`troubleshooting_roadmap.md`](troubleshooting_roadmap.md). This document focuses on
> **what** is being built and **how** it integrates — the roadmap tracks **when** and **who**.

---

## 🎯 Objective

Translate the concept from the standalone `Troubleshooting-Wizard` desktop application into a
fully modular Flask app that lives inside the mockCMMS monorepo — accessible to technicians
through the same web interface, protected by the same authentication, and controlled by the
same environment toggle pattern used by the `planning` and `reporting` modules.

---

## 📖 Source Concept: Troubleshooting-Wizard

The `Troubleshooting-Wizard` is a standalone Python/tkinter desktop tool for industrial equipment
diagnosis. Its core interaction model is:

> **Select technology → Choose task → Search error code → Get resolution steps**

### Features Being Adapted for mockCMMS

| Troubleshooting-Wizard Feature        | mockCMMS Adaptation                                      | In MVP? |
| :------------------------------------ | :------------------------------------------------------- | :-----: |
| Technology selection screen           | Web card/grid UI for selecting equipment families        | ✅ Yes  |
| Error code search (PDF lookup)        | Database-backed search with severity and structured data | ✅ Yes  |
| Step-by-step resolution guidance      | Ordered steps displayed in error code detail view        | ✅ Yes  |
| Manual/document access per technology | Resource links list (URLs + local references)            | ✅ Yes  |
| Config-driven technology definitions  | DB-managed technologies with admin CRUD interface        |  🔜 V2  |
| PDF processing tool (import pipeline) | Admin import from PDF to populate error code database    |  🔜 V2  |
| SEW Drive System DB error codes       | Seed data for SEW technology with full error code set    | ✅ Yes  |
| WTC Controller error code screenshots | Seed data for WTC technology with resource links         | ✅ Yes  |
| Standalone desktop GUI (tkinter)      | Not adapted — replaced by web interface                  | ❌ N/A  |

> [!IMPORTANT]
> The desktop GUI is **not** being ported. The value being extracted is the **data structure**
> and **interaction model**, not the UI code. The web interface will be built from scratch using
> the mockCMMS HTML/CSS/JS conventions (vanilla JS, no frameworks).

---

## 🏗️ Proposed App Structure

The module follows the same conventions as `apps/planning` and `apps/reporting`. Every
directory has a specific responsibility and must not be mixed.

```text
apps/troubleshooting/
├── src/                              # All application source code
│   ├── app.py                        # ⭐ Flask app factory (create_app)
│   ├── config.py                     # Configuration classes (Dev, Prod, Test)
│   ├── extensions.py                 # Flask extensions init (SQLAlchemy, etc.)
│   ├── routes/
│   │   └── troubleshooting.py        # ⭐ Blueprint — all routes defined here
│   ├── services/
│   │   ├── troubleshooting_service.py  # High-level orchestration logic
│   │   ├── error_code_service.py       # Error code search and lookup
│   │   ├── knowledge_repository.py     # Resource/manual access layer
│   │   └── db_seeding.py               # Idempotent seed data population
│   ├── models/
│   │   └── troubleshooting_models.py   # SQLAlchemy model definitions
│   ├── templates/
│   │   └── troubleshooting/
│   │       ├── index.html              # Technology selector page
│   │       ├── technology_hub.html     # Per-technology landing page
│   │       ├── error_search.html       # Error code search + results
│   │       ├── error_detail.html       # Error code detail + steps
│   │       └── resources.html          # Knowledge & resource links
│   └── static/
│       ├── css/
│       │   └── troubleshooting.css     # App-specific styles only
│       └── js/
│           └── troubleshooting.js      # App-specific JS (vanilla ES6+)
├── config/
│   └── config.example.json           # Template for local config (committed)
├── docs/
│   ├── troubleshooting_roadmap.md    # ⭐ Canonical app roadmap (copy from docs/)
│   ├── troubleshooting_bug_tracking.md  # App-level bug tracker
│   └── roadmap/                      # Detailed phase documents (created during impl.)
│       ├── 01_PHASE_0_DISCOVERY.md
│       ├── 02_PHASE_1_SCAFFOLDING.md
│       ├── 03_PHASE_2_MVP_FEATURES.md
│       ├── 04_PHASE_3_DATA_MANAGEMENT.md
│       └── 05_PHASE_4_HARDENING.md
├── instance/
│   └── troubleshooting.db            # SQLite database (dev — gitignored)
├── tests/
│   ├── unit/                         # Isolated service/model tests
│   ├── functional/                   # Route-level HTTP tests
│   └── integration/                  # App registration + end-to-end flows
├── setup.py                          # Package configuration
├── requirements.txt                  # App-local Python dependencies
└── README.md                         # App-level documentation
```

> [!NOTE]
> The `instance/` directory is gitignored. The app must create it at startup if it does not
> exist (SQLite), following the same pattern used in `apps/planning/instance/`.

---

## 🔗 Monorepo Integration Rules

These rules are **non-negotiable**. Deviating from them has caused bugs in the past
(e.g., `UnboundExecutionError` when a disabled module was imported at module level).

### Rule 1 — Environment Toggle

Add a `TROUBLESHOOTING_ENABLED` flag to both `.env.example` and `.env`. The flag follows the
exact same pattern as `PLANNING_ENABLED` and `REPORTING_ENABLED`:

```dotenv
# .env.example — add under "# MODULAR PACKAGES CONFIGURATION"

# Enable/disable the Troubleshooting module.
# Values: True/False
# If False, the /troubleshooting blueprint will not be registered.
TROUBLESHOOTING_ENABLED=False
```

### Rule 2 — Conditional Registration in `src/app.py`

The import and registration **must** happen inside a function — never at module level. The
existing pattern from `src/app.py` shows exactly how this is done:

```python
# src/app.py — inside create_app(), following the planning/reporting pattern

def is_troubleshooting_enabled(default="false"):
    """Return Troubleshooting app toggle value."""
    return get_env_bool("TROUBLESHOOTING_ENABLED", default)

# Inside create_app():
troubleshooting_enabled = is_troubleshooting_enabled()
if troubleshooting_enabled:
    # C0415 acceptable here — conditional import by design
    from apps.troubleshooting.src.routes.troubleshooting import troubleshooting_bp
    app.register_blueprint(troubleshooting_bp)
```

> [!IMPORTANT]
> The comment `# C0415 acceptable here` is already used in `src/app.py` for existing modules.
> It suppresses the pylint warning for non-top-level imports. Use the same convention.

### Rule 3 — Database Bind

The app must use its own SQLAlchemy `BIND_KEY` (`"troubleshooting"`) so it has an isolated
database, exactly like planning uses `"planning"`. Add the bind in `src/app.py`:

```python
# Inside create_app(), inside the binds configuration block
if troubleshooting_enabled or app.testing:
    if "troubleshooting" not in binds:
        if app.testing and not is_e2e:
            binds["troubleshooting"] = "sqlite:///:memory:"
        else:
            ts_instance_dir = os.path.join(
                app.root_path, "..", "apps", "troubleshooting", "instance"
            )
            os.makedirs(ts_instance_dir, exist_ok=True)
            binds["troubleshooting"] = (
                f"sqlite:///{os.path.join(ts_instance_dir, 'troubleshooting.db')}"
            )
```

### Rule 4 — No Cross-App Imports at Module Level

```python
# ❌ FORBIDDEN — in any file under src/
from apps.troubleshooting.src.models import TroubleshootingTechnology

# ✅ CORRECT — only inside a function, guarded by the enabled flag
def register_troubleshooting(app):
    if is_troubleshooting_enabled():
        from apps.troubleshooting.src.models import TroubleshootingTechnology
        ...
```

### Rule 5 — Navigation Entry

Add a nav link to `src/templates/base.html` that is **conditionally rendered** based on whether
the module is enabled. Follow the same pattern used for the Planning and Reporting nav entries.

---

## 🗄️ Domain Model (Draft — Pending Phase 0 Approval)

> [!NOTE]
> All tables use the SQLAlchemy `__bind_key__ = "troubleshooting"` attribute so they are stored
> in the app-local database, not in the core `mockcmms.db`.

### `troubleshooting_technologies`

Represents an equipment family or system type that can be selected by the user.

| Column        | Type           | Constraints               | Notes                                    |
| :------------ | :------------- | :------------------------ | :--------------------------------------- |
| `id`          | `INTEGER`      | PK, auto-increment        |                                          |
| `key`         | `VARCHAR(64)`  | UNIQUE, NOT NULL, indexed | URL-safe identifier (e.g., `"wtc"`)      |
| `name`        | `VARCHAR(128)` | NOT NULL                  | Display name (e.g., `"WTC Controllers"`) |
| `description` | `TEXT`         | nullable                  | Short description shown on card          |
| `icon_name`   | `VARCHAR(64)`  | nullable                  | Bootstrap icon or CSS class name         |
| `is_active`   | `BOOLEAN`      | NOT NULL, default `True`  | Soft-delete flag                         |
| `created_at`  | `DATETIME`     | NOT NULL                  | Auto-set on insert                       |

### `troubleshooting_error_codes`

Represents a specific error code belonging to a technology.

| Column          | Type           | Constraints                      | Notes                                          |
| :-------------- | :------------- | :------------------------------- | :--------------------------------------------- |
| `id`            | `INTEGER`      | PK, auto-increment               |                                                |
| `technology_id` | `INTEGER`      | FK → `technologies.id`, NOT NULL | Cascade delete                                 |
| `code`          | `VARCHAR(32)`  | NOT NULL, indexed                | The error code (e.g., `"E001"`, `"F-123"`)     |
| `title`         | `VARCHAR(256)` | NOT NULL                         | Short descriptive title                        |
| `description`   | `TEXT`         | nullable                         | Detailed explanation of the error              |
| `symptoms`      | `TEXT`         | nullable                         | Observable symptoms before diagnosis           |
| `severity`      | `VARCHAR(16)`  | NOT NULL, default `"medium"`     | `"low"` / `"medium"` / `"high"` / `"critical"` |
| `created_at`    | `DATETIME`     | NOT NULL                         | Auto-set on insert                             |

### `troubleshooting_steps`

Ordered resolution steps for a specific error code.

| Column            | Type      | Constraints                     | Notes                                     |
| :---------------- | :-------- | :------------------------------ | :---------------------------------------- |
| `id`              | `INTEGER` | PK, auto-increment              |                                           |
| `error_code_id`   | `INTEGER` | FK → `error_codes.id`, NOT NULL | Cascade delete                            |
| `step_order`      | `INTEGER` | NOT NULL                        | 1-based order; determines render sequence |
| `action`          | `TEXT`    | NOT NULL                        | The action the technician should take     |
| `expected_result` | `TEXT`    | nullable                        | What should happen if the step is correct |
| `warning`         | `TEXT`    | nullable                        | Safety or caution note for this step      |

### `troubleshooting_resources`

Reference documents and links associated with a technology.

| Column          | Type           | Constraints                      | Notes                                                          |
| :-------------- | :------------- | :------------------------------- | :------------------------------------------------------------- |
| `id`            | `INTEGER`      | PK, auto-increment               |                                                                |
| `technology_id` | `INTEGER`      | FK → `technologies.id`, NOT NULL | Cascade delete                                                 |
| `name`          | `VARCHAR(256)` | NOT NULL                         | Display name for the resource                                  |
| `resource_type` | `VARCHAR(32)`  | NOT NULL                         | `"manual"` / `"diagram"` / `"datasheet"` / `"video"` / `"url"` |
| `uri_or_path`   | `TEXT`         | NOT NULL                         | External URL or relative path — validated on save              |
| `description`   | `TEXT`         | nullable                         | Optional note about the resource contents                      |
| `is_active`     | `BOOLEAN`      | NOT NULL, default `True`         | Soft-delete flag                                               |

---

## 🔀 MVP User Flow

```
[1] Technician opens /troubleshooting/
        ↓
    Technology cards rendered from DB
    (Filter input available for quick narrowing)
        ↓
[2] Selects a technology card
        ↓
    /troubleshooting/<tech_key>/
    Technology hub: error search + resource links in one view
        ↓
[3a] Types error code or keyword in search box
        ↓
    Client-side live filter narrows results without page reload
        ↓
[3b] Selects a result from the list
        ↓
    /troubleshooting/<tech_key>/errors/<code>
    Error detail: title, severity badge, description, symptoms
        ↓
[4] Scrolls to ordered resolution steps
    Each step shows: action + expected result + optional warning
        ↓
[5] (Optional) Opens Resources tab / section
    /troubleshooting/<tech_key>/resources
    List of manuals, datasheets, links — opens in new tab
```

> [!TIP]
> Steps [3a] → [3b] → [4] should all happen within a single technology hub page when possible,
> to minimize navigation and keep the diagnosis flow fast for time-pressured technicians.

---

## 🛠️ Key Design Decisions

| Decision                                | Choice                           | Rationale                                                                  |
| :-------------------------------------- | :------------------------------- | :------------------------------------------------------------------------- |
| **Knowledge source-of-truth**           | Database (SQLite via SQLAlchemy) | Consistent with other apps; supports CRUD admin interface without restarts |
| **Config-driven vs DB-driven techs**    | DB-driven with admin CRUD        | Allows runtime updates without config file edits or deployments            |
| **Shared DB vs isolated DB**            | Isolated (`troubleshooting.db`)  | Keeps app self-contained; no risk of polluting `mockcmms.db`               |
| **Frontend approach**                   | Vanilla JS (ES6+), no framework  | Consistent with the rest of mockCMMS; no new tooling required              |
| **PDF import (Troubleshooting-Wizard)** | Deferred to V2                   | PDF parsing adds complexity; seed data covers MVP needs                    |
| **Authentication**                      | Reuse core mockCMMS session auth | No separate auth system; module is gated behind existing login             |
| **URL structure**                       | `/troubleshooting/<tech_key>/`   | Tech key in URL enables bookmarking and deep-linking per technology        |

---

## ⚠️ Risks and Mitigations

| Risk                                                | Likelihood | Impact | Mitigation                                                                         |
| :-------------------------------------------------- | :--------: | :----: | :--------------------------------------------------------------------------------- |
| Tight coupling with core app internals              |   Medium   |  High  | Enforce boundary: no module-level cross-app imports; code review gate              |
| Path traversal on local resource access             |    Low     |  High  | Centralize path resolution in `knowledge_repository.py`; validate on save          |
| Schema rework after MVP ships                       |   Medium   | Medium | Complete Phase 0 data model review before writing any code                         |
| Feature creep before MVP is stable                  |    High    | Medium | Lock MVP scope checklist in Phase 0; defer anything beyond it                      |
| Coverage drop from adding new code                  |    Low     | Medium | Write tests before or alongside each feature (TDD)                                 |
| `mypy` conflicts from `Troubleshooting-Wizard/src/` |    High    |  Low   | Already present — add `exclude` to `pyproject.toml` mypy config or move the folder |

> [!IMPORTANT]
> The `mypy` conflict between `src/` (mockCMMS core) and `Troubleshooting-Wizard/src/` is a
> **known pre-existing issue** reported in the validation output. It must be resolved — either
> by adding a mypy `exclude` pattern or by moving/renaming the `Troubleshooting-Wizard`
> directory — before Phase 1 begins.

---

## 📐 Non-Functional Requirements

### Performance

- Technology list page must load in under 500ms with 50+ technologies in the database
- Error code search filter must respond in real time (client-side) with no perceivable lag
  for up to 500 error codes per technology

### Security

- All routes must require an active mockCMMS session (reuse `@login_required` decorator)
- All forms (admin CRUD) must include CSRF tokens (Flask-WTF)
- Resource `uri_or_path` values must be validated and sanitized before storage and before use
- No internal paths, stack traces, or raw DB errors may be surfaced in HTTP responses

### Reliability

- The core app must start and operate normally when `TROUBLESHOOTING_ENABLED=False`
- A missing or misconfigured `troubleshooting.db` must produce a clear startup error, not a
  silent failure or a cryptic SQLAlchemy exception
- All service-layer errors must be caught, logged, and surfaced to the user as a friendly
  flash message

### Observability

- Use the existing `logs/application.log` and `logs/errors.log` pattern from the core app
- Log all error code lookups at DEBUG level and all failures at WARNING or ERROR level
- Do not log sensitive user input (search queries may contain internal codes — treat with care)

### Testability

- Service layer must be fully testable without a running Flask app (pure functions where possible)
- All routes must be testable via the Flask test client with an in-memory SQLite database
- Seed data function must be idempotent and callable in test setup without side effects
