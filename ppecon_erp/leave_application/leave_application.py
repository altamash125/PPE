import frappe
from frappe import _

@frappe.whitelist()
def submit_leave_from_mobile(data):
    data = frappe.parse_json(data)

    if not frappe.db.exists("Employee", data.get("employee")):
        frappe.throw("Employee does not exist")

    if not frappe.db.exists("Leave Type", data.get("leave_type")):
        frappe.throw("Leave Type does not exist")

    doc = frappe.get_doc({
        "doctype": "Leave Application",
        "employee": data.get("employee"),
        "leave_type": data.get("leave_type"),
        "from_date": data.get("from_date"),
        "to_date": data.get("to_date"),
        "incharge_replacement": data.get("incharge_replacement"),
        "custom_ticket": data.get("custom_ticket"),
        "description": data.get("reason")
    })

    doc.insert()
    doc.submit()

    return {
        "status": "success",
        "leave_application": doc.name,
        "workflow_state": doc.workflow_state
    }


# @frappe.whitelist()
# def submit_leave_from_mobile(data):
#     """
#     Mobile Submit API (ERPNext UI Equivalent)
#     """

#     if isinstance(data, str):
#         data = frappe.parse_json(data)

#     # REQUIRED fields (ERP UI)
#     required_fields = [
#         "employee",
#         "leave_type",
#         "from_date",
#         "to_date",
#         "incharge_replacement",
#         "custom_ticket"
#     ]

#     for field in required_fields:
#         if not data.get(field):
#             frappe.throw(_(f"{field.replace('_', ' ').title()} is required"))

#     # Create Leave Application
#     leave = frappe.new_doc("Leave Application")
#     leave.employee = data["employee"]
#     leave.leave_type = data["leave_type"]
#     leave.from_date = data["from_date"]
#     leave.to_date = data["to_date"]

#     #Optional field
#     leave.description = data.get("reason")

#     # ERP form mandatory fields
#     leave.incharge_replacement = data["incharge_replacement"]
#     leave.custom_ticket = data["custom_ticket"]

#     # Save
#     leave.insert(ignore_permissions=True)

#     # 2️⃣ Submit → triggers workflow
#     leave.submit()
#     leave.reload()

#     return {
#         "message": "Leave submitted successfully",
#         "leave_id": leave.name,
#         "docstatus": leave.docstatus,
#         "workflow_state": leave.workflow_state,
#         "status": leave.status
#     }
