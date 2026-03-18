# mockCMMS (Mock Computerized Maintenance Management System)

[![CI Pipeline](https://github.com/KirilMT/mockCMMS/actions/workflows/ci.yml/badge.svg)](https://github.com/KirilMT/mockCMMS/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/KirilMT/mockCMMS/graph/badge.svg?token=PSNIDHV66T)](https://codecov.io/gh/KirilMT/mockCMMS)
[![Linting: Ruff](https://img.shields.io/badge/linting-ruff-purple.svg)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

A modular Flask-based maintenance management system with a monorepo architecture
that supports dynamic loading of specialized applications.

## 🚀 Features

- **Modular Architecture:** Main application with dynamically loadable apps
- **Advanced Table System:** Excel-like functionality with sorting, filtering,
  column management, and export
- **Enhanced Database Models:** Comprehensive asset tracking, maintenance order
  management, and spare parts inventory
- **Centralized Configuration:** Single `.env` file for all applications
- **Unified Environment:** One virtual environment and dependency management
- **Dynamic App Loading:** Enable/disable apps without code changes
- **Comprehensive Reporting:** PDF and Markdown export capabilities with
  advanced filtering
- **Consistent UI/UX:** Shared base templates with responsive design
- **Scalable Design:** Easy addition of new specialized modules

## 📦 Applications

mockCMMS supports a **main application** with dynamically loadable **modular apps**:

| App                                       | Purpose                                                                                                            | Status    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | --------- |
| **[Planning](apps/planning/README.md)**   | Intelligent maintenance planning with custom Gantt charts, shift-based scheduling, and skill-based task assignment | Available |
| **[Reporting](apps/reporting/README.md)** | Comprehensive reporting and analytics with PDF/Markdown export capabilities                                        | Available |

For planned applications and development timeline, see [Project Roadmap](docs/mockCMMS_roadmap.md). For creating new apps, see [Contributing documentation](.github/CONTRIBUTING.md).

## ⚙️ Setup and Installation

### Prerequisites

- **Windows (Recommended):** The setup scripts can automatically install Python, Git, and Node.js via `winget`.
- **macOS/Linux:**
  - **Python:** 3.12 or higher
  - **pip:** Python package installer
  - **Git:** Version control

### Installation Steps

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd mockCMMS
   ```

   > **Note:** If you've already cloned the repository, open your terminal in
   > the `mockCMMS` project root directory (where `run.py` is located).

2. **Run the setup script (Windows PowerShell):**

   ```powershell
   .\scripts\setup.ps1
   ```

   > **Note:** This script automatically detects or installs Python 3.12+ and Git (on Windows) and sets up the virtual environment. For macOS/Linux, manually create a virtual environment and install dependencies from `requirements.txt`.

3. **Run the application:**

   ```bash
   python run.py
   ```

   The application will start in development mode. Access it at <http://127.0.0.1:5000>.

### Development Setup

To install testing and development dependencies (Pytest, Jest, Playwright, linting tools, and optionally GitHub CLI):

```powershell
.\scripts\setup-dev.ps1
```

This script automates the installation of:

- **Tools (Windows via winget):** Node.js, GitHub CLI (optional)
- **Python (venv):** `pytest`, `ruff`, `black`, `mypy`, `pylint`, `docformatter`
- **JavaScript (npm):** `jest`, `playwright`, `eslint`, `prettier`, `stylelint`

See [Development Cheat Sheet](#-development-cheat-sheet) for common commands.

## ⚙️ Configuration

| Variable            | Description                   | Default                      |
| ------------------- | ----------------------------- | ---------------------------- |
| `SECRET_KEY`        | Flask secret key for sessions | dev_key_fallback_for_testing |
| `FLASK_DEBUG`       | Enable debug mode             | 0                            |
| `PLANNING_ENABLED`  | Enable Planning app           | False                        |
| `REPORTING_ENABLED` | Enable Reporting app          | False                        |

Enable/disable apps via `.env` (changes apply on restart):

```dotenv
PLANNING_ENABLED=True
REPORTING_ENABLED=True
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=0
```

For app-specific configuration, see the app's README.

## 🏃 Running the Application

```bash
# Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate     # macOS/Linux

# Run application
python run.py
```

**Default Access:**

- **URL:** <http://127.0.0.1:5000>
- **Demo Login:** `admin` / `admin123` (from `test_data/dummy_data.json`)

The application will start in development mode with auto-reload enabled when `FLASK_DEBUG=1`.

## 🛠️ Development Cheat Sheet

| Command                                   | Description                                                      |
| :---------------------------------------- | :--------------------------------------------------------------- |
| `python scripts/format_code.py`           | **Run first.** Auto-fix formatting: isort → black → docformatter |
| `python scripts/validate_code.py`         | Full validation: linting + unit tests + coverage checks          |
| `python scripts/validate_code.py --quick` | Fast validation: targeted tests, skips E2E                       |
| `pytest tests/backend`                    | Run backend tests                                                |
| `npm test`                                | Jest unit tests                                                  |
| `npm run test:e2e`                        | Playwright E2E tests                                             |

**Quick CI Simulation:**

```bash
python scripts/format_code.py && python scripts/validate_code.py
```

See [Tests documentation](tests/README.md) for detailed testing information.

## 🏗️ Architecture Overview

The application uses a **modular, layered architecture** supporting a main application with dynamically loadable specialized apps.

### Technology Stack

- **Backend:** Flask (Python 3.12+) with SQLAlchemy ORM
- **Frontend:** Vanilla JavaScript (ES6+) with modular component architecture
- **Database:** SQLite (dev) / PostgreSQL (production-ready)

### Project Layers

```
Frontend (src/static/)          → JavaScript modules + CSS
     ↓
API/Routes (src/routes/)        → REST API + Web routes
     ↓
Business Logic (src/services/)  → Database utilities, core logic
     ↓
Data Layer (instance/)          → SQLite/PostgreSQL databases
```

## 🤝 Contributing

Contributions are welcome! See [Contributing documentation](.github/CONTRIBUTING.md) for:

- Workflow and commit conventions
- Creating new modular apps
- Debugging tips and coverage requirements

---

**Version:** [2.0.0](https://github.com/KirilMT/mockCMMS/compare/v1.2.3...v2.0.0) (2026-03-18)
