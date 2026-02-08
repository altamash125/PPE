# import frappe
# from frappe import _
# from frappe.utils import now, flt, cint
# import json

# @frappe.whitelist(allow_guest=False, methods=['POST'])
# def submit_employee_advance_from_mobile(**kwargs):
#     """
#     Mobile API to create and submit Employee Advance via Workflow
    
#     Accepts parameters as:
#     1. JSON Body (Content-Type: application/json)
#     2. Form Data (Content-Type: multipart/form-data)
#     3. URL Parameters
    
#     Required Parameters:
#     - employee: Employee ID
#     - advance_amount: Numeric amount
#     - purpose: Purpose description
#     - advance_account: From allowed list
#     - mode_of_payment: From allowed list
    
#     Optional:
#     - repay_unclaimed_amount_from_salary: 0 or 1 (default: 0)
#     - company: Company name (default: from employee)
#     - currency: Currency code (default: SAR)
#     - exchange_rate: Exchange rate (default: 1.0)
#     """
    
#     try:
#         # ===== PARAMETER EXTRACTION =====
#         # Initialize variables
#         employee = None
#         advance_amount = None
#         purpose = None
#         advance_account = None
#         mode_of_payment = None
#         repay_from_salary = 0
#         company = None
#         currency = "SAR"
#         exchange_rate = 1.0
        
#         # Method 1: Check if parameters are in kwargs (URL params or form-data)
#         if kwargs:
#             employee = kwargs.get("employee")
#             advance_amount = kwargs.get("advance_amount")
#             purpose = kwargs.get("purpose")
#             advance_account = kwargs.get("advance_account")
#             mode_of_payment = kwargs.get("mode_of_payment")
#             repay_from_salary = kwargs.get("repay_unclaimed_amount_from_salary", 0)
#             company = kwargs.get("company")
#             currency = kwargs.get("currency", "SAR")
#             exchange_rate = kwargs.get("exchange_rate", 1.0)
        
#         # Method 2: Check JSON request body
#         if frappe.request and frappe.request.data:
#             try:
#                 request_data = frappe.parse_json(frappe.request.get_data(as_text=True))
                
#                 # Only override if not already set from kwargs
#                 if request_data:
#                     employee = employee or request_data.get("employee")
#                     advance_amount = advance_amount or request_data.get("advance_amount")
#                     purpose = purpose or request_data.get("purpose")
#                     advance_account = advance_account or request_data.get("advance_account")
#                     mode_of_payment = mode_of_payment or request_data.get("mode_of_payment")
#                     repay_from_salary = repay_from_salary or request_data.get("repay_unclaimed_amount_from_salary", 0)
#                     company = company or request_data.get("company")
#                     currency = currency or request_data.get("currency", "SAR")
#                     exchange_rate = exchange_rate or request_data.get("exchange_rate", 1.0)
#             except:
#                 pass
        
#         # Method 3: Check form_dict for form-data
#         if frappe.form_dict:
#             form_data = frappe.form_dict
#             employee = employee or form_data.get("employee")
#             advance_amount = advance_amount or form_data.get("advance_amount")
#             purpose = purpose or form_data.get("purpose")
#             advance_account = advance_account or form_data.get("advance_account")
#             mode_of_payment = mode_of_payment or form_data.get("mode_of_payment")
#             repay_from_salary = repay_from_salary or form_data.get("repay_unclaimed_amount_from_salary", 0)
#             company = company or form_data.get("company")
#             currency = currency or form_data.get("currency", "SAR")
#             exchange_rate = exchange_rate or form_data.get("exchange_rate", 1.0)
        
#         # Log received parameters for debugging
#         frappe.logger().info(f"Employee Advance API Parameters: employee={employee}, amount={advance_amount}, purpose={purpose}")
        
#         # ===== VALIDATION =====
#         # Required fields validation with specific messages
#         validation_errors = []
        
#         if not employee:
#             validation_errors.append("employee")
#         if not advance_amount:
#             validation_errors.append("advance_amount")
#         if not purpose:
#             validation_errors.append("purpose")
#         if not advance_account:
#             validation_errors.append("advance_account")
#         if not mode_of_payment:
#             validation_errors.append("mode_of_payment")
        
