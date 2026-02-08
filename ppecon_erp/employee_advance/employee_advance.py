import frappe
from frappe import _

@frappe.whitelist()
def submit_employee_advance_from_mobile(**kwargs):
    """
    Mobile API to create and submit Employee Advance via Workflow
    """

    # Mandatory fields
    employee = kwargs.get("employee")
    advance_amount = kwargs.get("advance_amount")
    purpose = kwargs.get("purpose")

    if not employee:
        frappe.throw(_("Employee is required"))
    if not advance_amount:
        frappe.throw(_("Advance Amount is required"))
    if not purpose:
        frappe.throw(_("Purpose is required"))

    # Allowed Advance Account options
    allowed_advance_accounts = [
        "1310 - Debtors - PPE",
        "1311 - Retention with Clients - PPE",
        "1610 - Employee Advances - PPE",
        "1611 - Employees Petty cash - PPE"
    ]

    advance_account = kwargs.get("advance_account")
    if advance_account not in allowed_advance_accounts:
        frappe.throw(_("Invalid Advance Account"))

    # Allowed Mode of Payment options
    allowed_mode_of_payment = [
        "Cash",
        "Bank Transfer",
        "Cheque",
        "Credit Card",
        "Bank Draft"
    ]

    mode_of_payment = kwargs.get("mode_of_payment")
    if mode_of_payment not in allowed_mode_of_payment:
        frappe.throw(_("Invalid Mode of Payment"))

    # Checkbox (0 or 1)
    repay_from_salary = kwargs.get("repay_unclaimed_amount_from_salary", 0)
    repay_from_salary = 1 if str(repay_from_salary) in ["1", "true", "True"] else 0

    # Create Employee Advance document
    doc = frappe.get_doc({
        "doctype": "Employee Advance",
        "employee": employee,
        "advance_amount": advance_amount,
        "purpose": purpose,
        "advance_account": advance_account,
        "mode_of_payment": mode_of_payment,
        "repay_unclaimed_amount_from_salary": repay_from_salary
    })

    # 1️⃣ Draft Save
    doc.insert(ignore_permissions=True)

    # 2️⃣ Workflow Submit
    frappe.model.workflow.apply_workflow(
        doc,
        "Submit"   # MUST match workflow action name exactly
    )

    doc.reload()

    return {
        "message": "Employee Advance Submitted Successfully",
        "name": doc.name,
        "docstatus": doc.docstatus,
        "workflow_state": doc.workflow_state,
        "repay_unclaimed_amount_from_salary": doc.repay_unclaimed_amount_from_salary
    }
