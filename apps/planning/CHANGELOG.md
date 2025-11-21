# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Planning Engine (Phase 2 & 3):**
  - **Shift Break & Weekend Modes:** Implemented distinct planning modes with specific constraints (30-min window vs. multi-day).
  - **Shift Intersection Logic:** Backend logic to correctly intersect planning windows with shift patterns.
  - **Overnight Shift Support:** Full support for shifts crossing midnight (e.g., 22:00-06:00), including correct date wrapping.
  - **Weekend Day/Shift Subdivision:**
    - Gantt chart now splits weekend into Friday/Saturday/Sunday.
    - Further subdivides days into specific shifts (Morning/Afternoon/Night).
    - Implemented 3-level header hierarchy (Day -> Shift -> Hour).
  - **Team Formation Logic (Phase 5.7):**
    - Implemented `_select_best_team()` with multi-factor scoring (workload, skill diversity, proficiency).
    - Added automatic experience balancing (mixing senior/junior techs).
    - Implemented greedy algorithm for maximizing skill coverage in teams.

- **User Interface (Phase 3):**
  - **Custom Gantt Chart:**
    - Replaced external library with a custom, lightweight vanilla JS implementation.
    - Features: Technician-row layout, scrollable timeline, priority color-coding, and bidirectional table highlighting.
    - Dynamic height calculation based on technician count.
  - **Planning Dashboard:**
    - Integrated "Schedule View" and "Table View" into a unified `/planning` interface.
    - Added mode selection controls (Shift Break / Weekend).
    - Implemented "Loading" states and improved error handling (Toasts instead of alerts).
  - **Advanced Table Integration:**
    - Full support for sorting, filtering, and column management in the Planning Table.
    - Fixed height calculation issues for better viewport utilization.

- **Testing & Quality:**
  - **Test Suite Restoration:** Fixed critical import errors in `test_domain_models.py`, `test_planning_engine.py`, and `test_integration.py`.
  - **100% Pass Rate:** Achieved 38/38 passing tests for core planning logic.
  - **Security Audit:** Completed comprehensive audit of JavaScript assets.

### Changed
- **Documentation:**
  - **Refactoring:** Split monolithic `PLANNING_MODULE_ACTION_PLAN.md` into phase-specific files in `docs/roadmap/`.
  - **Consolidation:** Moved all app-specific documentation to `apps/planning/docs/`.
  - **Status Reporting:** Updated all status documents to accurately reflect the "Custom Gantt" implementation (correcting previous "Frappe Gantt" claims).
- **Architecture:**
  - Decoupled Planning UI from the legacy "Manage Mappings" Excel workflow.
  - Improved separation of concerns between Domain Models and Transformation Layer.

### Fixed
- **Critical:** Resolved `AttributeError: '__name__'` in `planning_engine.py` preventing server startup.
- **Logic:** Fixed "Shift Break" planning window constraints to strictly enforce 30-minute limits.
- **UI Bugs:**
  - Fixed "Weekend Planning" bug where single-day schedules assigned no tasks (Daily PM filtering issue).
  - Fixed Advanced Table event listener persistence after re-renders.
  - Fixed modal positioning and z-index issues.

## [1.2.0] - 2025-09-22

### Added
- **Project Screenshots**: Added a new screenshot gallery to the `README.md` to visually showcase the application's user interface.
- **Changelog**: Created a `CHANGELOG.md` file to track project versions and notable changes.
- **AI-Assisted Workflow**: Established a new workflow for updating version numbers and changelogs at the end of each issue.

### Changed
- **Project Structure**: Major refactoring of the project layout to follow standard conventions.
  - Renamed `wkndPlanning` directory to `src/`.
  - Moved runtime-generated directories (`logs`, `output`) to the project root.
  - Created a new `instance/` directory for the database.
  - Created a `docs/assets/` directory for documentation images.
- **Documentation**: Overhauled and updated the `README.md` with a more detailed and user-friendly "Setup and Installation" section and accurate project structure.
- **Issue Management**: Streamlined the issue and documentation workflow.
  - The AI assistant will now use the `gh issue list` command to fetch issues directly from GitHub.
  - Updated AI instruction files (`.github/AGENT.md`, `.github/copilot-instructions.md`) to reflect the new workflow.

### Removed
- **Obsolete `uploads` Directory**: Removed the unused `uploads` folder and all associated references from the code, configuration, and documentation.
- **Redundant Documentation**: Deleted obsolete `issues.md` and `ROADMAP.md` files to establish GitHub as the single source of truth.

## [1.1.0] - 2024-05-01

- Initial release version after major feature implementation.
