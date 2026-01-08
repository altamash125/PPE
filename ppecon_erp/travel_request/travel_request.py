import frappe
from frappe import _

@frappe.whitelist()
def submit_travel_request_from_mobile(**kwargs):
    """
    Mobile API to create and submit a Travel Request.
    Expected kwargs:
        - employee
        - from_date
        - to_date
        - purpose
        - travel_mode
        - estimated_cost
        - description (optional)
        - ticket_required (Yes/No)
        - any other travel request fields as needed
    """

    # Allowed ticket_required values
    allowed_ticket_values = ["Yes", "No"]
    ticket_required = kwargs.get("ticket_required")
    if ticket_required not in allowed_ticket_values:
        ticket_required = "No"
 
    # Prepare Travel Request document
    doc = frappe.get_doc({
        "doctype": "Travel Request",
        "employee": kwargs.get("employee"),
        "from_date": kwargs.get("from_date"),
        "to_date": kwargs.get("to_date"),
        "purpose": kwargs.get("purpose"),
        "travel_mode": kwargs.get("travel_mode"),
        "estimated_cost": kwargs.get("estimated_cost"),
        "ticket_required": ticket_required,
        "description": kwargs.get("description")
    })

    # 1️Create Draft (insert the document)
    doc.insert(ignore_permissions=True)

    # 2️Submit via Workflow (assuming workflow action is named "Submit")
    frappe.model.workflow.apply_workflow(
        doc,
        "Submit"  # Must exactly match the workflow action name
    )

    doc.reload()

    return {
        "message": "Travel Request Submitted",
        "name": doc.name,
        "workflow_state": doc.workflow_state,
        "description": doc.description  # Optional: return description
    }


@frappe.whitelist()
def trigger_travel_request_workflow(docname, action):
    """
    Trigger a workflow action on a Travel Request.
    Args:
        docname (str): The name (ID) of the Travel Request document
        action (str): The workflow action to trigger (e.g., 'Approve', 'Reject', etc.)
    """

    doc = frappe.get_doc("Travel Request", docname)
    frappe.model.workflow.apply_workflow(doc, action)
    doc.reload()

    return {
        "message": _("Action '{0}' performed on Travel Request '{1}'").format(action, docname),
        "workflow_state": doc.workflow_state
    }

