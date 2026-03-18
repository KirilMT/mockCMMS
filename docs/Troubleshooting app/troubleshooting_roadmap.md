# Troubleshooting App Roadmap

_Updated March 12, 2026_

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**When working on this project:**

1. **Update "ACTIVE WORK" section** when sprint phases change or complete
2. **Update status** as work progresses (e.g., "Phase 0" → "Phase 1" → "Completed")
3. **Move completed items** to "Recently Completed" section (don't delete immediately)
4. **Update "Last Updated" date** at the top when making changes
5. **Keep this file synchronized** with `docs/mockCMMS_roadmap.md` (high-level summary only
   there, full detail here)

> [!NOTE]
> This is a **pre-implementation planning roadmap**. The `apps/troubleshooting/` directory does
> not yet exist. The first implementation task is Phase 1 (Scaffolding). Once the app directory
> is created, a **canonical copy** of this roadmap must also live at
> `apps/troubleshooting/docs/troubleshooting_roadmap.md` and a bug tracker must be created at
> `apps/troubleshooting/docs/troubleshooting_bug_tracking.md`.

> [!TIP]
> **Document Relationship:** This roadmap plans new work for the Troubleshooting module. For bugs
> (once they exist), use the app-level bug tracker. For the core mockCMMS project overview, see
> [`docs/mockCMMS_roadmap.md`](../mockCMMS_roadmap.md).

---

## 🔥 ACTIVE WORK

**Current Sprint:** Phase 0 — Discovery and Architecture
**Status:** In Progress — Defining scope, data model, and integration boundaries
**Started:** March 12, 2026
**Target Completion:** TBD (depends on design decisions)

> [!IMPORTANT]
> **Phase 0 must be completed before any code is written.** The key deliverable is a finalized
> data model and a documented decision on the knowledge source-of-truth (database vs. config vs.
> hybrid). See [Concept & Architecture Doc](troubleshooting_concept_and_modular_architecture.md).

---

## 📋 PLANNED WORK

### Phase 0 — Discovery and Architecture

- **[ ] Finalize MVP Feature Scope** _(Priority: Critical)_
  - **Goal:** Lock the boundaries of the first release to avoid scope creep before scaffolding
    begins.
  - **Deliverables:**
    - Written MVP scope decision: what IS and IS NOT in v1.0
    - Confirmed data model (see architecture doc for draft)
    - Decision on source-of-truth for knowledge entries (database vs. config file vs. hybrid)
    - Defined integration points with the core mockCMMS app
  - **Status:** Not Started

- **[ ] Data Model Approval** _(Priority: Critical)_
  - **Goal:** Approve the initial database schema before implementation begins so schema changes
    don't cause rework.
  - **Draft tables (from architecture doc):**
    - `troubleshooting_technologies` — Equipment families/systems the user can select
    - `troubleshooting_error_codes` — Error codes linked to a technology with severity level
    - `troubleshooting_steps` — Ordered resolution steps per error code
    - `troubleshooting_resources` — Manuals, PDFs, and reference links per technology
  - **Reference:** [Architecture Document](troubleshooting_concept_and_modular_architecture.md)
  - **Status:** Draft in architecture doc — pending review

---

### Phase 1 — App Scaffolding

- **[ ] Create `apps/troubleshooting/` Package** _(Priority: Critical)_
  - **Goal:** Scaffold the full modular app structure, mirroring the conventions used by
    `apps/planning` and `apps/reporting`.
  - **Tasks:**
    - Create full directory structure (`src/`, `tests/`, `docs/`, `config/`, `instance/`)
    - Add `setup.py` (package setup) and `requirements.txt` (app-local dependencies)
    - Add `apps/troubleshooting/src/app.py` — Flask app factory
    - Add `apps/troubleshooting/src/config.py` — Configuration classes
    - Add `apps/troubleshooting/src/extensions.py` — Flask extensions (SQLAlchemy, etc.)
    - Add `apps/troubleshooting/src/routes/troubleshooting.py` — Blueprint definition
    - Add `apps/troubleshooting/README.md` — App-level documentation
    - Add `apps/troubleshooting/docs/troubleshooting_roadmap.md` — Canonical roadmap copy
    - Add `apps/troubleshooting/docs/troubleshooting_bug_tracking.md` — Bug tracker
    - Add placeholder `apps/troubleshooting/src/templates/troubleshooting/index.html`
  - **Status:** Not Started

- **[ ] Register App in Core mockCMMS** _(Priority: Critical)_
  - **Goal:** Add the `TROUBLESHOOTING_ENABLED` env toggle and hook the blueprint into the core
    app factory following the existing modular registration pattern.
  - **Files to modify:**
    - `.env.example` — Add `TROUBLESHOOTING_ENABLED=False` with documentation comment under
      the `# MODULAR PACKAGES CONFIGURATION` section
    - `src/app.py` — Add conditional import + blueprint registration **inside a function**
      (never at module level — follow the `PLANNING_ENABLED` / `REPORTING_ENABLED` pattern
      exactly)
  - **Constraint:** The core app must start cleanly when `TROUBLESHOOTING_ENABLED=False`. No
    `UnboundExecutionError`, no missing template errors.
  - **Status:** Not Started

---

### Phase 2 — Core MVP Features

- **[ ] Technology Selection UI** _(Priority: High)_
  - **Goal:** Implement the entry point — a technology selector that presents all active
    equipment families so technicians pick their context before searching.
  - **Features:**
    - Card/grid layout with technology name, description, and optional icon per card
    - Text-filter input to quickly narrow the list when many technologies are configured
    - Each card navigates to that technology's troubleshooting hub
    - Technologies driven by database records — not hardcoded HTML
    - Empty-state message when no technologies are configured
  - **Backend:** `GET /troubleshooting/` → renders index with technology list
  - **Status:** Not Started

- **[ ] Error Code Search** _(Priority: High)_
  - **Goal:** Let technicians search for an error code (or keyword) within a selected technology
    and retrieve structured diagnostic information.
  - **Features:**
    - Text input with live client-side filtering (no page reload for basic filtering)
    - Result list showing: code, title, severity badge, short description
    - Detail view per error code: full description, symptoms, possible causes, and severity
    - Ordered step-by-step resolution guide rendered below the error detail
    - "No results" state with a clear message and suggestion to check resources
  - **Backend:**
    - `GET /troubleshooting/<tech_key>/errors` → error code list for a technology
    - `GET /troubleshooting/<tech_key>/errors/<code>` → error code detail + resolution steps
  - **Status:** Not Started

- **[ ] Knowledge & Resource Links** _(Priority: High)_
  - **Goal:** Link each technology to associated manuals, PDFs, and reference materials so
    technicians can access documentation without leaving the app.
  - **Features:**
    - Resource list per technology: name, type, and access link
    - Support for external URLs (vendor portals, datasheets) and local file references
    - Resource-type visual indicator (manual, diagram, datasheet, video)
    - Secure path handling for local file references — no path traversal vulnerabilities
  - **Backend:** `GET /troubleshooting/<tech_key>/resources` → resource list for a technology
  - **Status:** Not Started

---

### Phase 3 — Data Population and Management

- **[ ] Seed Data for Development** _(Priority: High)_
  - **Goal:** Create a usable development dataset covering at least 2 technologies end-to-end
    so the app is demonstrable immediately after Phase 2 is complete.
  - **Tasks:**
    - Add seed script: `apps/troubleshooting/src/services/db_seeding.py`
    - Define at least 2 technologies (e.g., WTC Controllers, SEW Drive Systems — based on the
      Troubleshooting-Wizard reference data)
    - Add 5–10 error codes per technology, each with resolution steps and at least 1 resource
    - Make seeding idempotent — no duplicate records on repeated runs
    - Integrate seeding call into app startup (follows `AUTO_SEED_DATABASE` logic in core app)
  - **Status:** Not Started

- **[ ] Admin Interface for Technology Management** _(Priority: Medium)_
  - **Goal:** Allow admins to add, edit, and deactivate technologies and update knowledge
    entries without requiring code changes or manual database work.
  - **Features:**
    - CRUD for technologies (name, key, description, active flag)
    - CRUD for error codes and linked resolution steps
    - CRUD for resource links per technology
    - Role-based access: admin role required for all management routes
    - CSRF protection on all forms — mandatory, not optional
  - **Status:** Not Started

---

### Phase 4 — Quality and Hardening

- **[ ] Unit and Functional Tests** _(Priority: Critical)_
  - **Goal:** Ensure the service layer and all routes have test coverage that meets the
    repository floor (≥80% overall, ≥90% for critical paths).
  - **Tasks:**
    - Unit tests for all services (`troubleshooting_service.py`, `error_code_service.py`,
      `knowledge_repository.py`, `db_seeding.py`)
    - Functional tests for all routes (technology list, error search, detail view, resources)
    - Integration test: verify app registers correctly when enabled, is absent when disabled
    - Security tests: CSRF validation, authentication required, path sanitization
  - **Status:** Not Started

- **[ ] Security Review** _(Priority: High)_
  - **Goal:** Validate all user-facing inputs and prevent injection, path traversal, and
    information-leakage vulnerabilities before the module goes live.
  - **Checklist:**
    - [ ] Sanitize and validate all search query inputs server-side
    - [ ] Centralize resource path resolution — no raw user-supplied paths in file access
    - [ ] Ensure no internal file paths or stack traces are exposed in API responses
    - [ ] Rate-limit search endpoints if exposed without authentication
  - **Status:** Not Started

- **[ ] Coverage Verification and Final QA** _(Priority: High)_
  - **Goal:** Run `python scripts/validate_code.py` and confirm all checks pass before marking
    the module as shippable.
  - **Checklist (all must be green):**
    - [ ] `isort`, `black`, `docformatter` — no formatting errors
    - [ ] `ruff` — no linting errors
    - [ ] `mypy` — no type errors
    - [ ] `bandit` — no security issues
    - [ ] `pytest --cov` — ≥80% overall coverage
    - [ ] `diff-cover` — new code at ≥92% diff coverage
  - **Status:** Not Started

---

## ✅ RECENTLY COMPLETED

_Nothing completed yet — app is in planning phase (Phase 0)._

---

## 📅 DETAILED PHASES

Once implementation begins, create phase-level detail documents inside
`apps/troubleshooting/docs/roadmap/`:

| Phase   | Document (planned)              | Focus                                    |
| :------ | :------------------------------ | :--------------------------------------- |
| Phase 0 | `01_PHASE_0_DISCOVERY.md`       | Scope decisions, data model, boundaries  |
| Phase 1 | `02_PHASE_1_SCAFFOLDING.md`     | Package structure, env toggle, blueprint |
| Phase 2 | `03_PHASE_2_MVP_FEATURES.md`    | Technology selector, error search, links |
| Phase 3 | `04_PHASE_3_DATA_MANAGEMENT.md` | Seed data, admin CRUD interface          |
| Phase 4 | `05_PHASE_4_HARDENING.md`       | Tests, security, coverage, final QA      |

---

## 📊 EXIT CRITERIA FOR FIRST RELEASE

> [!IMPORTANT]
> All of the following must be true before the first release is considered shippable.

| Criterion                                                              | Status |
| :--------------------------------------------------------------------- | :----- |
| App starts cleanly with `TROUBLESHOOTING_ENABLED=True`                 | ⬜     |
| Core app is completely unaffected with `TROUBLESHOOTING_ENABLED=False` | ⬜     |
| At least 2 technologies fully implemented end-to-end                   | ⬜     |
| Error code search returns correct results for known codes              | ⬜     |
| All routes require authentication                                      | ⬜     |
| All forms have CSRF protection                                         | ⬜     |
| Test coverage ≥ 80%                                                    | ⬜     |
| Zero `ruff`, `black`, `mypy`, `isort` errors                           | ⬜     |
| `docs/mockCMMS_roadmap.md` reflects current app status                 | ⬜     |
| App-level bug tracker created at `apps/troubleshooting/docs/`          | ⬜     |
