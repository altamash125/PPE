import frappe
from frappe import _

@frappe.whitelist()
def get_leave_balance_for_employee(employee):
    """
    Returns Annual Leave and Sick Leave balance for an employee
    Ignores allocation period, uses case-insensitive leave type matching
    """

    if not employee:
        frappe.throw(_("Employee is required"))

    from frappe.utils import date_diff

    leave_types = ["Annual leave", "Sick Leave"]  # match exactly ERPNext spelling
    balances = {}

    for leave_type in leave_types:
        # Get all allocations for this leave type (submitted)
        allocations = frappe.get_list(
            "Leave Allocation",
            filters={"employee": employee, "docstatus": 1},
            fields=["leave_type", "total_leaves_allocated"]
        )

        total_allocated = sum(
            alloc.total_leaves_allocated 
            for alloc in allocations
            if alloc.leave_type.lower() == leave_type.lower()
        )

        # Get approved leaves
        leaves = frappe.get_list(
            "Leave Application",
            filters={
                "employee": employee,
                "status": "Approved",
                "docstatus": 1
            },
            fields=["leave_type", "from_date", "to_date", "half_day"]
        )

        total_taken = 0
        for l in leaves:
            if l.leave_type.lower() != leave_type.lower():
                continue
            days = date_diff(l.to_date, l.from_date) + 1
            if l.half_day:
                days -= 0.5
            total_taken += days

        balances[leave_type] = total_allocated - total_taken

    return {
        "employee": employee,
        "leave_balance": {
            "annual_leave": balances.get("Annual leave", 0),
            "sick_leave": balances.get("Sick Leave", 0)
        }
    }
