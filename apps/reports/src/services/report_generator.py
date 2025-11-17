import os
import json
import sys
from datetime import datetime, timedelta

# Add the main src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from services.db_utils import MaintenanceOrder, Asset, User

class ReportGenerator:
    def __init__(self):
        # Create reports directory in the reports app instance folder
        self.reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_report(self, report_type, title, parameters, format_type, user_id):
        """Generate a report based on type and parameters"""
        
        if report_type == 'reactive_production':
            data = self._get_reactive_production_data(parameters)
        elif report_type == 'completed_weekend':
            data = self._get_completed_weekend_data(parameters)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_{timestamp}.{format_type.lower()}"
        file_path = os.path.join(self.reports_dir, filename)
        
        # Generate report based on format
        if format_type.lower() == 'pdf':
            self._generate_pdf_report(data, title, file_path)
        elif format_type.lower() == 'markdown':
            self._generate_markdown_report(data, title, file_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return file_path
    
    def _get_reactive_production_data(self, parameters):
        """Get reactive maintenance orders during production"""
        query = MaintenanceOrder.query.filter_by(order_type='Reactive')
        
        if parameters.get('start_date'):
            start_date = datetime.strptime(parameters['start_date'], '%Y-%m-%d')
            query = query.filter(MaintenanceOrder.created_at >= start_date)
        
        if parameters.get('end_date'):
            end_date = datetime.strptime(parameters['end_date'], '%Y-%m-%d')
            query = query.filter(MaintenanceOrder.created_at <= end_date)
        
        if parameters.get('priority') and parameters['priority'] != 'All':
            query = query.filter(MaintenanceOrder.priority == parameters['priority'])
        
        mos = query.all()
        
        return {
            'title': 'Reactive Maintenance Orders During Production',
            'parameters': parameters,
            'maintenance_orders': [mo.to_dict() for mo in mos],
            'total_count': len(mos),
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_completed_weekend_data(self, parameters):
        """Get completed maintenance orders for weekend"""
        weekend_date = datetime.strptime(parameters['weekend_date'], '%Y-%m-%d')
        
        # Get Saturday and Sunday of that week
        days_ahead = 5 - weekend_date.weekday()  # Saturday is 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = weekend_date + timedelta(days=days_ahead)
        sunday = saturday + timedelta(days=1)
        
        mos = MaintenanceOrder.query.filter(
            MaintenanceOrder.status == 'Completed',
            MaintenanceOrder.completion_date >= saturday,
            MaintenanceOrder.completion_date <= sunday + timedelta(days=1)
        ).all()
        
        return {
            'title': f'Completed Maintenance Orders - Weekend of {saturday.strftime("%Y-%m-%d")}',
            'parameters': parameters,
            'weekend_dates': {
                'saturday': saturday.strftime('%Y-%m-%d'),
                'sunday': sunday.strftime('%Y-%m-%d')
            },
            'maintenance_orders': [mo.to_dict() for mo in mos],
            'total_count': len(mos),
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_pdf_report(self, data, title, file_path):
        """Generate PDF report (placeholder - requires reportlab)"""
        # For now, create a simple text file as placeholder
        with open(file_path.replace('.pdf', '.txt'), 'w') as f:
            f.write(f"PDF Report: {title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {data['generated_at']}\n")
            f.write(f"Total Records: {data['total_count']}\n\n")
            
            for mo in data['maintenance_orders']:
                f.write(f"MO #{mo['id']}: {mo['description']}\n")
                f.write(f"  Status: {mo['status']}\n")
                f.write(f"  Priority: {mo['priority']}\n")
                f.write(f"  Asset: {mo.get('asset_name', 'N/A')}\n\n")
        
        # Return the text file path for now
        return file_path.replace('.pdf', '.txt')
    
    def _generate_markdown_report(self, data, title, file_path):
        """Generate Markdown report"""
        with open(file_path, 'w') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Generated:** {data['generated_at']}\n")
            f.write(f"**Total Records:** {data['total_count']}\n\n")
            
            if data.get('weekend_dates'):
                f.write(f"**Weekend Period:** {data['weekend_dates']['saturday']} to {data['weekend_dates']['sunday']}\n\n")
            
            f.write("## Maintenance Orders\n\n")
            
            if data['maintenance_orders']:
                f.write("| ID | Description | Status | Priority | Asset |\n")
                f.write("|----|-----------|---------|---------|---------|\n")
                
                for mo in data['maintenance_orders']:
                    f.write(f"| {mo['id']} | {mo['description']} | {mo['status']} | {mo['priority']} | {mo.get('asset_name', 'N/A')} |\n")
            else:
                f.write("No maintenance orders found for the specified criteria.\n")
            
            f.write(f"\n---\n*Report generated by mockCMMS on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        return file_path