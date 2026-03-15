<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-14

### Added

- **Advanced Table Enhancements:**
  - **Column Resizing Polish:** Excel-like column resizing with sub-pixel
    precision
    - Columns to the left stay fixed during resize
    - Columns to the right shift position without changing width
    - Table width adjusts dynamically to accommodate changes
    - Smooth 60fps resizing using `requestAnimationFrame`
    - Click suppression to prevent unintended sorting after resize
  - **Sidebar UI:** Modern collapsible sidebar with three sections (Filters,
    Columns, Saved Views)
  - **Filter Enhancements:** AND/OR logic, auto-apply on changes, validation
  - **Error Handling:** Loading spinners, exponential backoff retry, offline
    detection
  - **Testing Guide:** Comprehensive 200+ test cases covering all functionality
- **Planning Integration (Major Feature):**
  - **Planning Module:** Fully integrated the new Planning Module with a custom
    Gantt chart and Shift Planning capabilities
  - **Advanced Scheduling:** Added support for complex shift patterns
    (Production 3x8h, Maintenance 2x12h) and overnight shifts
  - **Team Optimization:** Implemented multi-factor team formation logic
    (skills, workload, experience)
- **Infrastructure:**
  - **Test Suite:** Restored and verified the global test suite; fixed
    cross-module import issues affecting `pytest` discovery
  - **Shared Components:** Enhanced `AdvancedTable` component with better height
    calculation and event handling, shared across all apps

### Changed

- **Advanced Table Component:**
  - Auto-fit padding reduced from 24px to 5px for tighter content fit
  - All width calculations now use float precision (`getBoundingClientRect()`)
    to eliminate jitter
  - Column resizing now updates table width synchronously:
    `New Width = Start Width + (Column Change)`
- **Documentation:**
  - **Restructuring:** Major reorganization of the `docs/` directory
    - Moved app-specific documentation to `apps/<app_name>/docs/`
    - Refactored the monolithic Planning Module action plan into phase-specific
      documents
    - Cleaned up the root `docs/` directory to focus on project-level roadmaps
    - Removed completed temporary planning document
      (`advanced-table-fixes-plan.md`)
- **Configuration:**
  - Updated `.env` handling to support new Planning Module configuration flags

### Fixed

- **Advanced Table:**
  - Fixed save/load configuration persistence across renders
  - Fixed global search breaking on input
  - Fixed filter dropdown not updating when columns change
  - Fixed empty state messages not appearing correctly
  - Fixed sidebar state persistence after page refresh
- **Stability:** Resolved startup crashes related to circular imports in the
  Planning Engine
- **UI/UX:** Fixed various issues with the Advanced Table component (modals,
  event listeners, viewport height)
- **Testing:** Fixed `pytest` discovery issues allowing full regression testing
  of the Planning module

## [1.1.0] - 2025-01-28

### Added

- **Advanced Table System**: Excel-like functionality with sorting, filtering,
  pagination, and export capabilities
- **Enhanced Database Models**:
  - Asset model with asset_code, asset_type, cost_center fields
  - MaintenanceOrder model with 16+ new fields including priority, scheduling,
    time tracking
  - SparePart model with manufacturer information and stock tracking
  - Report and TableConfiguration models for advanced reporting
- **Reporting Application**: Complete modular Flask blueprint for comprehensive
  reporting
  - Reactive production reporting with filtering capabilities
  - Weekend completion reporting with date range selection
  - PDF and Markdown export formats
  - Report management with view, download, and delete functionality
- **Advanced Table Component**: JavaScript-based table with:
  - Column management and reordering
  - Advanced filtering with multiple operators
  - Configuration saving and loading
  - Full-screen layout with internal scrolling
  - Export functionality (CSV, JSON)
- **UI Consistency**: Shared base templates across all applications
- **Template Architecture**: Modular apps use own templates extending main app
  base

### Changed

- **Database Schema**: Updated all main models with comprehensive field sets
- **Page Integration**: All main pages (Assets, MOs, Spare Parts, Users) now use
  advanced tables
- **Navigation**: Updated to include Reporting app with proper routing
- **Template Structure**: Reporting app templates moved to own directory for
  better maintainability
- **Route Handling**: Enhanced to support new database fields and dictionary
  data format

### Fixed

- **UI Consistency**: Reporting app now maintains consistent layout with main
  application
- **Template Management**: Proper separation of app templates while maintaining
  UI consistency
- **Configuration Management**: Advanced table configurations properly saved and
  loaded
- **Search Functionality**: Enhanced filtering and search across all table
  implementations

### Technical Details

- Advanced JavaScript table component with full Excel-like functionality
- Modular Flask blueprint architecture for reporting
- Enhanced SQLAlchemy models with comprehensive field coverage
- Responsive CSS design with full-screen table layouts
- Environment variable control for all modular applications

## [1.0.0] - 2025-01-27

### Added

- **Initial Release**: First stable version of the mockCMMS monorepo
- **Modular Architecture**: Main application with dynamically loadable apps
- **Planning Integration**: Skill-based technician task assignment system
- **Centralized Configuration**: Single `.env` file for all applications
- **Unified Environment**: One virtual environment and dependency management
- **Dynamic App Loading**: Enable/disable apps without code changes
- **REST API**: Complete API endpoints for data integration
- **Database Management**: SQLite-based data storage with utilities
- **Documentation**: Comprehensive project documentation and AI instructions
- **Testing Framework**: Test suite for main application functionality

### Changed

- **Project Structure**: Updated documentation to reflect actual directory
  layout
- **AI Instructions**: Enhanced AI assistant guidelines with balanced detail
  levels
- **README Documentation**: Optimized project structure for different audiences

### Technical Details

- Flask-based web application with modular design
- SQLite database with seeding capabilities
- Environment-based configuration management
- Integrated planning management capabilities
