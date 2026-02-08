import frappe
from frappe import _

@frappe.whitelist()
def submit_employee_advance_from_mobile(**kwargs):
    """
    Mobile API to create and submit Employee Advance via Workflow.
    Works similar to Leave Application API.
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

    # Check if employee exists
    if not frappe.db.exists("Employee", employee):
        frappe.throw(_("Employee {0} does not exist").format(employee))

    # Allowed Advance Accounts
    allowed_advance_accounts = [
        "1310 - Debtors - PPE",
        "1311 - Retention with Clients - PPE",
        "1610 - Employee Advances - PPE",
        "1611 - Employees Petty cash - PPE"
    ]
    advance_account = kwargs.get("advance_account")
    if advance_account not in allowed_advance_accounts:
        frappe.throw(_("Invalid Advance Account"))

    # Allowed Mode of Payment
    allowed_modes = ["Cash", "Bank Transfer", "Cheque", "Credit Card", "Bank Draft"]
    mode_of_payment = kwargs.get("mode_of_payment")
    if mode_of_payment not in allowed_modes:
        frappe.throw(_("Invalid Mode of Payment"))

    # Checkbox for repayment from salary
    repay_from_salary = kwargs.get("repay_unclaimed_amount_from_salary", 0)
    repay_from_salary = 1 if str(repay_from_salary).lower() in ["1", "true"] else 0

    # Create Employee Advance document (Draft)
    doc = frappe.get_doc({
        "doctype": "Employee Advance",
        "employee": employee,
        "advance_amount": advance_amount,
        "purpose": purpose,
        "advance_account": advance_account,
        "mode_of_payment": mode_of_payment,
        "repay_unclaimed_amount_from_salary": repay_from_salary,
        "exchange_rate": 1.0,  # Required to avoid "Exchange Rate cannot be zero"
        "currency": "SAR",     # Set company currency
        "company": "Pioneer Projects Executer Company"
    })

    # 1️⃣ Draft save
    doc.insert(ignore_permissions=True)

    # 2️⃣ Submit via Workflow
    frappe.model.workflow.apply_workflow(
        doc,
        "Submit"  # Must exactly match the workflow action in Employee Advance workflow
    )

    doc.reload()

    return {
        "message": _("Employee Advance Submitted Successfully"),
        "name": doc.name,
        "docstatus": doc.docstatus,
        "workflow_state": doc.workflow_state,
        "repay_unclaimed_amount_from_salary": doc.repay_unclaimed_amount_from_salary
    }
