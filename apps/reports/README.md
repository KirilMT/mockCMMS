# Reports App

A modular reports application for mockCMMS that provides comprehensive reporting capabilities for maintenance operations.

## Features

- **Reactive Production Reports**: Generate reports for reactive maintenance orders during production periods
- **Weekend Completion Reports**: Generate reports for maintenance orders completed during weekends
- **Multiple Export Formats**: Support for Markdown and PDF (text) formats
- **Report Management**: View, download, and delete generated reports
- **Advanced Table Integration**: Uses mockCMMS advanced table component for report listing

## Installation

1. Install the reports app in editable mode:

   ```bash
   pip install -e apps/reports
   ```

2. Enable the reports app in your `.env` file:
   ```env
   REPORTS_ENABLED=True
   ```

## Configuration

The reports app uses the following environment variables:

- `REPORTS_ENABLED`: Enable/disable the reports app (default: False)

## File Structure

```
apps/reports/
├── src/
│   ├── routes/
│   │   └── reports.py          # Flask routes for reports
│   ├── services/
│   │   └── report_generator.py # Report generation logic
│   ├── templates/
│   │   ├── reports.html        # Reports listing page
│   │   ├── report_generate.html # Report generation form
│   │   └── report_detail.html  # Report detail view
│   └── __init__.py
├── instance/
│   └── reports/               # Generated report files
├── config/
├── setup.py
└── README.md
```

## Usage

1. Navigate to `/reports` to view all generated reports
2. Click "Generate Report" to create new reports
3. Select report type and parameters
4. Download or delete reports as needed

## Report Types

### Reactive Production Reports

- Filters maintenance orders by type "Reactive"
- Optional date range filtering
- Optional priority filtering
- Useful for tracking production disruptions

### Weekend Completion Reports

- Shows maintenance orders completed during weekends
- Automatically calculates weekend dates from selected week
- Useful for weekend maintenance summaries

## Integration

The reports app integrates with the main mockCMMS application through:

- Shared database models (Report, MaintenanceOrder, Asset, User)
- Common authentication system
- Templates extend main app's base template for consistent UI/UX
- Advanced table components integration
- Navigation integration in main application
