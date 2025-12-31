import frappe
from frappe import _

@frappe.whitelist()
def submit_leave_from_mobile(**kwargs):

    allowed_values = [
        "Yes (On Company)",
        "Yes (On Employee)",
        "No"
    ]

    ticket = kwargs.get("ticket")
    if ticket not in allowed_values:
        ticket = "No"

    doc = frappe.get_doc({
        "doctype": "Leave Application",
        "employee": kwargs.get("employee"),
        "leave_type": kwargs.get("leave_type"),
        "from_date": kwargs.get("from_date"),
        "to_date": kwargs.get("to_date"),
        "incharge_replacement": kwargs.get("incharge_replacement"),
        "ticket": ticket,
        "reason": kwargs.get("reason")
    })

    doc.insert(ignore_permissions=True)

    return {
        "message": "Leave Application created successfully",
        "name": doc.name,
        "workflow_state": getattr(doc, "workflow_state", "Open")
    }
