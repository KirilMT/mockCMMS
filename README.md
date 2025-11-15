# CMMS Workspace

This repository is a monorepo for the CMMS (Computerized Maintenance Management System) project and its related services. It contains the core applications and supporting tools for the CMMS ecosystem.

## Workspace Structure

All projects and services are located within the `packages/` directory.

-   **`packages/workforceManager`**: The primary application for managing the technician workforce, tasks, and scheduling.
-   **`packages/mockCMMS`**: A mock CMMS application designed for integration testing and simulating the production environment.

## Getting Started

To get started with a specific project, please refer to the `README.md` file located within its directory. For example, for instructions on how to set up and run the Workforce Manager, see `packages/workforceManager/README.md`.

Each project is intended to have its own virtual environment and dependencies, which should be managed within its respective directory.

## Running the Integrated Environment

To test the integration between `workforceManager` and `mockCMMS`, you can run both applications simultaneously. `workforceManager` will fetch its data from the `mockCMMS` API instead of from an Excel file.

### 1. Set up both projects

Ensure you have installed the dependencies for both projects in their respective virtual environments:

```sh
# For workforceManager
python -m venv packages/workforceManager/.venv
# On Windows PowerShell, run from the monorepo root:
.\packages\workforceManager\.venv\Scripts\Activate.ps1
# On macOS/Linux, run from the monorepo root:
source packages/workforceManager/.venv/bin/activate
pip install -r packages/workforceManager/requirements.txt

# For mockCMMS
python -m venv packages/mockCMMS/.venv
# On Windows PowerShell, run from the monorepo root:
.\packages\mockCMMS\.venv\Scripts\Activate.ps1
# On macOS/Linux, run from the monorepo root:
source packages/mockCMMS/.venv/bin/activate
pip install -r packages/mockCMMS/requirements.txt
```

### 2. Seed the Mock CMMS Database

In a terminal, **after activating the `mockCMMS` virtual environment**, run the seed script to populate the `mockCMMS` database with test data:

```sh
# Activate mockCMMS venv (if not already active)
# On Windows PowerShell: .\packages\mockCMMS\.venv\Scripts\Activate.ps1
# On macOS/Linux: source packages/mockCMMS/.venv/bin/activate

python packages/mockCMMS/src/services/seed.py
```

### 3. Run the Mock CMMS Server

In a new terminal, **after activating the `mockCMMS` virtual environment**, start the `mockCMMS` server. It will run on port 5001.

```sh
# Activate mockCMMS venv (if not already active)
# On Windows PowerShell: .\packages\mockCMMS\.venv\Scripts\Activate.ps1
# On macOS/Linux: source packages/mockCMMS/.venv/bin/activate

python packages/mockCMMS/run.py
```

### 4. Run the Workforce Manager in API Mode

In another new terminal, **after activating the `workforceManager` virtual environment**, set the `DATA_SOURCE` environment variable to `api` and start the `workforceManager` server. It will run on port 5000.

```sh
# Activate workforceManager venv (if not already active)
# On Windows PowerShell: .\packages\workforceManager\.venv\Scripts\Activate.ps1
# On macOS/Linux: source packages/workforceManager/.venv/bin/activate

# For Windows (Command Prompt)
set DATA_SOURCE=api
python packages/workforceManager/run.py

# For Windows (PowerShell)
$env:DATA_SOURCE="api"
python packages/workforceManager/run.py

# For macOS/Linux
export DATA_SOURCE=api
python packages/workforceManager/run.py
```

Now, when you use the `workforceManager` application, it will be using the data served by `mockCMMS`.

## Contributing

Contributions are welcome. Please read the [contributing guidelines](.github/CONTRIBUTING.md) for more information on our development process, how to propose bugfixes and improvements, and the coding standards.