# mockCMMS (Mock Computerized Maintenance Management System)

[![CI Pipeline](https://github.com/KirilMT/mockCMMS/actions/workflows/ci.yml/badge.svg)](https://github.com/KirilMT/mockCMMS/actions/workflows/ci.yml) [![codecov](https://codecov.io/gh/KirilMT/mockCMMS/branch/main/graph/badge.svg)](https://codecov.io/gh/KirilMT/mockCMMS) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

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

## 📁 Project Structure

```text
mockCMMS/
├── .github/                 # GitHub configuration and workflows
├── src/                     # Main mockCMMS application
│   ├── routes/              # API and web routes
│   │   ├── api.py           # REST API endpoints
│   │   └── main.py          # Web interface routes
│   ├── services/            # Business logic
│   │   └── db_utils.py      # Database utilities
│   ├── static/              # CSS, JS, images
│   ├── templates/           # HTML templates
│   └── app.py               # Flask application factory
├── apps/                    # Modular applications
│   ├── planning/            # Planning management module
│   │   ├── src/             # Application source code
│   │   │   ├── routes/      # Flask blueprints
│   │   │   ├── services/    # Core business logic
│   │   │   ├── static/      # CSS/JS assets
│   │   │   ├── templates/   # HTML templates
│   │   │   └── app.py       # Flask factory
│   │   ├── config/          # Configuration files
│   │   ├── instance/        # SQLite databases
│   │   ├── tests/           # Test suite
│   │   └── README.md        # Module documentation
│   └── reports/             # Reports and analytics module
│       ├── src/             # Application source code
│       │   ├── routes/      # Flask blueprints
│       │   ├── services/    # Report generation logic
│       │   └── templates/   # HTML templates
│       ├── instance/        # Generated reports storage
│       ├── setup.py         # Package configuration
│       └── README.md        # Module documentation
├── config/                  # Main app configuration
├── docs/                    # Project-level documentation
│   └── mockCMMS_roadmap.md  # High-level project roadmap
├── instance/                # SQLite databases
├── test_data/               # Test fixtures
├── tests/                   # Main app tests
├── .env                     # Environment configuration
├── requirements.txt         # Dependencies
└── run.py                   # Application entry point
```

## 📦 Applications

### Main Application

- **Core mockCMMS:** Base maintenance management functionality
- **Entry Point:** Serves as the foundation for all modular apps
- **Configuration Hub:** Manages settings for all integrated applications

### Modular Apps

- **[Planning](apps/planning/README.md):** Intelligent maintenance planning
  system with custom Gantt charts, shift-based scheduling, and skill-based task
  assignment
- **[Reports](apps/reports/README.md):** Comprehensive reporting and analytics
  system with PDF/Markdown export capabilities
- **Future Apps:** Additional modules can be easily integrated following the
  same pattern

> **Note:** For detailed setup and usage instructions for specific apps, refer
> to their individual README.md files.

## ⚙️ Setup and Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Git

### Installation Steps

1. **Clone the repository and navigate to it:**

   ```bash
   git clone <repository-url>
   cd mockCMMS
   ```

   > **Note:** If you've already cloned the repository, open your terminal in
   > the `mockCMMS` project root directory (where `run.py` is located).

2. **Run the setup script:**

   ```powershell
   .\scripts\setup.ps1
   ```

   The script will guide you through the installation process with clear
   feedback at each step.

3. **Activate the virtual environment:**

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   > **Note:** If you get an error, make sure you ran the setup script first.

4. **Run the application:**

   ```bash
   python run.py
   ```

## ⚙️ Configuration

### Environment Variables

| Variable           | Description                    | Default        |
| ------------------ | ------------------------------ | -------------- |
| `SECRET_KEY`       | Flask secret key for sessions  | Auto-generated |
| `FLASK_DEBUG`      | Enable debug mode (1/true/yes) | 0              |
| `PLANNING_ENABLED` | Enable Planning app            | False          |
| `REPORTS_ENABLED`  | Enable Reports app             | True           |

### App Management

- **Enable apps:** Set `APP_NAME_ENABLED=True` in `.env`
- **Disable apps:** Set `APP_NAME_ENABLED=False` in `.env`
- **Changes take effect:** On next application restart

## 🏃 Running the Application

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate     # macOS/Linux

# Run application
python run.py
```

The application will start in development mode by default. Access it at
`http://127.0.0.1:5000`

## 🏗️ JavaScript Architecture

### Overview

The application uses a modular JavaScript architecture for maintainability and
code organization.

### Core Components

#### Toast Notification System

- **Location:** `src/static/js/toast-notification.js`
- **Purpose:** Display user feedback messages (success, error, warning, info)
- **Features:**
  - FontAwesome icons for visual clarity
  - Auto-dismiss with configurable duration
  - Manual close button
  - Positioned at top-center of viewport
- **API:**

  ```javascript
  ToastNotification.success("Operation successful!");
  ToastNotification.error("Failed to save", 7000);
  ToastNotification.warning("Please review");
  ToastNotification.info("New update available");
  ```

#### Flash Messages Handler

- **Location:** `src/static/js/flash-messages.js`
- **Purpose:** Bridge Flask's `flash()` function with ToastNotification UI
- **Category Mapping:**
  - Flask `'danger'` → Toast `'error'`
  - Flask `'success'` → Toast `'success'`
  - Flask `'warning'` → Toast `'warning'`
  - Flask `'info'` → Toast `'info'`
- **Usage:**

  ```python
  # In Flask route
  flash('Asset created successfully!', 'success')
  flash('Invalid input', 'danger')
  ```

#### Advanced Table System

- **Location:** `src/static/js/advanced-table/` (modular architecture)
- **Components:**
  - `table-core.js` - Core AdvancedTable class
  - `table-render.js` - Rendering methods
  - `table-data.js` - Filtering, sorting, pagination
  - `table-config.js` - Save/load configurations
  - `table-events.js` - Event handling
  - `table-export.js` - CSV export functionality
  - `table-init.js` - Initialization helper
  - `table-sidebar.js` - Sidebar functionality
  - `table-resize.js` - Excel-like column resizing
  - `table-loading.js` - Loading states and spinners
  - `table-retry.js` - Retry mechanisms with exponential backoff
- **Features:**
  - Excel-like sorting and filtering with AND/OR logic
  - Column visibility management
  - Drag-and-drop column reordering
  - **Excel-like column resizing** with sub-pixel precision
  - Global search across all columns
  - Save/load custom view configurations
  - CSV export
  - Responsive design with collapsible sidebar
  - Loading states and automatic retry on failures

### File Organization

```text
src/static/js/
├── advanced-table/              # Modular table system
│   ├── table-core.js           # Core class and initialization
│   ├── table-render.js         # HTML rendering
│   ├── table-data.js           # Data operations
│   ├── table-config.js         # Configuration persistence
│   ├── table-events.js         # Event listeners
│   ├── table-export.js         # Export functionality
│   ├── table-init.js           # Helper functions
│   ├── table-sidebar.js        # Sidebar functionality
│   ├── table-resize.js         # Column resizing
│   ├── table-loading.js        # Loading states
│   └── table-retry.js          # Retry mechanisms
├── toast-notification.js       # Toast UI component (general purpose)
└── flash-messages.js           # Flask flash message integration
```

## �️ Development Guide

### Adding a New App

1. **Create app directory:**

   ```bash
   mkdir apps/your-app
   ```

2. **Add setup.py in the app root**

3. **Install in editable mode:**

   ```bash
   pip install -e apps/your-app
   ```

4. **Add configuration to `.env`:**

   ```env
   # --- Your App ---
   YOUR_APP_ENABLED=True
   YOUR_APP_SETTING=value
   ```

5. **Register blueprint in `src/app.py`**

### Development Workflow

1. Make changes to any app
2. Restart with `python run.py`
3. All apps reload automatically
4. Use `.env` to enable/disable apps for testing

## 🤝 Contributing

Contributions are welcome. Please read the
[contributing guidelines](.github/CONTRIBUTING.md) for development process,
coding standards, and submission guidelines.

---

**Version:** 1.2.0 | **Last Updated:** December 17, 2025
