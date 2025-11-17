# mockCMMS (Mock Computerized Maintenance Management System)

A modular Flask-based maintenance management system with a monorepo architecture that supports dynamic loading of specialized applications.

## 🚀 Features

- **Modular Architecture:** Main application with dynamically loadable apps
- **Advanced Table System:** Excel-like functionality with sorting, filtering, column management, and export
- **Enhanced Database Models:** Comprehensive asset tracking, maintenance order management, and spare parts inventory
- **Centralized Configuration:** Single `.env` file for all applications
- **Unified Environment:** One virtual environment and dependency management
- **Dynamic App Loading:** Enable/disable apps without code changes
- **Comprehensive Reporting:** PDF and Markdown export capabilities with advanced filtering
- **Consistent UI/UX:** Shared base templates with responsive design
- **Scalable Design:** Easy addition of new specialized modules

## 📁 Project Structure

```
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
│   ├── workforceManager/    # Workforce management module
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
├── docs/                    # Documentation
├── instance/                # SQLite databases
├── test_data/               # Test fixtures
├── tests/                   # Main app tests
├── .env                     # Environment configuration
├── requirements.txt         # Dependencies
└── run.py                   # Application entry point
```

## 🔧 Applications

### Main Application
- **Core mockCMMS:** Base maintenance management functionality
- **Entry Point:** Serves as the foundation for all modular apps
- **Configuration Hub:** Manages settings for all integrated applications

### Modular Apps
- **[Workforce Manager](apps/workforceManager/README.md):** Advanced skill-based technician task assignment system with workload optimization
- **[Reports](apps/reports/README.md):** Comprehensive reporting and analytics system with PDF/Markdown export capabilities
- **Future Apps:** Additional modules can be easily integrated following the same pattern

> **Note:** For detailed setup and usage instructions for specific apps, refer to their individual README.md files.

## ⚙️ Setup and Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Git

### Installation Steps

1. **Navigate to the mockCMMS directory:**
   ```bash
   cd mockCMMS
   ```

2. **Create a virtual environment:**
   ```powershell
   py -3 -m venv .venv
   ```

3. **Activate the virtual environment:**
   - On **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - On **Windows (Command Prompt)**:
     ```cmd
     .venv\Scripts\activate
     ```
   - On **macOS/Linux (bash/zsh):**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install modular apps in editable mode:**
   ```bash
   pip install -e apps/workforceManager
   pip install -e apps/reports
   ```

6. **Set up environment configuration:**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file as needed for your environment.

7. **Run the application:**
   ```bash
   python run.py
   ```

8. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for sessions | Auto-generated |
| `FLASK_DEBUG` | Enable debug mode (1/true/yes) | 0 |
| `WORKFORCE_MANAGER_ENABLED` | Enable Workforce Manager app | False |
| `REPORTS_ENABLED` | Enable Reports app | True |

### App Management

- **Enable apps:** Set `APP_NAME_ENABLED=True` in `.env`
- **Disable apps:** Set `APP_NAME_ENABLED=False` in `.env`
- **Changes take effect:** On next application restart

## 🚀 Running the Application

### Development Mode
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate     # macOS/Linux

# Run application
python run.py
```

### Production Mode
```bash
python run.py
```

## 🔧 Development Guide

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

## 🗄️ Database Management

### Seeding the Database

```bash
# Activate virtual environment first
python src/services/seed.py
```

## 🤝 Contributing

Contributions are welcome. Please read the [contributing guidelines](.github/CONTRIBUTING.md) for development process, coding standards, and submission guidelines.

---

**Version:** 1.1.0 | **Last Updated:** January 28, 2025