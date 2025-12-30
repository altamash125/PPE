import frappe
from frappe import _

@frappe.whitelist()
def submit_leave_from_mobile(**kwargs):
    # now kwargs will contain all fields from your data dict
    employee = kwargs.get("employee")
    leave_type = kwargs.get("leave_type")
    from_date = kwargs.get("from_date")
    to_date = kwargs.get("to_date")
    incharge_replacement = kwargs.get("incharge_replacement")
    custom_ticket_ = kwargs.get("custom_ticket") or "No"  # mandatory field
    reason = kwargs.get("reason")

    # create and submit Leave Application
    doc = frappe.get_doc({
        "doctype": "Leave Application",
        "employee": employee,
        "leave_type": leave_type,
        "from_date": from_date,
        "to_date": to_date,
        "incharge_replacement": incharge_replacement,
        "custom_ticket_": custom_ticket_,
        "reason": reason,
        "status": "Open"
    })
    doc.insert(ignore_permissions=True)
    doc.submit()

    # workflow info
    workflow_state = getattr(doc, "workflow_state", "Open")
    actions = getattr(doc, "get_workflow_actions", lambda: [])()

    return {
        "message": "Leave submitted successfully",
        "name": doc.name,
        "workflow_state": workflow_state,
        "available_actions": actions
    }


