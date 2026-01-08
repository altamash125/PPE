
import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def update_items(mr_name, items):
    """
    Directly update Qty, UOM, and Date in the database
    """
    
    if isinstance(items, str):
        items = frappe.parse_json(items)

    for updated_item in items:
        row_id = updated_item.get("name")
        
        if row_id:
            # Updating database directly bypasses "Not allowed to change" validation
            frappe.db.set_value("Material Request Item", row_id, {
                "qty": flt(updated_item.get("qty")),
                "uom": updated_item.get("uom"), # Update UOM
                "schedule_date": updated_item.get("schedule_date")
            }, update_modified=True)

    # Refresh the document cache
    frappe.clear_document_cache("Material Request", mr_name)
    
    return True

