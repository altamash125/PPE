import frappe
from frappe import _
from datetime import datetime, timedelta
import json

@frappe.whitelist()
def get_filtered_data(filters=None, page=1, page_size=10):
    """Get filtered data with pagination"""
    try:
        filters = json.loads(filters) if isinstance(filters, str) else (filters or {})
        page = int(page)
        page_size = int(page_size)
        
        conditions = []
        params = []
        
        # Build WHERE conditions based on filters
        if filters.get('search'):
            search = f"%{filters['search']}%"
            conditions.append("""
                (mr.name LIKE %s OR mr.project LIKE %s OR 
                sq.supplier_quotation LIKE %s OR po.purchase_order LIKE %s OR 
                pr.payment_request LIKE %s OR mr.supplier LIKE %s OR 
                po.supplier LIKE %s OR pr.party LIKE %s)
            """)
            params.extend([search] * 8)
        
        if filters.get('status') and filters['status'] != 'all':
            conditions.append("mr.status = %s")
            params.append(filters['status'])
        
        if filters.get('date_range') and filters['date_range'] != 'all':
            date_condition = get_date_condition(filters['date_range'])
            if date_condition:
                conditions.append(date_condition)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Base query
        query = """
            SELECT 
                mr.name as material_request,
                mr.status as mr_status,
                mr.project,
                DATE(mr.transaction_date) as mr_date,
                sq.name as supplier_quotation,
                DATE(sq.transaction_date) as sq_date,
                sq.status as sq_status,
                sq.grand_total as sq_total,
                po.name as purchase_order,
                DATE(po.transaction_date) as po_date,
                po.supplier as po_supplier,
                po.grand_total as po_total,
                pr.name as payment_request,
                DATE(pr.creation) as pr_date,
                pr.party as pr_party,
                pr.grand_total as pr_total,
                GROUP_CONCAT(DISTINCT pe.name SEPARATOR ', ') as payment_entries,
                GROUP_CONCAT(DISTINCT DATE(pe.posting_date) SEPARATOR ', ') as pe_dates,
                GROUP_CONCAT(DISTINCT pe.reference_no SEPARATOR ', ') as cheque,
                COALESCE(po.grand_total, pr.grand_total, 0) as total_amount
            FROM `tabMaterial Request` mr
            LEFT JOIN `tabSupplier Quotation` sq ON sq.material_request = mr.name
            LEFT JOIN `tabPurchase Order` po ON po.material_request = mr.name
            LEFT JOIN `tabPayment Request` pr ON pr.reference_name = mr.name
            LEFT JOIN `tabPayment Entry Reference` per ON per.reference_name = pr.name
            LEFT JOIN `tabPayment Entry` pe ON pe.name = per.parent
            WHERE {where_clause}
            GROUP BY mr.name, sq.name, po.name, pr.name
            ORDER BY mr.transaction_date DESC
            LIMIT %s OFFSET %s
        """.format(where_clause=where_clause)
        
        # Count query
        count_query = """
            SELECT COUNT(DISTINCT mr.name)
            FROM `tabMaterial Request` mr
            LEFT JOIN `tabSupplier Quotation` sq ON sq.material_request = mr.name
            LEFT JOIN `tabPurchase Order` po ON po.material_request = mr.name
            LEFT JOIN `tabPayment Request` pr ON pr.reference_name = mr.name
            WHERE {where_clause}
        """.format(where_clause=where_clause)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Execute queries
        data = frappe.db.sql(query, params + [page_size, offset], as_dict=True)
        total_records = frappe.db.sql(count_query, params, as_scalar=True)[0]
        
        return {
            "success": True,
            "data": data,
            "total_records": total_records,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_filtered_data: {str(e)}", "PO PR Tracker")
        return {
            "success": False,
            "message": str(e)
        }

def get_date_condition(date_range):
    """Get SQL condition for date range filter"""
    today = datetime.now().date()
    
    if date_range == 'today':
        return "DATE(mr.transaction_date) = %s"
    elif date_range == 'week':
        week_start = today - timedelta(days=today.weekday())
        return "DATE(mr.transaction_date) >= %s"
    elif date_range == 'month':
        month_start = today.replace(day=1)
        return "DATE(mr.transaction_date) >= %s"
    elif date_range == 'quarter':
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start = today.replace(month=quarter_month, day=1)
        return "DATE(mr.transaction_date) >= %s"
    elif date_range == 'year':
        year_start = today.replace(month=1, day=1)
        return "DATE(mr.transaction_date) >= %s"
    
    return None

# import frappe
# from frappe import _

# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     summary = get_summary_data(data)
    
#     return columns, data, None, None, summary

# def get_columns():
#     return [
#         {"fieldname": "material_request", "label": _("Material Request"), "fieldtype": "Link", "options": "Material Request", "width": 120},
#         {"fieldname": "mr_status", "label": _("MR Status"), "fieldtype": "Data", "width": 100},
#         {"fieldname": "project", "label": _("Project"), "fieldtype": "Data", "width": 120},
#         {"fieldname": "mr_date", "label": _("MR Date"), "fieldtype": "Date", "width": 100},
#         {"fieldname": "supplier_quotation", "label": _("Supplier Quotation"), "fieldtype": "Link", "options": "Supplier Quotation", "width": 120},
#         {"fieldname": "sq_date", "label": _("SQ Date"), "fieldtype": "Date", "width": 100},
#         {"fieldname": "sq_status", "label": _("SQ Status"), "fieldtype": "Data", "width": 100},
#         {"fieldname": "sq_total", "label": _("SQ Total"), "fieldtype": "Currency", "width": 100},
#         {"fieldname": "purchase_order", "label": _("Purchase Order"), "fieldtype": "Link", "options": "Purchase Order", "width": 120},
#         {"fieldname": "po_date", "label": _("PO Date"), "fieldtype": "Date", "width": 100},
#         {"fieldname": "po_supplier", "label": _("PO Supplier"), "fieldtype": "Data", "width": 120},
#         {"fieldname": "po_total", "label": _("PO Total"), "fieldtype": "Currency", "width": 100},
#         {"fieldname": "payment_request", "label": _("Payment Request"), "fieldtype": "Link", "options": "Payment Request", "width": 120},
#         {"fieldname": "pr_date", "label": _("PR Date"), "fieldtype": "Date", "width": 100},
#         {"fieldname": "pr_party", "label": _("PR Party"), "fieldtype": "Data", "width": 120},
#         {"fieldname": "pr_total", "label": _("PR Total"), "fieldtype": "Currency", "width": 100},
#         {"fieldname": "payment_entries", "label": _("Payment Entries"), "fieldtype": "Data", "width": 150},
#         {"fieldname": "pe_dates", "label": _("PE Dates"), "fieldtype": "Data", "width": 120},
#         {"fieldname": "cheque", "label": _("Cheque"), "fieldtype": "Data", "width": 100},
#         {"fieldname": "total_amount", "label": _("Total Amount"), "fieldtype": "Currency", "width": 100}
#     ]

# def get_data(filters=None):
#     sql_query = """
#         SELECT
#             mr.name AS material_request,
#             mr.status AS mr_status,
#             COALESCE(mri.project, mr.custom_project_name) AS project,
#             DATE(mr.transaction_date) AS mr_date,
            
#             -- Supplier Quotation
#             sq.name AS supplier_quotation,
#             DATE(sq.transaction_date) AS sq_date,
#             sq.workflow_state AS sq_status,
#             sq.grand_total AS sq_total,
            
#             -- Purchase Order
#             po.name AS purchase_order,
#             DATE(po.transaction_date) AS po_date,
#             po.supplier AS po_supplier,
#             po.grand_total AS po_total,
            
#             -- Payment Request
#             pr.name AS payment_request,
#             DATE(pr.transaction_date) AS pr_date,
#             pr.party AS pr_party,
#             pr.grand_total AS pr_total,
            
#             -- Payment Entries aggregated
#             COALESCE(
#                 (SELECT GROUP_CONCAT(DISTINCT pe2.name SEPARATOR ', ')
#                  FROM `tabPayment Entry Reference` per2
#                  JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent 
#                  WHERE per2.reference_name = po.name AND pe2.docstatus = 1
#                  GROUP BY per2.reference_name), 
#                 'None'
#             ) AS payment_entries,
            
#             COALESCE(
#                 (SELECT GROUP_CONCAT(DISTINCT DATE(pe2.posting_date) SEPARATOR ', ')
#                  FROM `tabPayment Entry Reference` per2
#                  JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent 
#                  WHERE per2.reference_name = po.name AND pe2.docstatus = 1
#                  GROUP BY per2.reference_name), 
#                 'None'
#             ) AS pe_dates,
            
#             COALESCE(
#                 (SELECT GROUP_CONCAT(DISTINCT pe2.reference_no SEPARATOR ', ')
#                  FROM `tabPayment Entry Reference` per2
#                  JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent 
#                  WHERE per2.reference_name = po.name AND pe2.docstatus = 1
#                  GROUP BY per2.reference_name), 
#                 'None'
#             ) AS cheque,
            
#             COALESCE(
#                 (SELECT SUM(pe2.paid_amount)
#                  FROM `tabPayment Entry Reference` per2
#                  JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent 
#                  WHERE per2.reference_name = po.name AND pe2.docstatus = 1
#                  GROUP BY per2.reference_name), 
#                 0
#             ) AS total_amount
        
#         FROM `tabMaterial Request` mr
#         LEFT JOIN `tabMaterial Request Item` mri
#             ON mri.parent = mr.name
#         LEFT JOIN `tabSupplier Quotation Item` sqi
#             ON sqi.material_request = mr.name
#         LEFT JOIN `tabSupplier Quotation` sq
#             ON sqi.parent = sq.name AND sq.docstatus = 1
#         LEFT JOIN `tabPurchase Order Item` poi
#             ON poi.material_request = mr.name
#         LEFT JOIN `tabPurchase Order` po
#             ON poi.parent = po.name AND po.docstatus = 1
#         LEFT JOIN `tabPayment Request` pr
#             ON pr.reference_name = po.name
        
#         WHERE mr.docstatus = 1  
#         GROUP BY mr.name, sq.name, po.name, pr.name
#         ORDER BY mr.transaction_date DESC
#     """
    
#     return frappe.db.sql(sql_query, as_dict=True)

# def get_summary_data(data):
#     total_mr = len(data)
#     total_sq = len([d for d in data if d.get('supplier_quotation') and d.get('supplier_quotation') != 'None'])
#     total_po = len([d for d in data if d.get('purchase_order') and d.get('purchase_order') != 'None'])
#     total_pr = len([d for d in data if d.get('payment_request') and d.get('payment_request') != 'None'])
    
#     total_po_amount = sum([float(d.get('po_total') or 0) for d in data])
#     total_pr_amount = sum([float(d.get('pr_total') or 0) for d in data])
    
#     return [
#         {"label": "Total MR", "value": total_mr, "datatype": "Int"},
#         {"label": "Total SQ", "value": total_sq, "datatype": "Int"},
#         {"label": "Total PO", "value": total_po, "datatype": "Int"},
#         {"label": "Total PR", "value": total_pr, "datatype": "Int"},
#         {"label": "Total PO Amount", "value": total_po_amount, "datatype": "Currency"},
#         {"label": "Total PR Amount", "value": total_pr_amount, "datatype": "Currency"}
#     ]