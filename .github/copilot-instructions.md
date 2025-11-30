# AI Assistant Instructions for the CMMS Monorepo (GitHub Copilot)

> **⚠️ SYNCHRONIZATION NOTICE:** This file (`copilot-instructions.md`) is for **GitHub Copilot** instructions. A parallel document, `GEMINI.md`, exists for **Gemini Code Assist** instructions. While both documents should be nearly identical (except for model-specific references), they should be kept in sync. **If you make changes to this file, please ensure the corresponding section in `GEMINI.md` is also updated**, and vice versa.

This document provides a comprehensive guide for the GitHub Copilot AI to effectively contribute to this monorepo. Adherence to these guidelines is critical for maintaining code quality, consistency, and a clean project structure.

## 1. Monorepo Philosophy

This repository is a monorepo that houses multiple, distinct but related projects (apps).

-   **Project Location:** The main application is in `src/` and modular apps are in the `apps/` directory.
-   **Isolation:** Each package is self-contained. It has its own dependencies (`requirements.txt`), virtual environment (`.venv`), tests (`tests/`), and documentation.
-   **Root Configuration:** The root of the repository contains shared configuration for the entire workspace, such as `.gitignore`, `LICENSE`, and repository-wide documentation and workflows in `.github/`.

---

## 2. Core Packages

### 2.1. `apps/planning`

#### Overview

The `planning` is a Flask-based web application for managing weekend technician task assignments. Its core purpose is to use skill-based matching and workload optimization to generate efficient work schedules.

#### Core Architectural Shift

A critical piece of context for this package is its ongoing transition from a simple task priority-based system to a more sophisticated **technology skill-based system** for task assignments.

-   **Database Impact**: The `technician_task_assignments.priority` column is obsolete. The new schema requires a many-to-many relationship between tasks and the technologies/skills required to perform them.
-   **Logic Impact**: The core assignment logic in `src/services/task_assigner.py` must now prioritize matching task skill requirements with technician skill sets.

#### Key Technologies

-   **Backend:** Python, Flask
-   **Data Processing:** pandas, numpy
-   **Database:** SQLite
-   **Frontend:** HTML, CSS, JavaScript (vanilla)
-   **Testing:** Pytest
-   **Containerization:** Docker, Docker Compose

#### Detailed Directory Structure

The repository structure below shows the complete CMMS monorepo with all packages and key files. Pay special attention to the `planning` package, especially `src/services/task_assigner.py`, which contains the core skill-based task assignment logic.

```
mockCMMS/
├── .github/                       # GitHub workflows and AI instructions
│   ├── AGENT.md                   # Gemini Code Assist instructions
│   ├── copilot-instructions.md    # GitHub Copilot instructions
│   ├── CODEOWNERS                 # Code ownership definitions
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   └── GIT_WORKFLOW.md            # Git workflow strategy
├── src/                           # Main mockCMMS application
│   ├── routes/                    # API and web routes
│   │   ├── api.py                 # ⭐ REST API endpoints for data integration
│   │   └── main.py                # Main web interface routes
│   ├── services/                  # Business logic layer
│   │   └── db_utils.py            # Database utilities and helpers
│   ├── static/                    # Static assets (CSS, JS, images)
│   ├── templates/                 # Jinja2 HTML templates
│   └── app.py                     # ⭐ Flask application factory and config
├── apps/planning/         # ⭐ Skill-based task assignment module
│   ├── src/                       # Application source code
│   │   ├── routes/                # Flask blueprints
│   │   │   └── planning.py   # Main blueprint with all endpoints
│   │   ├── services/              # Core business logic
│   │   │   ├── task_assigner.py       # ⭐ CRITICAL: Skill-based assignment algorithm
│   │   │   ├── data_processing.py     # Data transformation and validation
│   │   │   ├── db_utils.py            # Database operations and queries
│   │   │   ├── dashboard.py           # Dashboard generation logic
│   │   │   ├── extract_data.py        # Data extraction from external sources
│   │   │   └── config_manager.py      # Configuration management
│   │   ├── static/                # CSS/JS assets
│   │   │   ├── css/               # Stylesheets
│   │   │   └── js/                # JavaScript modules
│   │   ├── templates/             # HTML templates
│   │   │   ├── index.html         # Main dashboard
│   │   │   └── manage_mappings.html # Configuration interface
│   │   ├── app.py                 # Flask factory and initialization
│   │   ├── config.py              # Configuration classes
│   │   └── extensions.py          # Flask extensions setup
│   ├── config/                    # Configuration files
│   │   ├── config.json            # App-specific settings
│   │   └── config.example.json    # Configuration template
│   ├── instance/                  # Runtime data
│   │   └── planning.db   # SQLite database
│   ├── tests/                     # Test suite
│   │   ├── test_core.py           # Core functionality tests
│   │   └── test_integration.py    # Integration tests
│   ├── logs/                      # Application logs (generated)
│   ├── output/                    # Generated reports and dashboards
│   └── README.md                  # Module-specific documentation
├── apps/reports/                  # ⭐ Reports and analytics module
│   ├── src/                       # Application source code
│   │   ├── routes/                # Flask blueprints
│   │   │   └── reports.py         # Main blueprint with all endpoints
│   │   ├── services/              # Core business logic
│   │   │   └── report_generator.py    # Report generation and export logic
│   │   └── templates/             # HTML templates
│   │       ├── reports.html           # Reports listing page with advanced table
│   │       ├── report_generate.html   # Report generation interface
│   │       └── report_detail.html     # Report detail view
│   ├── instance/                  # Generated reports storage
│   │   └── reports/               # Report files directory
│   ├── setup.py                   # Package configuration
│   └── README.md                  # Module-specific documentation
├── config/                        # Main app configuration
├── docs/                          # Project documentation
├── instance/                      # Main app databases
│   └── mockcmms.db                # Main application SQLite database
├── test_data/                     # Test fixtures and sample data
├── tests/                         # Main app tests
├── .env                           # Environment configuration
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
└── run.py                         # ⭐ Application entry point
```

