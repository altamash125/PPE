import frappe
from frappe import _
from frappe.utils import now, flt, cint

@frappe.whitelist(allow_guest=False)
def submit_employee_advance_from_mobile(**kwargs):
    """
    Mobile API to create and submit Employee Advance via Workflow
    
    Required Parameters:
    - employee: Employee ID
    - advance_amount: Numeric amount
    - purpose: Purpose description
    - advance_account: From allowed list
    - mode_of_payment: From allowed list
    
    Optional:
    - repay_unclaimed_amount_from_salary: 0 or 1 (default: 0)
    """
    
    try:
        # ===== VALIDATION =====
        employee = kwargs.get("employee")
        advance_amount = kwargs.get("advance_amount")
        purpose = kwargs.get("purpose")
        advance_account = kwargs.get("advance_account")
        mode_of_payment = kwargs.get("mode_of_payment")
        repay_from_salary = kwargs.get("repay_unclaimed_amount_from_salary", 0)
        
        # Required fields validation
        if not all([employee, advance_amount, purpose, advance_account, mode_of_payment]):
            frappe.throw(_("Missing required fields: employee, advance_amount, purpose, advance_account, mode_of_payment"))
        
        # Type validation
        try:
            advance_amount = flt(advance_amount)
            if advance_amount <= 0:
                frappe.throw(_("Advance Amount must be greater than 0"))
        except ValueError:
            frappe.throw(_("Advance Amount must be a valid number"))
        
        # Validate employee exists
        if not frappe.db.exists("Employee", employee):
            frappe.throw(_("Employee {0} does not exist").format(employee))
        
        # Get employee details to determine company
        employee_doc = frappe.get_doc("Employee", employee)
        company = employee_doc.company
        
        # Validate advance account
        allowed_accounts = [
            "1310 - Debtors - PPE",
            "1311 - Retention with Clients - PPE", 
            "1610 - Employee Advances - PPE",
            "1611 - Employees Petty cash - PPE"
        ]
        
        # Check if account exists in database and is in allowed list
        if not frappe.db.exists("Account", advance_account):
            frappe.throw(_("Account {0} does not exist").format(advance_account))
        
        if advance_account not in allowed_accounts:
            frappe.throw(_("Invalid Advance Account. Allowed: {0}").format(", ".join(allowed_accounts)))
        
        # Validate mode of payment
        allowed_modes = ["Cash", "Bank Transfer", "Cheque", "Credit Card", "Bank Draft"]
        if not frappe.db.exists("Mode of Payment", mode_of_payment):
            frappe.throw(_("Mode of Payment {0} does not exist").format(mode_of_payment))
        
        if mode_of_payment not in allowed_modes:
            frappe.throw(_("Invalid Mode of Payment. Allowed: {0}").format(", ".join(allowed_modes)))
        
        # Convert repay_from_salary to integer (0 or 1)
        repay_from_salary = cint(repay_from_salary)
        if repay_from_salary not in [0, 1]:
            repay_from_salary = 0
        
        # ===== CREATE DOCUMENT =====
        doc = frappe.get_doc({
            "doctype": "Employee Advance",
            "employee": employee,
            "advance_amount": advance_amount,
            "purpose": purpose,
            "advance_account": advance_account,
            "mode_of_payment": mode_of_payment,
            "repay_unclaimed_amount_from_salary": repay_from_salary,
            "company": company,
            "currency": "SAR",  # Consider making this configurable
            "exchange_rate": 1.0,
            "posting_date": now()  # Add posting date
        })
        
        # Insert with proper permissions (user should have create rights)
        doc.insert()
        
        # ===== WORKFLOW SUBMISSION =====
        workflow_applied = False
        try:
            # Check if workflow exists for this doctype
            workflow = frappe.get_all("Workflow", 
                filters={"document_type": "Employee Advance", "is_active": 1},
                limit=1)
            
            if workflow:
                frappe.model.workflow.apply_workflow(doc, "Submit")
                workflow_applied = True
            else:
                # If no workflow, submit normally
                doc.submit()
        except frappe.exceptions.DocstatusTransitionError as e:
            # Handle specific workflow transition errors
            frappe.log_error(
                title="Workflow Transition Error",
                message=f"Error in Employee Advance workflow: {str(e)}\nDoc: {doc.name}"
            )
            # Document is saved as draft
            pass
        except Exception as e:
            frappe.log_error(
                title="Employee Advance Submission Error",
                message=f"Error: {str(e)}\nDoc: {doc.name}"
            )
            frappe.throw(_("Error submitting document: {0}").format(str(e)))
        
        doc.reload()
        
        # ===== RESPONSE =====
        return {
            "success": True,
            "message": _("Employee Advance {0} created successfully").format(doc.name),
            "data": {
                "name": doc.name,
                "docstatus": doc.docstatus,
                "workflow_state": doc.get("workflow_state", "Draft"),
                "workflow_applied": workflow_applied,
                "repay_unclaimed_amount_from_salary": doc.repay_unclaimed_amount_from_salary,
                "employee": doc.employee,
                "advance_amount": doc.advance_amount
            }
        }
        
    except frappe.exceptions.ValidationError as e:
        # Handle validation errors
        frappe.log_error(title="Employee Advance Validation Error", message=str(e))
        return {
            "success": False,
            "message": str(e),
            "error": "VALIDATION_ERROR"
        }
    except Exception as e:
        # Handle unexpected errors
        frappe.log_error(title="Employee Advance API Error", message=f"Args: {kwargs}\nError: {str(e)}")
        return {
            "success": False,
            "message": _("An error occurred while processing your request"),
            "error": "SERVER_ERROR"
        }