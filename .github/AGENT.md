# AI Assistant Instructions for the CMMS Monorepo (Gemini Code Assist)

This document provides a comprehensive guide for the Gemini Code Assist AI to effectively contribute to this monorepo. Adherence to these guidelines is critical for maintaining code quality, consistency, and a clean project structure.

## 1. Monorepo Philosophy

This repository is a monorepo that houses multiple, distinct but related projects (packages).

-   **Project Location:** All projects are located within the `packages/` directory.
-   **Isolation:** Each package is self-contained. It has its own dependencies (`requirements.txt`), virtual environment (`.venv`), tests (`tests/`), and documentation.
-   **Root Configuration:** The root of the repository contains shared configuration for the entire workspace, such as `.gitignore`, `LICENSE`, and repository-wide documentation and workflows in `.github/`.

---

## 2. Core Packages

### 2.1. `packages/workforceManager`

#### Overview

The `workforceManager` is a Flask-based web application for managing weekend technician task assignments. Its core purpose is to use skill-based matching and workload optimization to generate efficient work schedules.

#### Key Technologies

-   **Backend:** Python, Flask
-   **Data Processing:** pandas, numpy
-   **Database:** SQLite
-   **Frontend:** HTML, CSS, JavaScript (vanilla)
-   **Testing:** Pytest
-   **Containerization:** Docker, Docker Compose

#### Detailed Directory Structure

```
packages/workforceManager/
├── .env.example           # Example environment variables
├── config/                # Application configuration files
│   └── config.example.json
├── docker/                # Dockerfile and docker-compose.yml
├── docs/                  # Project-specific documentation
├── instance/              # (Generated) Instance folder for the database
├── logs/                  # (Generated) Application and error logs
├── output/                # (Generated) Output files like generated dashboards
├── requirements.txt       # Python dependencies for this package
├── run.py                 # Entry point to run the Flask application
├── src/                     # Main application source code
│   ├── __init__.py
│   ├── app.py             # Flask application factory and core routes
│   ├── config.py          # Configuration loading
│   ├── extensions.py      # Flask extension initializations
│   ├── template_filters.py  # Custom Jinja2 template filters
│   ├── routes/            # Flask Blueprints for modular routing
│   │   ├── api.py
│   │   ├── health.py
│   │   └── main.py
│   ├── services/          # Core business logic (most important directory)
│   │   ├── config_manager.py
│   │   ├── dashboard.py
│   │   ├── data_processing.py
│   │   ├── db_utils.py    # Database schema and operations
│   │   └── task_assigner.py # The main task assignment logic
│   ├── static/            # CSS, JS, and image assets
│   └── templates/         # Jinja2 HTML templates
├── test_data/             # Data files used for testing (e.g., .xlsb files)
└── tests/                 # Pytest tests for this package
```

#### Local Development & Testing

-   **Run the application:** From the repository root, execute `python packages/workforceManager/run.py`.
-   **Run tests:** From the repository root, execute `pytest packages/workforceManager/tests/`.

### 2.2. `packages/mockCMMS`

#### Overview

This package is intended to be a mock implementation of the production CMMS. Its purpose is to provide a realistic environment for integration testing of `workforceManager` and other future applications without depending on the real production system. It should be developed to mirror the API and behavior of the production CMMS as closely as possible.

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