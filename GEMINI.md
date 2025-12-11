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
-   **Comment Standards:** 
    - Comments explain WHY, not WHAT (code should be self-explanatory)
    - NEVER reference bug/issue numbers (e.g., `<!-- Bug #5 -->`, `// Bug #5: Fix`)
    - Focus on business logic, complex algorithms, or non-obvious decisions
    - Use proper grammar and punctuation
    - Keep comments concise and relevant
    - Remove commented-out code blocks
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

#### 🚨 CRITICAL: Testing Documentation (MANDATORY)

**After implementing ANY changes (bug fixes, features, enhancements), ALWAYS create a testing guide document in `docs/` with:**
- Comprehensive test cases covering all changes
- Step-by-step instructions
- Expected results for each test
- Quick test scenarios (2-5 minutes)
- Edge cases and error conditions
- Visual checks (UI/UX)
- Browser console checks
- Pass/Fail checkboxes
- Issues tracking section

#### 🚨 CRITICAL: Evidence Accuracy (MANDATORY)

**When verifying with screenshots or videos, you MUST enable "No-Hallucination Mode".**

**Rules:**
1. **Analyze Evidence First**: Look closely at the screenshot/video BEFORE writing your conclusion.
2. **Describe Only What's Visible**: Your walkthrough description and "Test Passed" confirmation MUST MATCH EXACTLY what is shown in the media.
3. **No Assumptions**: Do not assume the code fix worked if the screenshot doesn't show it.
4. **Reject Mismatches**: If your code change typically produces Result A, but the screenshot shows Result B, trust the screenshot. The test FAILED.
5. **Zero Tolerance for Hallucination**: Describing a UI element that isn't there, or stating a layout is fixed when it's clearly broken in the image, is UNACCEPTABLE.

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

#### 🚨 CRITICAL: Documentation Upkeep (MANDATORY)

**Documentation First Rule:**
Before committing any code changes, you **must** update all relevant documentation to reflect the changes. This includes the root `README.md`, package-specific documentation, and relevant architecture or planning files.

**Roadmap & Plan Updates:**
When implementing features or fixes:
1. **Mark tasks as completed** in detailed plan files (e.g., `docs/*-plan.md`)
2. **Update progress tracking** sections
3. **Update project roadmap** (e.g., `docs/roadmap.md`) when phases complete
4. **Add implementation notes** under completed tasks
5. **Document blockers** if issues arise
6. **Update "Last Updated" dates**

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

#### 🚨 CRITICAL: File Corruption Handling (MANDATORY)

**NEVER use `git checkout` or `git restore` to fix corrupted files during editing!**

**Why**: Uncommitted changes will be PERMANENTLY LOST. This can result in losing hours of work.

