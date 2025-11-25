# AI Assistant Instructions

> **⚠️ SYNCHRONIZATION NOTICE:** This file (`GEMINI.md`) is for **Gemini Code Assist** instructions. A parallel document, `copilot-instructions.md`, exists for **GitHub Copilot** instructions. While both documents should be nearly identical (except for model-specific references), they should be kept in sync. **If you make changes to this file, please ensure the corresponding section in `copilot-instructions.md` is also updated**, and vice versa.

This document is divided into two parts:
1.  **Global AI Coding Standards:** Universal rules for high-quality code generation, applicable to any project.
2.  **Workspace Context & Specifics:** Detailed information about this specific monorepo, its architecture, and local workflows.

---

## 1. Global AI Coding Standards

These instructions apply to **all** coding tasks unless explicitly overridden by workspace-specific rules.

### 1.1. Code Quality & Style
-   **Clarity & Conciseness:** Always generate code that is clear, concise, and well-commented, especially for complex logic or algorithms.
-   **Conventions:** Adhere to the widely accepted style and formatting conventions for the target language or framework (e.g., PEP 8 for Python, Google JavaScript Style Guide, etc.).
-   **Paradigm:** Prefer class-based object-oriented programming for languages that support it, unless a functional or procedural approach is clearly more suitable for a simple utility or script.
-   **Maintainability:** Prioritize maintainability, scalability, and testability. Use modular design, meaningful naming, and separation of concerns.
-   **Refactoring:** Actively refactor code to improve its structure and remove unused or "dead" code.
-   **Hardcoding:** Avoid hardcoding values; use configuration files, environment variables, or constants where possible.

### 1.2. Reliability, Security & Performance
-   **Error Handling:** Include robust error handling appropriate for the language (e.g., try-catch, try-except, error callbacks, etc.) to ensure code reliability.
-   **Security:** For web applications or code handling user input, always follow security best practices (e.g., input validation, output encoding, use of secure libraries, avoiding injection vulnerabilities, etc.).
-   **Performance:** Optimize for performance and resource efficiency when relevant, but never at the expense of code clarity or correctness.
-   **Concurrency:** Handle concurrency and parallelism safely using language features like `async/await`, goroutines, or threads to improve performance.

### 1.3. Architecture & Best Practices
-   **Libraries:** Prefer using well-established libraries and frameworks for common tasks, and ensure dependencies are properly managed (e.g., `requirements.txt`, `package.json`, etc.).
-   **API Design:** When designing APIs, follow RESTful conventions or GraphQL best practices to ensure they are intuitive and scalable.
-   **State Management:** For complex applications, consider state management patterns and libraries (e.g., Redux, MobX, Vuex) for predictable state transitions.
-   **Infrastructure:** For infrastructure management, prefer Infrastructure as Code (IaC) tools like Terraform or CloudFormation.
-   **Observability:** Incorporate logging, metrics, and tracing to provide visibility into the application's behavior in production.

### 1.4. Testing & Deployment

#### 🚨 CRITICAL: Comprehensive Automated Verification (MANDATORY)

**ALL verification steps MUST be performed automatically. DO NOT ask the user to verify manually.**

**For UI Changes:**
-   **MANDATORY**: Use `browser_subagent` tool to perform comprehensive browser verification
-   The video recording MUST demonstrate ALL implemented, changed, or deleted features
-   Perform ALL necessary actions (scrolling, clicking, navigating) to show every aspect of the change
-   Test all user flows affected by the changes

**For Code Logic Changes:**
-   **MANDATORY**: Run automated tests using `pytest` or equivalent
-   Create new tests if none exist for the changed functionality
-   Verify all test cases pass before considering work complete

**For Database Schema Changes:**
-   **MANDATORY**: Verify database changes automatically:
  1. Stop the running app if active
  2. Delete the current database instance (e.g., `instance/mockcmms.db`)
  3. Restart the app to recreate the database with the new schema
  4. Run SQL queries to verify schema correctness
  5. Create automated tests in `tests/` directory to verify schema
-   Document all migration scripts and their execution results

**General Testing:**
-   **Verification:** Where appropriate, include basic unit tests or usage examples to demonstrate correctness and facilitate future maintenance.
-   **CI/CD:** Promote the use of CI/CD pipelines to automate testing and deployment, ensuring code quality and faster release cycles.

**Verification is NOT optional** - it is a critical step that MUST be completed automatically for every change.

### 1.5. Documentation Management

#### 🚨 CRITICAL: Documentation Standards (MANDATORY)

**Documentation quality is CRITICAL to avoid wasting time and resources.**

**All documentation MUST be:**
-   **Clean**: No duplicate information, no outdated sections
-   **Clear**: Easy to understand, well-organized structure
-   **Organized**: Logical flow, proper headings, consistent formatting
-   **Up-to-date**: Reflects current state, not historical plans or outdated analysis

**When creating or updating documentation:**
1. **Remove outdated content** - Delete old analysis, completed tasks, historical notes
2. **Single source of truth** - Each piece of information appears ONCE
3. **Status-focused** - Show what IS, not what WAS or what WILL BE
4. **Concise** - Use tables, bullet points, and clear sections
5. **Scannable** - Users should find information in seconds, not minutes