#### Local Development & Testing

-   **Run the application:** From the repository root, execute `python run.py`. The main app will load enabled modular apps.
-   **Run tests:** From the repository root, execute `pytest tests/` for main app tests or `pytest apps/planning/tests/` for planning tests.

### 2.2. `apps/reports`

#### Overview

The `reports` is a Flask-based web application for generating comprehensive maintenance reports and analytics. Its core purpose is to provide PDF and Markdown export capabilities for reactive production reports and weekend completion summaries.

#### Key Technologies

-   **Backend:** Python, Flask
-   **Report Generation:** Custom report generator with PDF/Markdown support
-   **Database:** Shared SQLite database with main mockCMMS app
-   **Frontend:** HTML, CSS, JavaScript (vanilla)
-   **Export Formats:** PDF (text), Markdown

#### Core Features

-   **Modular Architecture:** Completely separate Flask blueprint app
-   **Environment Control:** Enable/disable via `REPORTS_ENABLED` environment variable
-   **Report Types:** Reactive production reports, weekend completion summaries
-   **Export Capabilities:** Multiple format support with file management
-   **Database Integration:** Uses shared mockCMMS database models

#### Running the Integrated Environment (with mockCMMS)

1.  **Configure `.env` Files:** Before running, ensure both packages have their `.env` files properly configured:
    
    **Root** - `.env`:
    ```dotenv
    PLANNING_ENABLED=True
    REPORTS_ENABLED=True
    DATA_SOURCE=api
    ```

2.  **Seed the Mock CMMS Database:** In a terminal, **after activating the `mockCMMS` virtual environment**, run the seed script to populate the `mockCMMS` database with test data:
    ```sh
    # Activate mockCMMS venv (if not already active)
    # On Windows PowerShell: .\apps\mockCMMS\.venv\Scripts\Activate.ps1
    # On macOS/Linux: source apps/mockCMMS/.venv/bin/activate

    python src/services/seed.py
    ```

3.  **Run the Mock CMMS Server:** In a new terminal, **after activating the `mockCMMS` virtual environment**, start the `mockCMMS` server. It will run on port 5001.
    ```sh
    # Activate mockCMMS venv (if not already active)
    # On Windows PowerShell: .\apps\mockCMMS\.venv\Scripts\Activate.ps1
    # On macOS/Linux: source apps/mockCMMS/.venv/bin/activate

    python run.py
    ```

4.  **Run Planning in API Mode:** In another new terminal, **after activating the `planning` virtual environment**, start the `planning` server. It will run on port 5000 and automatically use the `api` data source as configured in the `.env` file.
    ```sh
    # Activate planning venv (if not already active)
    # On Windows PowerShell: .\apps\planning\.venv\Scripts\Activate.ps1
    # On macOS/Linux: source apps/planning/.venv/bin/activate

    # planning now runs as part of the main application
    ```


---

## 3. General Development Guidelines

-   **Git Workflow:** All contributions must follow the process outlined in [**GIT_WORKFLOW.md**](./GIT_WORKFLOW.md).
-   **Commit Messages:** Commit messages must adhere to the conventions described in [**CONTRIBUTING.md**](./CONTRIBUTING.md).
-   **Dependencies:** Manage dependencies via the `requirements.t xt` file within each package. Do not create a root-level `requirements.txt`.
-   **Code Style:** Follow PEP 8 for Python and maintain consistency with the existing code style.