**If you detect file corruption during editing:**
1. **STOP immediately** - Do not make further edits to the corrupted file
2. **Notify the user** - Explain what happened and ask how to proceed
3. **Suggest options**:
   - Manual restoration by user (they may have editor undo/backup)
   - Rewrite the specific corrupted section (if small)
   - User can decide if Git restore is appropriate (they know what's committed)

**Prevention**:
- Make smaller, more targeted edits instead of large multi-line replacements
- Ensure `TargetContent` EXACTLY matches the file content (including whitespace)
- For large files (>1000 lines), consider splitting into smaller modules first
- The running application does NOT cause file corruption - editing errors do

**General Guidelines:**
-   **Clarification:** If the request is ambiguous or lacks important details, ask for clarification before generating extensive code.
-   **Focus:** Keep responses focused on the direct query. Avoid conversational fluff or suggesting unrelated tasks unless explicitly asked.
-   **Step-by-Step:** When provided with a numbered list of changes or a multi-step plan (e.g., "Prompt 1:", "Prompt 2:"), focus your response and any code modifications only on the current step or prompt being asked about.
-   **Auto-Run Preference:** When executing standard, non-destructive terminal commands (specifically running Python files like `run.py` or executing tests via `pytest`), prefer setting `SafeToAutoRun` to `true` to streamline the workflow, rather than asking for explicit user permission each time.
-   **Browser Auto-Run Preference:** When using browser automation tools for verification and testing, prefer executing browser commands automatically without requesting user approval for each action. This streamlines the verification workflow and reduces interruptions. Only request user approval for destructive browser actions or when user input is genuinely required.
    -   **JavaScript Execution:** Always execute JavaScript code automatically during browser testing without requesting user permission. This includes overriding browser confirmations (e.g., `window.confirm = function() { return true; }`), manipulating DOM elements, and executing test scripts.
    -   **Confirmation Dialogs:** Automatically override `window.confirm`, `window.alert`, and `window.prompt` functions when needed for automated testing to prevent blocking the test flow.
-   **Server Check Before Browser Automation (MANDATORY):** Before using any browser automation tools (browser_subagent), ALWAYS check if the development server is running by checking the metadata for running terminal commands. If the server is not running (e.g., `python run.py` not in running commands list), start it first using `run_command` with appropriate wait time. Never assume the server is running based on browser subagent errors - always verify from metadata first.

### 1.7. Version Control & Commit Standards

#### 🚨 CRITICAL: Comprehensive Commit Workflow (MANDATORY)

Before committing, follow this comprehensive workflow to ensure all changes are properly reviewed, staged, and documented:

**Step 1: Review All Changed Files**
```bash
git status                    # See all modified files
git status --short            # Compact view
git diff --stat               # Summary of changes
```

**Step 2: Examine Each Changed File**
- For EACH modified file, review the actual changes:
```bash
git diff path/to/file.ext     # View detailed changes
```
- Understand what changed and why
- Identify if changes are related to the current task or are unrelated

**Step 3: Stage Relevant Files**
- Add files that are part of the current logical change:
```bash
git add path/to/file1.ext path/to/file2.ext
```
- DO NOT stage unrelated changes - commit them separately
- If a file has both related and unrelated changes, use `git add -p` for partial staging

**Step 4: Verify Staged Changes**
```bash
git diff --cached --stat              # Summary of staged changes
git diff --cached path/to/file.ext    # Review specific staged file
```
- Ensure only intended changes are staged
- Double-check no debug code, console.logs, or temporary changes are included

**Step 5: Create Detailed Commit Message**
- Check recent commits for style/format consistency:
```bash
git log -n 5 --oneline        # Recent commit titles
git log -n 1                  # Last commit details
```
- Follow project conventions (see examples in git log)
- Structure your commit message:
  * **Title**: Brief summary (50-72 chars), use conventional commits format
  * **Body**: Detailed explanation of WHAT changed and WHY
  * **Files**: List all modified files with brief description of changes
  * **Technical Details**: Implementation approach, algorithms, patterns used
  * **Testing**: How changes were verified

**Step 6: Final Pre-Commit Checklist**
- [ ] All related files are staged (`git diff --cached --stat`)
- [ ] No unrelated changes are staged
- [ ] Commit message is detailed and follows project conventions
- [ ] All temporary/debug code is removed
- [ ] Tests pass (if applicable)

**Example Workflow:**
```bash
# 1. Check what changed
git status

# 2. Review each file
git diff src/static/css/main.css
git diff src/templates/base.html

# 3. Stage related files
git add src/static/css/main.css src/templates/base.html docs/bug_tracking.md

# 4. Verify staged changes
git diff --cached --stat
git diff --cached src/static/css/main.css

# 5. Check commit history for style
git log -n 5

# 6. Commit with detailed message
git commit -m "feat: Fix Bug #30 - Assignees field layout shift

Implemented fixed height (100px) for Select2 container to prevent
layout shifts when adding/removing assignees.

Files Changed:
- src/static/css/main.css (Bug #30 CSS fix)
- src/templates/base.html (CSS cache busting)
- docs/bug_tracking.md (Bug #30 marked resolved)

Technical Details:
- Fixed height with overflow-y: auto for internal scrolling
- Flexbox layout for proper tag wrapping

Testing:
- Verified no layout shift with multiple assignees"
```

**CRITICAL**: Never commit without reviewing ALL changed files. Hidden changes in unexpected files can introduce bugs or break functionality.

### 1.8. AI Workflow Standards

-   **Efficiency is Key:** Perform all necessary edits for a given task in a single, atomic step per file.
-   **Be Proactive:** Before making changes, use your tools to understand the relevant files and the overall structure.
-   **Single Edit Rule:** When editing a file, apply all planned changes in one unified edit. Do not split the edit into multiple smaller patches for the same request.
-   **Complete All Subtasks:** When working on a task, you MUST complete ALL subtasks within that task before moving to the next task. Do NOT leave tasks partially complete. If a task has 8 subtasks, implement all 8 before marking the task as done.

### 1.9. Tooling & Workspace Standards

#### Artifact Management (Antigravity IDE)
> **Purpose**: Artifacts should be well-organized, clean, and easy to navigate.

**Core Principles:**
- **One artifact per type per task**: Maintain only ONE implementation plan, ONE task list, and ONE walkthrough per active task
- **Update, don't recreate**: Always update existing artifacts rather than creating new ones
- **Never delete completed work**: Keep all completed tasks and historical information in artifacts
- **Version control for media**: Keep only the most recent 1-2 versions of screenshots/videos
- **Organization**: Use clear, descriptive naming conventions

**Artifact Types:**
1. **`task.md`** (Task Checklist): One file per session. Update items `[x]` when complete. Add new items if scope expands.
2. **`implementation_plan.md`** (Technical Plan): One file per major task. Update status/headers.
3. **`walkthrough.md`** (Verification): Append new results. Keep evidence.

#### Temporary File Management (Other Environments)
For environments without native artifact support, use temporary markdown files (e.g., `task_[feature].md`, `plan_[feature].md`) managed in a system temp directory or ignored local directory. Follow the same "One file per type" and "Update, don't recreate" principles.

#### Project Directory File Creation (CRITICAL)
> **Rule**: DO NOT create unnecessary files in the project directory. Use artifacts/temp files for all temporary/testing outputs.

**Strict Guidelines:**
- **NEVER create temporary files in the project directory** - Use artifacts/temp files instead
- **NEVER create test output files in the project** - Use artifacts for test results, logs, screenshots
- **NEVER create planning/tracking files in the project** - Use artifacts
- **Only create files that are part of the actual codebase** - Source code, configuration, documentation

**Exceptions (when project files ARE allowed):**
1. **Source code files** - New features, bug fixes, refactoring
2. **Configuration files** - Required by the application or tools
3. **Documentation files** - User-facing docs in `docs/` directory
4. **Test files** - Permanent test suites in `tests/` directory

**Mandatory Cleanup:**
- If you MUST create temporary files in the project for testing (e.g., test database):
  1. Document it
  2. **Delete immediately after testing**
  3. Verify deletion
  4. Never commit temporary files

### 1.10. Bug Tracking & Discovery

#### 🚨 CRITICAL: Proactive Bug Discovery (MANDATORY)

When browsing or testing the application, if you discover a potential bug or unexpected behavior:

1. **DO NOT add it to any bug tracking document immediately**
2. **ASK the user first** - Describe what you observed:
   - What action you were performing
   - What you expected to happen
   - What actually happened
   - Screenshot/evidence if available
3. **WAIT for user confirmation** - Only add to bug tracking after user explicitly confirms it's a valid bug
4. **Assign proper priority** - Work with user to determine severity

> [!CAUTION]
> Adding bugs without user confirmation leads to document pollution and wasted effort on non-issues.

#### Bug Fix Workflow

1. **Before fixing**: Verify the bug exists (browser test, reproduce the issue)
2. **Apply fix**: Make code changes
3. **Verify fix**: Use browser automation to confirm fix works
4. **Update documentation**: Mark as "Fixed" with resolution notes
5. **Notify user**: Request confirmation before marking "Resolved"

#### Status Transitions

| From | To | Trigger |
|------|----|---------|
| Open | In Progress | You start working on the bug |
| In Progress | Fixed | Code applied, automated verification passed |
| Fixed | ✅ Resolved | **User confirms** fix works |

> [!CAUTION]
> NEVER mark a bug as "Resolved" without explicit user confirmation. "Fixed" means code is applied; "Resolved" means user verified.

#### Bug Tracking Document Updates

- **ALWAYS update summary counts** when changing bug statuses
- **NEVER create duplicate bug IDs** - search document first
- **Reference this section** instead of duplicating rules in bug tracking documents

---

## 2. Workspace Context: Monorepo Philosophy

This repository is a monorepo that houses multiple, distinct but related projects (apps).

-   **Project Location:** The main application is in `src/` and modular apps are in the `apps/` directory.
-   **Isolation:** Each package is self-contained. It has its own dependencies (`requirements.txt`), virtual environment (`.venv`), tests (`tests/`), and documentation.
-   **Root Configuration:** The root of the repository contains shared configuration for the entire workspace, such as `.gitignore`, `LICENSE`, and repository-wide documentation and workflows in `.github/`.

---

## 3. Workspace Context: Core Packages

### 3.1. Detailed Directory Structure

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

### 3.2. `apps/planning`

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

#### Local Development & Testing

-   **Run the application:** From the repository root, execute `python run.py`. The main app will load enabled modular apps.
-   **Run tests:** From the repository root, execute `pytest tests/` for main app tests or `pytest apps/planning/tests/` for planning tests.

### 3.3. `apps/reports`

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

-   **Git Workflow:** All contributions must follow the process outlined in [**GIT_WORKFLOW.md**](.github/GIT_WORKFLOW.md).
-   **Commit Messages:** Commit messages must adhere to the conventions described in [**CONTRIBUTING.md**](.github/CONTRIBUTING.md).
-   **Dependencies:** Manage dependencies via the `requirements.txt` file within each package. Do not create a root-level `requirements.txt`.

---

## 5. Workspace-Specific AI Instructions

1.  **LOGIN CREDENTIALS**: If login is required for verification and default credentials fail, ALWAYS check `test_data/dummy_data.json` for valid user credentials (e.g., admin/admin123).

2.  **VERSION MANAGEMENT**: After completing any significant changes:
    1. Update the appropriate `CHANGELOG.md` file(s) with new entries following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
    2. Update version numbers in both `CHANGELOG.md` and corresponding `README.md` files (must be synchronized)
    3. Use [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH (e.g., 1.2.0)
    4. Update the "Last Updated" date in README.md files
    5. Main app versions are in `/CHANGELOG.md` and `/README.md`
    6. Planning module versions are in `/apps/planning/CHANGELOG.md` and `/apps/planning/README.md`

3.  **MANDATORY AUTOMATED TESTING & VERIFICATION**:
    -   **Requirement**: For any task involving features that have a corresponding test plan in the `docs/` directory (e.g., `docs/table_features_test_plan.md` or any future `docs/*_test_plan.md`), you **MUST** execute the detailed test plan using the `browser_subagent`.
    -   **Procedure**:
        1.  **Identify Test Plan**: Check `docs/` for relevant test plans.
        2.  **Execute Tests**: Use `browser_subagent` to perform ALL steps in the plan (CRUD operations, UI interactions, etc.).
        3.  **Fix & Retry**: If ANY error occurs or a test fails, you must:
            -   Debug and fix the issue.
            -   Re-run the ENTIRE test suite from the plan.
            -   Repeat until ALL tests pass.
        4.  **Evidence**: You MUST provide a video recording and screenshots demonstrating that all tests have passed.
        5.  **Completion**: Do not mark the task as complete until verification is successful with evidence.