**Examples of BAD documentation:**
-   ❌ Mixing "completed work" with "remaining work" in the same section
-   ❌ Keeping old "issues identified" sections after issues are fixed
-   ❌ Multiple sections saying the same thing in different ways
-   ❌ Long narrative explanations when a table would suffice

**Examples of GOOD documentation:**
-   ✅ Single "Final Status" section showing current state
-   ✅ Tables summarizing changes (Before → After)
-   ✅ Clear verification steps with expected results
-   ✅ Concise summaries with links to details if needed

**Pay attention to documentation management** - This is a critical step that must be executed properly.

**Public API Documentation:**
-   Document public APIs, classes, and complex functions with docstrings or comments, following the conventions of the target language.

### 1.6. Interaction Guidelines

#### 🚨 CRITICAL: Smart Decision-Making (MANDATORY)

**DO NOT ask unnecessary questions or request user review for things you can verify yourself.**

**Before asking the user:**
1. **Explore all options** - Use available tools to gather information
2. **Make informed decisions** - Analyze the codebase, run tests, check documentation
3. **Verify automatically** - Run tests, check database, use browser verification
4. **Only ask when truly blocked** - Missing requirements, design decisions, user preferences

**Examples of UNNECESSARY questions:**
-   ❌ "Should I delete this unused model?" (if you verified it's unused, just delete it)
-   ❌ "Which cleanup phase should I do?" (if user said "do all", do all)
-   ❌ "Should I run tests?" (always run tests automatically)
-   ❌ "Can I proceed?" (if you have all information, proceed)

**Examples of NECESSARY questions:**
-   ✅ "Should we use approach A or B?" (genuine design decision)
-   ✅ "What should the default value be?" (user preference needed)
-   ✅ "This will break the API - should we proceed?" (user impact decision)

**Be smart enough to:**
-   Verify things yourself before asking
-   Use all available tools and information
-   Make decisions when you have sufficient context
-   Only escalate to user when truly necessary

**General Guidelines:**
-   **Clarification:** If the request is ambiguous or lacks important details, ask for clarification before generating extensive code.
-   **Focus:** Keep responses focused on the direct query. Avoid conversational fluff or suggesting unrelated tasks unless explicitly asked.
-   **Step-by-Step:** When provided with a numbered list of changes or a multi-step plan (e.g., "Prompt 1:", "Prompt 2:"), focus your response and any code modifications only on the current step or prompt being asked about.
-   **Auto-Run Preference:** When executing standard, non-destructive terminal commands (specifically running Python files like `run.py` or executing tests via `pytest`), prefer setting `SafeToAutoRun` to `true` to streamline the workflow, rather than asking for explicit user permission each time.

---

## 2. Workspace Context: Monorepo Philosophy

This repository is a monorepo that houses multiple, distinct but related projects (apps).

-   **Project Location:** The main application is in `src/` and modular apps are in the `apps/` directory.
-   **Isolation:** Each package is self-contained. It has its own dependencies (`requirements.txt`), virtual environment (`.venv`), tests (`tests/`), and documentation.
-   **Root Configuration:** The root of the repository contains shared configuration for the entire workspace, such as `.gitignore`, `LICENSE`, and repository-wide documentation and workflows in `.github/`.

---

## 3. Workspace Context: Core Packages

### 3.1. `apps/planning`

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

### 3.2. `apps/reports`

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

## 4. Workspace-Specific Guidelines

-   **Git Workflow:** All contributions must follow the process outlined in [**GIT_WORKFLOW.md**](./GIT_WORKFLOW.md).
-   **Commit Messages:** Commit messages must adhere to the conventions described in [**CONTRIBUTING.md**](./CONTRIBUTING.md).
-   **Dependencies:** Manage dependencies via the `requirements.txt` file within each package. Do not create a root-level `requirements.txt`.

---

## 5. Workspace-Specific AI Instructions

-   **Efficiency is Key:** Perform all necessary edits for a given task in a single, atomic step per file.
-   **Be Proactive:** Before making changes, use your tools to understand the relevant files and the overall structure outlined in this document.
-   **Single Edit Rule:** When editing a file, apply all planned changes in one unified edit. Do not split the edit into multiple smaller patches for the same request.
-   **Documentation First:** Before committing any code changes, you **must** update all relevant documentation to reflect the changes. This includes the root `README.md`, this `GEMINI.md` file, package-specific documentation, files in the `.github/` directory (e.g., `CONTRIBUTING.md`, `GIT_WORKFLOW.md`), and any files in `docs/` directories (root and subdirectories).
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
-   **Version Management:** After completing any significant changes:
    1. Update the appropriate `CHANGELOG.md` file(s) with new entries following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
    2. Update version numbers in both `CHANGELOG.md` and corresponding `README.md` files (must be synchronized)
    3. Use [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH (e.g., 1.2.0)
    4. Update the "Last Updated" date in README.md files
    5. Main app versions are in `/CHANGELOG.md` and `/README.md`
    6. Planning module versions are in `/apps/planning/CHANGELOG.md` and `/apps/planning/README.md`
