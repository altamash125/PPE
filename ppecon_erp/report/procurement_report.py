# material_request_tracking/material_request_tracking/api/material_request.py

import frappe
from frappe import _
import json
from datetime import datetime, date

@frappe.whitelist(allow_guest=False)
def get_material_request_tracking(filters=None, sort_by=None):
    """
    API to fetch material request tracking data
    """
    
    # Parse filters if provided as string
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    
    # Build the SQL query
    query = """
        SELECT
            mr.name AS material_request,
            DATE(mr.transaction_date) AS mr_date,
            COALESCE(mri.project, mr.custom_project_name) AS project,
            mr.status AS mr_status,
            sq.name AS supplier_quotation,
            DATE(sq.transaction_date) AS sq_date,
            sq.workflow_state AS sq_status,
            sq.grand_total AS sq_total,
            po.name AS purchase_order,
            DATE(po.transaction_date) AS po_date,
            po.supplier AS po_supplier,
            po.grand_total AS po_total,
            po.status AS po_status,
            COALESCE(
                (SELECT MIN(pe2.posting_date)
                 FROM `tabPayment Entry Reference` per2
                 JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent 
                 WHERE per2.reference_name = po.name AND pe2.docstatus = 1), 
                NULL
            ) AS first_payment_date,
            COALESCE(
                (SELECT GROUP_CONCAT(DISTINCT pe2.name SEPARATOR ', ')
                 FROM `tabPayment Entry Reference` per2
                 JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent 
                 WHERE per2.reference_name = po.name AND pe2.docstatus = 1), 
                NULL
            ) AS payment_entries,
            COALESCE(
                (SELECT SUM(pe2.paid_amount)
                 FROM `tabPayment Entry Reference` per2
                 JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent 
                 WHERE per2.reference_name = po.name AND pe2.docstatus = 1), 
                0
            ) AS total_paid
        FROM `tabMaterial Request` mr
        LEFT JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
        LEFT JOIN `tabSupplier Quotation Item` sqi ON sqi.material_request = mr.name
        LEFT JOIN `tabSupplier Quotation` sq ON sqi.parent = sq.name AND sq.docstatus = 1
        LEFT JOIN `tabPurchase Order Item` poi ON poi.material_request = mr.name
        LEFT JOIN `tabPurchase Order` po ON poi.parent = po.name AND po.docstatus = 1
        WHERE mr.docstatus = 1
    """

    # Add filters
    conditions = []
    values = {}

    if filters:
        if filters.get('mr_status') and len(filters['mr_status']) > 0:
            placeholders = ', '.join(['%s'] * len(filters['mr_status']))
            conditions.append(f"mr.status IN ({placeholders})")
            values.update({f'status_{i}': status for i, status in enumerate(filters['mr_status'])})
        
        if filters.get('project'):
            conditions.append("(mri.project LIKE %(project)s OR mr.custom_project_name LIKE %(project)s)")
            values['project'] = f"%{filters['project']}%"
        
        if filters.get('supplier'):
            conditions.append("po.supplier LIKE %(supplier)s")
            values['supplier'] = f"%{filters['supplier']}%"
        
        if filters.get('from_date'):
            conditions.append("DATE(mr.transaction_date) >= %(from_date)s")
            values['from_date'] = filters['from_date']
        
        if filters.get('to_date'):
            conditions.append("DATE(mr.transaction_date) <= %(to_date)s")
            values['to_date'] = filters['to_date']

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " GROUP BY mr.name, sq.name, po.name"

    try:
        raw_data = frappe.db.sql(query, values, as_dict=True)
        
        # Process data to add delay calculations
        processed_data = []
        for row in raw_data:
            processed_row = dict(row)
            
            # Calculate delays
            processed_row['mr_sq_delay_days'] = calculate_delay(
                row.get('mr_date'), 
                row.get('sq_date')
            )
            processed_row['sq_po_delay_days'] = calculate_delay(
                row.get('sq_date'), 
                row.get('po_date')
            )
            processed_row['po_payment_delay_days'] = calculate_delay(
                row.get('po_date'), 
                row.get('first_payment_date')
            )
            
            processed_data.append(processed_row)
        
        # Apply sorting
        if sort_by:
            processed_data = sort_data(processed_data, sort_by)
        
        return {
            'status': 'success',
            'data': processed_data,
            'total_count': len(processed_data)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in material request tracking: {str(e)}", "Material Request Tracking")
        return {
            'status': 'error',
            'message': str(e)
        }

def calculate_delay(start_date, end_date):
    """Calculate delay in days between two dates"""
    if not start_date or not end_date:
        return None
    
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    delta = end_date - start_date
    return delta.days

def sort_data(data, sort_by):
    """Sort data based on specified option"""
    if sort_by == 'mr_date_first':
        return sorted(data, key=lambda x: (x.get('mr_date') or date.min), reverse=True)
    elif sort_by == 'sq_date_first':
        return sorted(data, key=lambda x: (x.get('sq_date') or date.min), reverse=True)
    elif sort_by == 'id_first':
        return sorted(data, key=lambda x: x.get('material_request') or '')
    elif sort_by == 'process':
        def process_score(row):
            if row.get('payment_entries'):
                return 1
            elif row.get('purchase_order'):
                return 2
            elif row.get('supplier_quotation'):
                return 3
            else:
                return 4
        return sorted(data, key=lambda x: (process_score(x), x.get('mr_date') or date.min))
    return data

@frappe.whitelist(allow_guest=False)
def get_filter_options():
    """Get filter options for the dashboard"""
    try:
        mr_statuses = frappe.db.sql_list("""
            SELECT DISTINCT status 
            FROM `tabMaterial Request` 
            WHERE docstatus = 1 
            ORDER BY status
        """)
        
        return {
            'status': 'success',
            'filters': {
                'mr_statuses': mr_statuses
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }