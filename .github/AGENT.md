# AI Assistant Instructions for the CMMS Monorepo (Gemini Code Assist)

> **⚠️ SYNCHRONIZATION NOTICE:** This file (`AGENT.md`) is for **Gemini Code Assist** instructions. A parallel document, `copilot-instructions.md`, exists for **GitHub Copilot** instructions. While both documents should be nearly identical (except for model-specific references), they should be kept in sync. **If you make changes to this file, please ensure the corresponding section in `copilot-instructions.md` is also updated**, and vice versa.

This document provides a comprehensive guide for the Gemini Code Assist AI to effectively contribute to this monorepo. Adherence to these guidelines is critical for maintaining code quality, consistency, and a clean project structure.

## 1. Monorepo Philosophy

This repository is a monorepo that houses multiple, distinct but related projects (apps).

-   **Project Location:** The main application is in `src/` and modular apps are in the `apps/` directory.
-   **Isolation:** Each package is self-contained. It has its own dependencies (`requirements.txt`), virtual environment (`.venv`), tests (`tests/`), and documentation.
-   **Root Configuration:** The root of the repository contains shared configuration for the entire workspace, such as `.gitignore`, `LICENSE`, and repository-wide documentation and workflows in `.github/`.

---

## 2. Core Packages

### 2.1. `apps/workforceManager`

#### Overview

The `workforceManager` is a Flask-based web application for managing weekend technician task assignments. Its core purpose is to use skill-based matching and workload optimization to generate efficient work schedules.

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

The repository structure below shows the complete CMMS monorepo with all packages and key files. Pay special attention to the `workforceManager` package, especially `src/services/task_assigner.py`, which contains the core skill-based task assignment logic.

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
├── apps/workforceManager/         # ⭐ Skill-based task assignment module
│   ├── src/                       # Application source code
│   │   ├── routes/                # Flask blueprints
│   │   │   └── workforce_manager.py   # Main blueprint with all endpoints
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
│   │   └── workforce_manager.db   # SQLite database
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
-   **Run tests:** From the repository root, execute `pytest tests/` for main app tests or `pytest apps/workforceManager/tests/` for workforceManager tests.

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
    WORKFORCE_MANAGER_ENABLED=True
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

4.  **Run Workforce Manager in API Mode:** In another new terminal, **after activating the `workforceManager` virtual environment**, start the `workforceManager` server. It will run on port 5000 and automatically use the `api` data source as configured in the `.env` file.
    ```sh
    # Activate workforceManager venv (if not already active)
    # On Windows PowerShell: .\apps\workforceManager\.venv\Scripts\Activate.ps1
    # On macOS/Linux: source apps/workforceManager/.venv/bin/activate

    # WorkforceManager now runs as part of the main application
    ```


---

## 3. General Development Guidelines

-   **Git Workflow:** All contributions must follow the process outlined in [**GIT_WORKFLOW.md**](./GIT_WORKFLOW.md).
-   **Commit Messages:** Commit messages must adhere to the conventions described in [**CONTRIBUTING.md**](./CONTRIBUTING.md).
-   **Dependencies:** Manage dependencies via the `requirements.txt` file within each package. Do not create a root-level `requirements.txt`.
-   **Code Style:** Follow PEP 8 for Python and maintain consistency with the existing code style.

---

## 4. AI-Specific Instructions

-   **Efficiency is Key:** Perform all necessary edits for a given task in a single, atomic step per file.
-   **Be Proactive:** Before making changes, use your tools to understand the relevant files and the overall structure outlined in this document.
-   **Single Edit Rule:** When editing a file, apply all planned changes in one unified edit. Do not split the edit into multiple smaller patches for the same request.
-   **Documentation First:** Before committing any code changes, you **must** update all relevant documentation, including the root `README.md`, this `AGENT.md` file, and any package-specific documentation, to reflect the changes.
-   **Version Management:** After completing any significant changes:
    1. Update the appropriate `CHANGELOG.md` file(s) with new entries following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
    2. Update version numbers in both `CHANGELOG.md` and corresponding `README.md` files (must be synchronized)
    3. Use [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH (e.g., 1.2.0)
    4. Update the "Last Updated" date in README.md files
    5. Main app versions are in `/CHANGELOG.md` and `/README.md`
    6. WorkforceManager versions are in `/apps/workforceManager/CHANGELOG.md` and `/apps/workforceManager/README.md`