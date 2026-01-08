# import frappe
# from frappe import _
# from frappe.utils import flt, now
# import json

# @frappe.whitelist()
# def update_items(mr_name=None, items=None):

#     # -------------------------------
#     # 🔐 Basic validations
#     # -------------------------------
#     if not mr_name:
#         frappe.throw(_("Material Request name is missing"))

#     if "Purchase Manager" not in frappe.get_roles():
#         frappe.throw(_("Only Purchase Manager can update items"))

#     if not items:
#         frappe.throw(_("No items received to update"))

#     # -------------------------------
#     # 🧠 SAFE JSON parsing (NO ERROR)
#     # -------------------------------
#     if isinstance(items, str):
#         try:
#             items = json.loads(items)
#         except Exception:
#             frappe.throw(_("Invalid items data received"))

#     if not isinstance(items, list):
#         frappe.throw(_("Items must be a list"))

#     mr = frappe.get_doc("Material Request", mr_name)

#     if mr.docstatus != 1:
#         frappe.throw(_("Only Approved Material Requests can be updated"))

#     # -------------------------------
#     # 🔄 Update rows
#     # -------------------------------
#     updated = 0

#     for row in items:
#         row_id = row.get("name")
#         if not row_id:
#             continue

#         frappe.db.set_value(
#             "Material Request Item",
#             row_id,
#             {
#                 "qty": flt(row.get("qty")),
#                 "uom": row.get("uom"),
#                 "schedule_date": row.get("schedule_date"),
#                 "modified": now(),
#                 "modified_by": frappe.session.user
#             },
#             update_modified=False
#         )
#         updated += 1

#     frappe.clear_document_cache("Material Request", mr_name)
#     frappe.db.commit()

#     return {
#         "updated_rows": updated,
#         "status": "success"
#     }


# import frappe
# from frappe import _
# from frappe.utils import flt, now

# @frappe.whitelist()
# def update_items(mr_name, items):
#     """
#     Update Qty, UOM, and Schedule Date in Approved Material Request
#     (PO-style Update Items)
#     """

#     # -------------------------------
#     # 🔐 Security checks
#     # -------------------------------
#     if "Purchase Manager" not in frappe.get_roles():
#         frappe.throw(_("Only Purchase Manager can update items"))

#     if not mr_name:
#         frappe.throw(_("Material Request name is required"))

#     # -------------------------------
#     # 🧠 Parse items safely
#     # -------------------------------
#     if isinstance(items, str):
#         items = frappe.parse_json(items)

#     if not items:
#         frappe.throw(_("No items to update"))

#     mr = frappe.get_doc("Material Request", mr_name)

#     if mr.docstatus != 1:
#         frappe.throw(_("Only Approved Material Requests can be updated"))

#     # -------------------------------
#     # 🔄 Update items directly
#     # -------------------------------
#     updated_rows = 0

#     for row in items:
#         row_id = row.get("name")
#         if not row_id:
#             continue

#         frappe.db.set_value(
#             "Material Request Item",
#             row_id,
#             {
#                 "qty": flt(row.get("qty")),
#                 "uom": row.get("uom"),
#                 "schedule_date": row.get("schedule_date"),
#                 "modified": now(),
#                 "modified_by": frappe.session.user
#             },
#             update_modified=False
#         )
#         updated_rows += 1

#     # -------------------------------
#     # 🧹 Clear cache + commit once
#     # -------------------------------
#     frappe.clear_document_cache("Material Request", mr_name)
#     frappe.db.commit()

#     # -------------------------------
#     # 🧾 Optional audit log
#     # -------------------------------
#     frappe.logger().info(
#         f"Material Request {mr_name} items updated by {frappe.session.user}"
#     )

#     return {
#         "updated_rows": updated_rows,
#         "message": "Items updated successfully"
#     }

# import frappe
# from frappe import _
# from frappe.utils import flt

# @frappe.whitelist()
# def update_items(mr_name, items):
#     """
#     Directly update Qty, UOM, and Date in the database
#     """

#     if isinstance(items, str):
#         items = frappe.parse_json(items)

#     for updated_item in items:
#         row_id = updated_item.get("name")
        
#         if row_id:
#             # Updating database directly bypasses "Not allowed to change" validation
#             frappe.db.set_value("Material Request Item", row_id, {
#                 "qty": flt(updated_item.get("qty")),
#                 "uom": updated_item.get("uom"), # Update UOM
#                 "schedule_date": updated_item.get("schedule_date")
#             }, update_modified=True)

#     # Refresh the document cache
#     frappe.clear_document_cache("Material Request", mr_name)
    
#     return True