#         if validation_errors:
#             frappe.throw(_("Missing required fields: {0}").format(", ".join(validation_errors)))
        
#         # Type validation for advance_amount
#         try:
#             advance_amount = flt(advance_amount)
#             if advance_amount <= 0:
#                 frappe.throw(_("Advance Amount must be greater than 0"))
#             if advance_amount > 1000000:  # Example: Set a reasonable maximum limit
#                 frappe.throw(_("Advance Amount cannot exceed 1,000,000"))
#         except ValueError:
#             frappe.throw(_("Advance Amount must be a valid number"))
        
#         # Validate employee exists
#         if not frappe.db.exists("Employee", employee):
#             frappe.throw(_("Employee {0} does not exist").format(employee))
        
#         # Get employee details
#         employee_doc = frappe.get_doc("Employee", employee)
        
#         # Use provided company or default to employee's company
#         if not company:
#             company = employee_doc.company
        
#         if not company:
#             frappe.throw(_("Company not specified and cannot be determined from employee"))
        
#         # Validate company exists
#         if not frappe.db.exists("Company", company):
#             frappe.throw(_("Company {0} does not exist").format(company))
        
#         # Validate advance account
#         allowed_accounts = [
#             "1310 - Debtors - PPE",
#             "1311 - Retention with Clients - PPE", 
#             "1610 - Employee Advances - PPE",
#             "1611 - Employees Petty cash - PPE"
#         ]
        
#         # Check if account exists in database
#         if not frappe.db.exists("Account", {"name": advance_account}):
#             frappe.throw(_("Account {0} does not exist").format(advance_account))
        
#         # Check if account is in allowed list
#         if advance_account not in allowed_accounts:
#             frappe.throw(_("Invalid Advance Account. Allowed accounts are: {0}").format(", ".join(allowed_accounts)))
        
#         # Validate mode of payment exists
#         if not frappe.db.exists("Mode of Payment", mode_of_payment):
#             frappe.throw(_("Mode of Payment {0} does not exist").format(mode_of_payment))
        
#         # Optional: Validate allowed modes
#         allowed_modes = ["Cash", "Bank Transfer", "Cheque", "Credit Card", "Bank Draft"]
#         if mode_of_payment not in allowed_modes:
#             frappe.logger().warning(f"Mode of Payment {mode_of_payment} is not in recommended list")
        
#         # Convert repay_from_salary to integer
#         repay_from_salary = cint(repay_from_salary)
#         if repay_from_salary not in [0, 1]:
#             repay_from_salary = 0
        
#         # Validate currency
#         if not frappe.db.exists("Currency", currency):
#             frappe.throw(_("Currency {0} does not exist").format(currency))
        
#         # Validate exchange rate
#         try:
#             exchange_rate = flt(exchange_rate)
#             if exchange_rate <= 0:
#                 frappe.throw(_("Exchange Rate must be greater than 0"))
#         except ValueError:
#             frappe.throw(_("Exchange Rate must be a valid number"))
        
#         # ===== PERMISSION CHECK =====
#         # Check if user has permission to create Employee Advance
#         if not frappe.has_permission("Employee Advance", "create", user=frappe.session.user):
#             frappe.throw(_("You don't have permission to create Employee Advance"), frappe.PermissionError)
        
#         # ===== CREATE DOCUMENT =====
#         doc_data = {
#             "doctype": "Employee Advance",
#             "employee": employee,
#             "advance_amount": advance_amount,
#             "purpose": purpose,
#             "advance_account": advance_account,
#             "mode_of_payment": mode_of_payment,
#             "repay_unclaimed_amount_from_salary": repay_from_salary,
#             "company": company,
#             "currency": currency,
#             "exchange_rate": exchange_rate,
#             "posting_date": now(),
#             "remarks": f"Created via Mobile API by {frappe.session.user}"
#         }
        
#         # Create document
#         doc = frappe.get_doc(doc_data)
#         doc.insert(ignore_permissions=False)  # Respect permissions
        
#         # ===== WORKFLOW SUBMISSION =====
#         workflow_applied = False
#         submission_successful = False
        
