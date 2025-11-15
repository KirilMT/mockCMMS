# Mock CMMS Application

This is the `mockCMMS` application, a robust mock Computerized Maintenance Management System designed to simulate a production environment. It serves as a testing and integration platform for the `workforceManager` application and other future CMMS improvements.

## Features

-   **Core CMMS Entities:** Manages Assets, Maintenance Orders, Spare Parts, Users, and Roles.
-   **RESTful API:** Provides API endpoints for CRUD operations on all core entities.
-   **User Management:** Basic user registration, login, and role-based access control.
-   **Workforce Manager Integration:** Can host the `workforceManager` application, providing it with data directly from its own database.

## Getting Started

### 1. Setup

Ensure you have Python 3.8+ installed.

1.  **Navigate to the `mockCMMS` directory:**
    ```sh
    cd packages/mockCMMS
    ```
2.  **Create and activate a virtual environment:**
    ```sh
    python -m venv .venv
    # On Windows PowerShell
    .\.venv\Scripts\Activate.ps1
    # On macOS/Linux
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

### 2. Initialize and Seed the Database

Before running the application, you need to create the database and populate it with sample data.

1.  **Ensure your virtual environment is active.**
2.  **Run the seed script:**
    ```sh
    python src/services/seed.py
    ```
    This will create `mockcmms.db` in the `instance/` folder and fill it with sample Assets, MOs, Spare Parts, Users (including `admin`/`adminpass`), and Tasks.

### 3. Run the Application

1.  **Ensure your virtual environment is active.**
2.  **Start the Flask server:**
    ```sh
    python run.py
    ```
    The application will be available at `http://127.0.0.1:5001/`.

### 4. Accessing the Application

-   **Web UI:** Open your browser to `http://127.0.0.1:5001/`.
-   **API Endpoints:** Access the API at `http://127.0.0.1:5001/api/v1/`.
-   **Default Admin User:**
    -   Username: `admin`
    -   Password: `adminpass`

## Integration with `workforceManager`

This application is designed to integrate with `workforceManager`. Refer to the root `README.md` or `.github/AI_INSTRUCTIONS.md` for instructions on running the integrated environment.
