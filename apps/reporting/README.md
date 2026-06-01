# Reporting App

A modular reporting application for mockCMMS that provides comprehensive reporting capabilities for maintenance operations.

## Features

- **Reactive Production Reporting**: Generate reports for reactive maintenance orders during production periods
- **Weekend Completion Reporting**: Generate reports for maintenance orders completed during weekends
- **Multiple Export Formats**: Support for Markdown and PDF (text) formats
- **Report Management**: View, download, and delete generated reports
- **Advanced Table Integration**: Uses mockCMMS advanced table component for report listing

## Installation

1. Install the reporting app in editable mode:

   ```bash
   pip install -e apps/reporting
   ```

2. Enable the reporting app in your `.env` file:
   ```dotenv
   REPORTING_ENABLED=True
   ```

## Configuration

The reporting app uses the following environment variables:

- `REPORTING_ENABLED`: Enable/disable the reporting app (default: False)

## File Structure

```
apps/reporting/
├── src/
│   ├── routes/
│   │   └── reporting.py          # Flask routes for reporting
│   ├── services/
│   │   └── report_generator.py # Report generation logic
│   ├── templates/
│   │   ├── reporting.html        # Reporting listing page
│   │   ├── report_generate.html # Report generation form
│   │   └── report_detail.html  # Report detail view
│   └── __init__.py
├── instance/
│   └── reporting/               # Generated report files
├── config/
├── setup.py
└── README.md
```

## Usage

1. Navigate to `/reporting` to view all generated reports
2. Click "Generate Report" to create a new report
3. Select report type and parameters
4. Download or delete reports when they are no longer needed

## Report Types

### Reactive Production Reporting

- Filters maintenance orders by type "Reactive"
- Optional date range filtering
- Optional priority filtering
- Useful for tracking production disruptions

### Weekend Completion Reporting

- Shows maintenance orders completed during weekends
- Automatically calculates weekend dates from selected week
- Useful for weekend maintenance summaries

## Integration

The reporting app integrates with the main mockCMMS application through:

- Shared database models (Report, MaintenanceOrder, Asset, User)
- Common authentication system
- Templates extend main app's base template for consistent UI/UX
- Advanced table components integration
- Navigation integration in main application

_Updated June 1, 2026_
