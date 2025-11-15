# Mock CMMS Development Plan

This document outlines the plan for creating the `mockCMMS` project, a robust mock CMMS application that will host and integrate the `workforceManager` application, serving as a comprehensive testing and improvement environment.

## Phase 1: Project Scaffolding and Initial Analysis (Completed)

- [x] 1.1. Create the basic directory structure for the `mockCMMS` Flask application, mirroring `workforceManager`.
- [x] 1.2. Initialize a dedicated virtual environment and `requirements.txt` for `mockCMMS`.
- [x] 1.3. Conduct a detailed analysis of `workforceManager` to identify data structures and interaction points (APIs, UI selectors) that need to be mocked.
    - [x] 1.3.1. Analyze `packages/workforceManager/src/services/extract_data.py` and `data_processing.py` to understand the structure of PM and REP task data from the Excel files.
    - [x] 1.3.2. Search the `workforceManager` codebase for any use of Selenium or other browser automation tools to identify required UI elements.

## Phase 2: `mockCMMS` Core Backend Development (Completed)

- [x] 2.1. Define database models (using SQLAlchemy and SQLite) for the necessary CMMS data (e.g., Tasks, Technicians, Skills).
- [x] 2.2. Create a mechanism to populate the `mockCMMS` database with realistic test data (e.g., a seed command).
- [x] 2.3. Implement a REST API endpoint (e.g., `/api/v1/tasks`) to serve task data in a format compatible with `workforceManager`.
- [x] 2.4. Implement a basic `run.py` to start the `mockCMMS` server.

## Phase 3: `mockCMMS` Core Frontend Development (Completed)

- [x] 3.1. Create basic HTML templates for any pages that `workforceManager` needs to interact with.
- [x] 3.2. Ensure these pages contain the specific HTML elements and CSS selectors identified during the analysis phase (1.3.2).

## Phase 4: `workforceManager` Initial Integration (Completed)

- [x] 4.1. Add a new configuration option to `workforceManager`'s `config/config.json` to select the data source (`excel` or `api`).
- [x] 4.2. Refactor the data loading logic in `workforceManager` (`src/services/extract_data.py`) to include a new function that fetches data from the `mockCMMS` API when the configuration is set to `api`.
- [x] 4.3. Ensure the existing Excel loading functionality remains the default and is not broken.

## Phase 5: Initial Testing and Documentation (Completed)

- [x] 5.1. Create integration tests that launch both `mockCMMS` and `workforceManager` to verify the end-to-end workflow.
- [x] 5.2. Write unit tests for the new API endpoints in `mockCMMS`.
- [x] 5.3. Update the root `README.md` and `.github/AI_INSTRUCTIONS.md` with instructions on how to run the integrated environment.

---

## Phase 6: Expanding `mockCMMS` to a Robust CMMS Application

- [x] 6.1. **Database Expansion:** Define new SQLAlchemy models for:
    - [x] 6.1.1. `Asset` (e.g., name, description, location, status)
    - [x] 6.1.2. `MaintenanceOrder` (MO) (e.g., asset_id, description, type, status, due_date)
    - [x] 6.1.3. `SparePart` (e.g., name, description, quantity, location)
    - [x] 6.1.4. `User` (e.g., username, password_hash, roles)
    - [x] 6.1.5. `Role` (e.g., name, permissions)
- [x] 6.2. **Backend APIs/Views for New Models:**
    - [x] 6.2.1. Implement REST API endpoints for CRUD operations on `Asset`, `MaintenanceOrder`, `SparePart`, `User`, `Role`.
    - [x] 6.2.2. Implement basic user authentication and authorization.
- [x] 6.3. **Frontend UI for New Models:**
    - [x] 6.3.1. Create a base layout for `mockCMMS` with a navigation bar (Home, Assets, MOs, Spare Parts, Users, Workforce Manager).
    - [x] 6.3.2. Create dedicated HTML pages/views to list, view details, and manage (add/edit/delete) Assets.
    - [x] 6.3.3. Create dedicated HTML pages/views to list, view details, and manage Maintenance Orders.
    - [x] 6.3.4. Create dedicated HTML pages/views to list, view details, and manage Spare Parts.
    - [x] 6.3.5. Create dedicated HTML pages/views for User Management (list users, add/edit roles).
    - [x] 6.3.6. Implement login/logout functionality.
- [x] 6.4. **Seed Data Expansion:** Update `seed.py` to include sample data for all new models.

## Phase 7: Deep Integration of `workforceManager` within `mockCMMS`

- [x] 7.1. **`workforceManager` Embedding:**
    - [x] 7.1.1. Create a new route/view in `mockCMMS` (e.g., `/workforce-manager`) that will render the `workforceManager` application.
    - [x] 7.1.2. Modify `workforceManager`'s `create_app` or configuration to detect if it's being run within `mockCMMS` and automatically set `DATA_SOURCE=api`.
    - [x] 7.1.3. Adapt `workforceManager`'s UI (specifically the data upload page) to be bypassed or hidden when integrated, as data will come from `mockCMMS`.
- [x] 7.2. **Data Synchronization/Mapping:**
    - [x] 7.2.1. Ensure `workforceManager`'s data extraction logic (when in API mode) can correctly consume data from `mockCMMS`'s expanded models (e.g., mapping `mockCMMS` Assets/MOs to `workforceManager` Tasks). This might require adjustments in `workforceManager`'s `extract_data.py` or `data_processing.py`.
- [x] 7.3. **Navigation:** Add a "Workforce Manager" link to `mockCMMS`'s main navigation.

## Phase 8: Final Testing and Documentation

- [x] 8.1. **Comprehensive Integration Tests:** Expand integration tests to cover the full `mockCMMS` UI and its interaction with the embedded `workforceManager`.
- [x] 8.2. **Update Documentation:**
    - [x] 8.2.1. Update `packages/mockCMMS/README.md` with instructions for running the full `mockCMMS` application.
    - [x] 8.2.2. Update root `README.md` and `.github/AI_INSTRUCTIONS.md` with instructions for running the expanded `mockCMMS` and its integrated `workforceManager`.