#         try:
#             # Check if workflow exists
#             workflow = frappe.get_all("Workflow", 
#                 filters={
#                     "document_type": "Employee Advance", 
#                     "is_active": 1,
#                     "workflow_state_field": "workflow_state"
#                 },
#                 limit=1)
            
#             if workflow:
#                 # Apply workflow transition
#                 frappe.model.workflow.apply_workflow(doc, "Submit")
#                 workflow_applied = True
#                 submission_successful = True
#                 frappe.db.commit()
#             else:
#                 # If no workflow, submit normally
#                 doc.submit()
#                 submission_successful = True
#                 frappe.db.commit()
                
#         except frappe.exceptions.DocstatusTransitionError as e:
#             # Document cannot be submitted (might be in draft due to workflow rules)
#             frappe.log_error(
#                 title="Employee Advance Workflow Transition Error",
#                 message=f"Document {doc.name} could not be submitted via workflow: {str(e)}"
#             )
#             # Document remains in draft - this is acceptable
#             frappe.db.rollback()
#         except Exception as e:
#             frappe.log_error(
#                 title="Employee Advance Submission Error",
#                 message=f"Error submitting document {doc.name}: {str(e)}"
#             )
#             frappe.db.rollback()
#             # Don't throw error - return draft status
        
#         # Reload to get latest status
#         doc.reload()
        
#         # ===== LOG ACTIVITY =====
#         frappe.logger().info(
#             f"Employee Advance {doc.name} created via API by {frappe.session.user}. "
#             f"Status: {doc.docstatus}, Workflow State: {doc.get('workflow_state', 'Draft')}"
#         )
        
#         # ===== PREPARE RESPONSE =====
#         response = {
#             "success": True,
#             "message": _("Employee Advance created successfully"),
#             "data": {
#                 "name": doc.name,
#                 "docstatus": doc.docstatus,
#                 "status": "Submitted" if doc.docstatus == 1 else "Draft",
#                 "workflow_state": doc.get("workflow_state", "Draft"),
#                 "workflow_applied": workflow_applied,
#                 "submission_successful": submission_successful,
#                 "employee": doc.employee,
#                 "employee_name": doc.employee_name,
#                 "advance_amount": doc.advance_amount,
#                 "currency": doc.currency,
#                 "purpose": doc.purpose,
#                 "company": doc.company,
#                 "posting_date": str(doc.posting_date) if doc.posting_date else None,
#                 "repay_unclaimed_amount_from_salary": doc.repay_unclaimed_amount_from_salary,
#                 "creation": str(doc.creation) if doc.creation else None
#             }
#         }
        
#         return response
        
#     except frappe.exceptions.ValidationError as e:
#         # Handle validation errors
#         frappe.log_error(
#             title="Employee Advance API Validation Error",
#             message=f"Validation Error: {str(e)}\nParameters: {kwargs}\nUser: {frappe.session.user}"
#         )
#         frappe.db.rollback()
        
#         return {
#             "success": False,
#             "message": str(e),
#             "error": "VALIDATION_ERROR",
#             "error_details": frappe.get_traceback()
#         }
        
#     except frappe.exceptions.PermissionError as e:
#         # Handle permission errors
#         frappe.log_error(
#             title="Employee Advance API Permission Error",
#             message=f"Permission Error: {str(e)}\nUser: {frappe.session.user}"
#         )
#         frappe.db.rollback()
        
#         return {
#             "success": False,
#             "message": str(e),
#             "error": "PERMISSION_ERROR"
#         }
        
#     except Exception as e:
#         # Handle unexpected errors
#         error_message = f"Unexpected error: {str(e)}\nTraceback: {frappe.get_traceback()}"
#         frappe.log_error(
#             title="Employee Advance API Unexpected Error",
#             message=error_message
#         )
#         frappe.db.rollback()
        
#         return {
#             "success": False,
#             "message": _("An internal error occurred while processing your request"),
#             "error": "INTERNAL_SERVER_ERROR",
#             "error_id": frappe.generate_hash(length=8)  # For support reference
#         }

import frappe
from frappe import _
from frappe.utils import now, flt, cint
import json
import re

