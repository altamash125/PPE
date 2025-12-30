import frappe
from frappe import _

@frappe.whitelist()
def submit_leave_from_mobile(**kwargs):
    employee = kwargs.get("employee")
    leave_type = kwargs.get("leave_type")
    from_date = kwargs.get("from_date")
    to_date = kwargs.get("to_date")
    incharge_replacement = kwargs.get("incharge_replacement")
    custom_ticket = kwargs.get("custom_ticket") or "No"  # Correct field name!
    reason = kwargs.get("reason")

    # create Leave Application in draft/open state
    doc = frappe.get_doc({
        "doctype": "Leave Application",
        "employee": employee,
        "leave_type": leave_type,
        "from_date": from_date,
        "to_date": to_date,
        "incharge_replacement": incharge_replacement,
        "custom_ticket": custom_ticket,  # fixed here
        "reason": reason,
        "status": "Open"  # draft state
    })
    doc.insert(ignore_permissions=True)

    # workflow info
    workflow_state = getattr(doc, "workflow_state", "Open")
    actions = getattr(doc, "get_workflow_actions", lambda: [])()

    return {
        "message": "Leave Application created successfully",
        "name": doc.name,
        "workflow_state": workflow_state,
        "available_actions": actions
    }
