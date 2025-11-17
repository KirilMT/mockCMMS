# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-28

### Added
- **Advanced Table System**: Excel-like functionality with sorting, filtering, pagination, and export capabilities
- **Enhanced Database Models**: 
  - Asset model with asset_code, asset_type, cost_center fields
  - MaintenanceOrder model with 16+ new fields including priority, scheduling, time tracking
  - SparePart model with manufacturer information and stock tracking
  - Report and TableConfiguration models for advanced reporting
- **Reports Application**: Complete modular Flask blueprint for comprehensive reporting
  - Reactive production reports with filtering capabilities
  - Weekend completion reports with date range selection
  - PDF and Markdown export formats
  - Report management with view, download, and delete functionality
- **Advanced Table Component**: JavaScript-based table with:
  - Column management and reordering
  - Advanced filtering with multiple operators
  - Configuration saving and loading
  - Full-screen layout with internal scrolling
  - Export functionality (CSV, JSON)
- **UI Consistency**: Shared base templates across all applications
- **Template Architecture**: Modular apps use own templates extending main app base

### Changed
- **Database Schema**: Updated all main models with comprehensive field sets
- **Page Integration**: All main pages (Assets, MOs, Spare Parts, Users) now use advanced tables
- **Navigation**: Updated to include Reports app with proper routing
- **Template Structure**: Reports app templates moved to own directory for better maintainability
- **Route Handling**: Enhanced to support new database fields and dictionary data format

### Fixed
- **UI Consistency**: Reports app now maintains consistent layout with main application
- **Template Management**: Proper separation of app templates while maintaining UI consistency
- **Configuration Management**: Advanced table configurations properly saved and loaded
- **Search Functionality**: Enhanced filtering and search across all table implementations

### Technical Details
- Advanced JavaScript table component with full Excel-like functionality
- Modular Flask blueprint architecture for reports
- Enhanced SQLAlchemy models with comprehensive field coverage
- Responsive CSS design with full-screen table layouts
- Environment variable control for all modular applications

## [1.0.0] - 2025-01-27

### Added
- **Initial Release**: First stable version of the mockCMMS monorepo
- **Modular Architecture**: Main application with dynamically loadable apps
- **Workforce Manager Integration**: Skill-based technician task assignment system
- **Centralized Configuration**: Single `.env` file for all applications
- **Unified Environment**: One virtual environment and dependency management
- **Dynamic App Loading**: Enable/disable apps without code changes
- **REST API**: Complete API endpoints for data integration
- **Database Management**: SQLite-based data storage with utilities
- **Documentation**: Comprehensive project documentation and AI instructions
- **Testing Framework**: Test suite for main application functionality

### Changed
- **Project Structure**: Updated documentation to reflect actual directory layout
- **AI Instructions**: Enhanced AI assistant guidelines with balanced detail levels
- **README Documentation**: Optimized project structure for different audiences

### Technical Details
- Flask-based web application with modular design
- SQLite database with seeding capabilities
- Environment-based configuration management
- Integrated workforce management capabilities