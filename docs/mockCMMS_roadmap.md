# mockCMMS Project Roadmap: Future Enhancements
_Adapted from original mock_cmms_plan.md on November 17, 2025_

> **Note for AI Assistants:** This roadmap was created by analyzing a previous, deprecated project (`planning`). It captures the strategic vision and high-value, unimplemented features from that project, adapted for the modern, modular architecture of `mockCMMS`. Its purpose is to guide future development on the **existing** `mockCMMS` project, not to suggest overwriting or replacing its current functionality. Please use this file as a guide for *adding new features*, not for re-implementing what is already in place.

## 1. Purpose
This document outlines a strategic roadmap for the `mockCMMS` project, focusing on unimplemented, high-value features identified from previous planning documents. It is adapted to the project's current modular architecture and serves as a guide for future development sprints.

---

## 2. Application-Specific Feature Roadmap

### `planning` App Enhancements
This application already handles skill-based task assignment. The next logical steps involve deeper integration and more advanced planning management features.

- **[ ] Advanced Technician Management:**
    - **Goal:** Track detailed technician status beyond basic skills.
    - **Features:**
        - Implement models and UI to manage shifts, availability, and status (e.g., on-call, sick leave, training).
        - Track and visualize individual technician workload over time.

- **[ ] Advanced Planning Algorithms:**
    - **Goal:** Evolve beyond simple task assignment to holistic planning planning.
    - **Features:**
        - Develop logic for complex scheduling scenarios like multi-day shutdowns or holidays, factoring in technician availability.
        - Create a "planning" feature that can simulate and optimize schedules before finalizing them.

### `reports` App Enhancements
This application is intended for reporting and analytics. The following features would provide significant value.

- **[ ] Automated & Specialized Reporting:**
    - **Goal:** Generate key operational reports automatically.
    - **Features:**
        - **Weekend Task Report:** A report summarizing all tasks planned and completed over a weekend.
        - **Shift Production Report:** A summary of maintenance activities during a specific shift.
        - **Technician-Submitted Reports:** A system for technicians to log ad-hoc issues like breakdowns or PLC alarms, which can then be aggregated into reports.

- **[ ] Advanced Statistical Analysis:**
    - **Goal:** Provide deeper insights into maintenance operations.
    - **Features:**
        - Develop statistical dashboards for asset performance (e.g., Mean Time Between Failures).
        - Analyze technician performance and skill gaps.
        - Generate reports on spare part consumption trends.

### Core `mockCMMS` Application Enhancements
The core application can be improved with the following features to support the satellite apps.

- **[ ] Advanced Asset & Spares Management:**
    - **Goal:** Move beyond basic CRUD to more intelligent management.
    - **Features:**
        - **Asset Hierarchy:** Implement full parent-child relationships for assets (e.g., Line > Station > Asset > Sub-asset) and allow metadata (e.g., manuals, diagrams) to be attached.
        - **Automated Spares Ordering:** Create a system that automatically flags spare parts for reorder when inventory drops below a certain threshold during task planning.

- **[ ] Realistic Data Simulation & Testing Tools:**
    - **Goal:** Improve the robustness and testability of the entire platform.
    - **Features:**
        - Build a service that can generate realistic mock data (PMs, MOs, technician logs) for stress-testing and demonstration purposes.
        - Create a UI for simulating user inputs, such as manually triggering a breakdown alarm or reporting a technician as absent, to test the system's dynamic response.

---

## 3. Summary of Key Unimplemented Features

- **Advanced Technician Tracking:** Availability, workload, and dynamic status.
- **Automated, Specialized Reports:** Shift, weekend, and technician-submitted reports.
- **Hierarchical Assets & Automated Spares:** Deeper, more intelligent asset and inventory management.
- **Data Simulation Engine:** For robust testing and development.