---

## 4. AI-Specific Instructions

-   **Efficiency is Key:** Perform all necessary edits for a given task in a single, atomic step per file.
-   **Be Proactive:** Before making changes, use your tools to understand the relevant files and the overall structure outlined in this document.
-   **Single Edit Rule:** When editing a file, apply all planned changes in one unified edit. Do not split the edit into multiple smaller patches for the same request.
-   **Documentation First:** Before committing any code changes, you **must** update all relevant documentation, including the root `README.md`, this `copilot-instructions.md` file, and any package-specific documentation, to reflect the changes.
-   **Roadmap & Plan Updates:** When implementing features or fixes:
    1. **Mark tasks as completed** in detailed plan files (e.g., `docs/advanced-table-fixes-plan.md`) by changing `[ ]` to `[x]`
    2. **Update progress tracking** sections with percentages and current focus
    3. **Update `docs/mockCMMS_roadmap.md`** when phases complete or status changes
    4. **Add implementation notes** under completed tasks with important details or decisions
    5. **Document blockers** if issues arise during implementation
    6. **Update "Last Updated" dates** in roadmap files
    7. **COMPLETE ALL SUBTASKS**: When working on a task, you MUST complete ALL subtasks within that task before moving to the next task. Do NOT leave tasks partially complete. If a task has 8 subtasks, implement all 8 before marking the task as done.
    8. **PROVIDE TESTING GUIDE**: After implementing ANY changes (bug fixes, features, enhancements), ALWAYS create a testing guide document in `docs/` with:
       - Comprehensive test cases covering all changes
       - Step-by-step instructions
       - Expected results for each test
       - Quick test scenarios (2-5 minutes)
       - Edge cases and error conditions
       - Visual checks (UI/UX)
       - Browser console checks
       - Pass/Fail checkboxes
       - Issues tracking section
    9. **TEMPORARY FILE MANAGEMENT** (GitHub Copilot in other IDEs):
        > **Purpose**: Since GitHub Copilot doesn't have a dedicated artifact system, use temporary markdown files for planning, tracking, and documentation during development.
        
        **Core Principles:**
        - **One file per type per task**: Maintain only ONE implementation plan, ONE task list, and ONE walkthrough per active task
        - **Update, don't recreate**: Always update existing temp files rather than creating new ones
        - **Never delete completed work**: Keep all completed tasks and historical information
        - **Clear naming**: Use descriptive names with feature identifiers
        - **Location**: Files are managed by the IDE in a system temp directory (similar to Antigravity's artifact system)
        
        **Temp File Types and Management:**
        
        1. **`task_[feature].md`** (Task Checklist):
           - ONE file per feature/task
           - Update by marking items `[x]` when complete
           - NEVER delete completed tasks - they show progress
           - Add new tasks at the bottom if scope expands
           - Keep all historical tasks visible
        
        2. **`plan_[feature].md`** (Technical Plan):
           - ONE file per major feature/task
           - Update sections as work progresses
           - Keep "Completed" sections at bottom for reference
           - Update "Current Status" section at top
           - NEVER delete completed items - move them to "Completed" section
        
        3. **`walkthrough_[feature].md`** (Verification/Results):
           - ONE file per feature/task
           - Append new test results, don't replace old ones
           - Organize by test sections
           - Keep all test evidence and results
           - Update summary sections as new tests complete
        
        4. **Screenshots/Evidence**:
           - Keep only the **2 most recent versions** of each screenshot
           - Use descriptive names: `test_2_4_search_results.png`
           - Reference in walkthrough with appropriate paths
        
        **Naming Conventions:**
        **Naming Conventions:**
        - Tasks: `task_[feature].md` (e.g., `task_table_features.md`)
        - Plans: `plan_[feature].md` (e.g., `plan_table_features.md`)
        - Walkthroughs: `walkthrough_[feature].md`
        - Screenshots: `[test_id]_[description].png` (e.g., `test_2_4_search_results.png`)
        
        **File Management:**
        > **Note**: Temp files are managed by the IDE in a system temp directory (similar to Antigravity's artifact system). Files are NOT stored in the project directory.
        
        - Files are stored in the IDE's system temp directory
        - Use the same naming conventions as artifacts for consistency
        - The IDE handles file location and organization automatically
        
        **Cleanup Rules:**
        - Before adding new screenshots, check if 2 versions exist and delete oldest
        - NEVER delete task lists, plans, or walkthroughs
        - Keep temp files organized and easy to scan
        - The IDE may automatically clean up temp files when sessions end
    10. **PROJECT DIRECTORY FILE CREATION** (CRITICAL):
        > **Rule**: DO NOT create unnecessary files in the project directory. Use IDE temp files for all temporary/testing outputs.
        
        **Strict Guidelines:**
        - **NEVER create temporary files in the project directory** - Use IDE temp file system instead
        - **NEVER create test output files in the project** - Use temp files for test results, logs, screenshots
        - **NEVER create planning/tracking files in the project** - Use temp files (task_[feature].md, plan_[feature].md, walkthrough_[feature].md)
        - **Only create files that are part of the actual codebase** - Source code, configuration, documentation
        
        **Exceptions (when project files ARE allowed):**
        1. **Source code files** - New features, bug fixes, refactoring
        2. **Configuration files** - Required by the application or tools
        3. **Documentation files** - User-facing docs in `docs/` directory (e.g., test plans, roadmaps)
        4. **Test files** - Permanent test suites in `tests/` directory
        
        **Mandatory Cleanup (if project files are created for testing):**
        - If you MUST create temporary files in the project for testing (e.g., test database, temp config):
          1. Inform the user about the file creation
          2. **Delete the file immediately after testing completes**
          3. Remind the user to verify the file is deleted
          4. Never commit temporary test files to git
        
        **Examples:**
        - ❌ BAD: Creating `temp_test_results.txt` in project root
        - ✅ GOOD: Using temp file `walkthrough_[feature].md` for test results
        - ❌ BAD: Creating `debug_log.txt` in project directory
        - ✅ GOOD: Using temp file or viewing logs in terminal
        - ❌ BAD: Creating `test_plan_draft.md` in project
        - ✅ GOOD: Using temp file `plan_[feature].md`
        - ✅ ACCEPTABLE: Creating `instance/test_temp.db` for testing, then deleting it after tests complete
        
        **Verification:**
        - Before completing any task, remind user to verify no unnecessary files were left in the project directory
        - Suggest checking `git status` to ensure only intended files are present
        - Remind user to clean up any temporary files before final commit
    11. **LOGIN CREDENTIALS**: If login is required for verification and default credentials fail, ALWAYS check `test_data/dummy_data.json` for valid user credentials (e.g., admin/admin123).
    12. **COMMIT STANDARDS**: Before committing, ALWAYS check the recent git log (`git log -n 5`) to ensure your commit message follows the project's structure, detail, and style conventions.
    13. **Version Management:** After completing any significant changes:
        1. Update the appropriate `CHANGELOG.md` file(s) with new entries following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
        2. Update version numbers in both `CHANGELOG.md` and corresponding `README.md` files (must be synchronized)
        3. Use [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH (e.g., 1.2.0)
        4. Update the "Last Updated" date in README.md files
        5. Main app versions are in `/CHANGELOG.md` and `/README.md`
        6. Planning module versions are in `/apps/planning/CHANGELOG.md` and `/apps/planning/README.md`
        7. Reports versions are in `/apps/reports/CHANGELOG.md` and `/apps/reports/README.md`
    14. **MANDATORY MANUAL TESTING & VERIFICATION**:
        > **Note**: GitHub Copilot does not have access to automated browser testing tools. All testing must be performed manually by the user.
        
        -   **Requirement**: For any task involving features that have a corresponding test plan in the `docs/` directory (e.g., `docs/table_features_test_plan.md` or any future `docs/*_test_plan.md`), you **MUST** provide clear manual testing instructions.
        -   **Procedure**:
            1.  **Identify Test Plan**: Check `docs/` for relevant test plans.
            2.  **Reference Test Plan**: Direct the user to the specific test plan document (e.g., "Please execute tests from `docs/table_features_test_plan.md`").
            3.  **Highlight Critical Tests**: If only specific sections are relevant to your changes, explicitly list which test sections to run (e.g., "Please run tests 2.3 (Filtering) and 2.4 (Global Search)").
            4.  **Provide Context**: Explain what changed and why specific tests are important for verification.
            5.  **Request Confirmation**: Ask the user to confirm that all tests pass before considering the task complete.
            6.  **Document Results**: If the user reports test failures, debug and fix issues, then request re-testing.
        -   **Testing Guide Creation**: When implementing new features or significant changes:
            1.  Create or update the relevant test plan in `docs/` if it doesn't exist or needs updates.
            2.  Ensure test plans include:
                - Clear step-by-step instructions
                - Expected results for each test
                - Screenshots or visual checkpoints where applicable
                - Edge cases and error conditions
            3.  Use the format from existing test plans (e.g., `docs/table_features_test_plan.md`) for consistency.
        -   **Completion Criteria**: Do not mark a task as complete until:
            1.  You have provided clear testing instructions to the user
            2.  The user has confirmed that tests pass OR
            3.  The user explicitly approves skipping tests for the current iteration