@frappe.whitelist(allow_guest=False, methods=['POST'])
def submit_employee_advance_from_mobile(**kwargs):
    """
    Mobile API to create and submit Employee Advance via Workflow
    """
    
    try:
        # ===== PARAMETER EXTRACTION =====
        employee = None
        advance_amount = None
        purpose = None
        advance_account = None
        mode_of_payment = None
        repay_from_salary = 0
        
        # Try multiple methods to get parameters
        # 1. From JSON body
        if frappe.request and frappe.request.data:
            try:
                data = frappe.parse_json(frappe.request.get_data(as_text=True))
                if data:
                    employee = data.get("employee")
                    advance_amount = data.get("advance_amount")
                    purpose = data.get("purpose")
                    advance_account = data.get("advance_account")
                    mode_of_payment = data.get("mode_of_payment")
                    repay_from_salary = data.get("repay_unclaimed_amount_from_salary", 0)
            except:
                pass
        
        # 2. From form-data or kwargs (overwrite only if not already set)
        if not employee:
            employee = kwargs.get("employee")
        if not advance_amount:
            advance_amount = kwargs.get("advance_amount")
        if not purpose:
            purpose = kwargs.get("purpose")
        if not advance_account:
            advance_account = kwargs.get("advance_account")
        if not mode_of_payment:
            mode_of_payment = kwargs.get("mode_of_payment")
        if not repay_from_salary:
            repay_from_salary = kwargs.get("repay_unclaimed_amount_from_salary", 0)
        
        # ===== VALIDATION =====
        # Log the received parameters for debugging
        frappe.logger().info(f"""
            API Parameters Received:
            - employee: {employee}
            - advance_amount: {advance_amount}
            - purpose: {purpose}
            - advance_account: {advance_account}
            - mode_of_payment: {mode_of_payment}
            - repay_from_salary: {repay_from_salary}
        """)
        
        # Required fields validation
        if not all([employee, advance_amount, purpose, advance_account, mode_of_payment]):
            frappe.throw(_("Missing required fields. Received: employee={0}, amount={1}, purpose={2}, account={3}, mode={4}").format(
                employee, advance_amount, purpose, advance_account, mode_of_payment
            ))
        
        # ===== EMPLOYEE VALIDATION (IMPROVED) =====
        employee_exists = False
        actual_employee_id = None
        
        # Method 1: Direct check
        if frappe.db.exists("Employee", employee):
            employee_exists = True
            actual_employee_id = employee
        else:
            # Method 2: Try to find by employee_number or other fields
            # Check if it's a numeric ID without prefix
            numeric_match = re.search(r'(\d+)', str(employee))
            if numeric_match:
                numeric_id = numeric_match.group(1)
                
                # Try different patterns
                patterns_to_try = [
                    numeric_id,  # "00152"
                    str(int(numeric_id)),  # "152" (without leading zeros)
                    f"HR-EMP-{numeric_id}",  # "HR-EMP-00152"
                    f"HR-EMP-{str(int(numeric_id))}",  # "HR-EMP-152"
                    f"EMP{numeric_id}",  # "EMP00152"
                    f"EMP{str(int(numeric_id))}",  # "EMP152"
                ]
                
                for pattern in patterns_to_try:
                    if frappe.db.exists("Employee", pattern):
                        employee_exists = True
                        actual_employee_id = pattern
                        frappe.logger().info(f"Found employee with pattern {pattern} for input {employee}")
                        break
            
            # Method 3: Search by employee name or custom field
            if not employee_exists:
                # Search in Employee doctype
                employees = frappe.get_all("Employee", 
                    filters={"employee_name": ["like", f"%{employee}%"]},
                    fields=["name", "employee_name", "employee_number"],
                    limit=5)
                
                if employees:
                    if len(employees) == 1:
                        # If only one match, use it
                        employee_exists = True
                        actual_employee_id = employees[0].name
                        frappe.logger().info(f"Found employee by name: {actual_employee_id}")
                    else:
                        # Multiple matches found
                        frappe.throw(_("Multiple employees found for '{0}'. Please use exact Employee ID. Found: {1}").format(
                            employee, 
                            ", ".join([f"{e.name} ({e.employee_name})" for e in employees])
                        ))
        
        if not employee_exists:
            # Get list of actual employees for debugging
            all_employees = frappe.get_all("Employee", 
                fields=["name", "employee_name", "employee_number"],
                filters={"status": "Active"},
                order_by="name",
                limit=20)
            
            frappe.logger().error(f"Employee not found: {employee}. Available employees: {all_employees}")
            
            error_msg = _("Employee '{0}' does not exist. ").format(employee)
            if all_employees:
                error_msg += _("Available active employees: {0}").format(
                    ", ".join([f"{e['name']} ({e['employee_name']})" for e in all_employees])
                )
            
            frappe.throw(error_msg)
        
        # Now use the actual employee ID
        employee = actual_employee_id
        
        # ===== REST OF VALIDATION =====
        try:
            advance_amount = flt(advance_amount)
            if advance_amount <= 0:
                frappe.throw(_("Advance Amount must be greater than 0"))
        except ValueError:
            frappe.throw(_("Advance Amount must be a valid number"))
        
        # Get employee details
        employee_doc = frappe.get_doc("Employee", employee)
        company = employee_doc.company
        
        # Validate advance account
        allowed_accounts = [
            "1310 - Debtors - PPE",
            "1311 - Retention with Clients - PPE", 
            "1610 - Employee Advances - PPE",
            "1611 - Employees Petty cash - PPE"
        ]
        
        if not frappe.db.exists("Account", advance_account):
            frappe.throw(_("Account '{0}' does not exist. Available accounts: {1}").format(
                advance_account,
                ", ".join(allowed_accounts)
            ))
        
        if advance_account not in allowed_accounts:
            frappe.throw(_("Invalid Advance Account '{0}'. Allowed: {1}").format(
                advance_account, 
                ", ".join(allowed_accounts)
            ))
        
        # Validate mode of payment
        if not frappe.db.exists("Mode of Payment", mode_of_payment):
            # List available modes
            available_modes = frappe.get_all("Mode of Payment", 
                fields=["name"],
                filters={"enabled": 1})
            
            frappe.throw(_("Mode of Payment '{0}' does not exist. Available: {1}").format(
                mode_of_payment,
                ", ".join([m["name"] for m in available_modes])
            ))
        
        repay_from_salary = 1 if str(repay_from_salary).lower() in ["1", "true", "yes"] else 0
        
        # ===== CREATE DOCUMENT =====
        doc = frappe.get_doc({
            "doctype": "Employee Advance",
            "employee": employee,
            "employee_name": employee_doc.employee_name,
            "advance_amount": advance_amount,
            "purpose": purpose,
            "advance_account": advance_account,
            "mode_of_payment": mode_of_payment,
            "repay_unclaimed_amount_from_salary": repay_from_salary,
            "company": company,
            "currency": "SAR",
            "exchange_rate": 1.0,
            "posting_date": now(),
        })
        
        doc.insert()
        
        # Try to submit via workflow
        workflow_applied = False
        try:
            workflow = frappe.get_all("Workflow", 
                filters={"document_type": "Employee Advance", "is_active": 1},
                limit=1)
            
            if workflow:
                frappe.model.workflow.apply_workflow(doc, "Submit")
                workflow_applied = True
            else:
                doc.submit()
        except Exception as e:
            frappe.log_error(f"Workflow submission error: {str(e)}", "Employee Advance API")
            # Document remains as draft - this is acceptable
        
        doc.reload()
        
        return {
            "success": True,
            "message": _("Employee Advance created successfully"),
            "data": {
                "name": doc.name,
                "docstatus": doc.docstatus,
                "workflow_state": doc.get("workflow_state", "Draft"),
                "employee": doc.employee,
                "employee_name": doc.employee_name,
                "advance_amount": doc.advance_amount,
                "company": doc.company
            }
        }
        
    except frappe.exceptions.ValidationError as e:
        frappe.log_error(str(e), "Employee Advance API Validation")
        return {
            "success": False,
            "message": str(e),
            "error": "VALIDATION_ERROR"
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Employee Advance API Error")
        return {
            "success": False,
            "message": _("An error occurred: {0}").format(str(e)),
            "error": "SERVER_ERROR"
        }