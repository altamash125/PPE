import frappe
from frappe import _
from frappe.utils import flt, nowdate

@frappe.whitelist()
def submit_employee_advance_from_mobile(**kwargs):
    """
    Mobile API to create and submit Employee Advance via Workflow.
    Includes specific account options and repay_unclaimed_amount_from_salary field.
    """
    
    # Account options as per your requirement
    ADVANCE_ACCOUNT_OPTIONS = [
        "1610 - Employee Advances - PPE",
        "1311 - Retention with Clients - PPE", 
        "1310 - Debtors - PPE",
        "1611 - Employees Petty cash - PPE"
    ]
    
    # Set default company - use Pioneer Projects Executer Company as default
    DEFAULT_COMPANY = "Pioneer Projects Executer Company"
    
    # Check if company exists, fallback to any company if not
    def get_company(company_name=None):
        if company_name:
            if frappe.db.exists("Company", company_name):
                return company_name
            else:
                frappe.log_error(f"Company {company_name} not found, using default")
        
        # Try default company
        if frappe.db.exists("Company", DEFAULT_COMPANY):
            return DEFAULT_COMPANY
        
        # Try any company
        companies = frappe.get_all("Company", fields=["name"], limit=1)
        if companies:
            return companies[0].name
        
        frappe.throw(_("No Company found in the system. Please create a Company first."))
    
    # Set default values
    posting_date = kwargs.get("posting_date", nowdate())
    company = get_company(kwargs.get("company"))
    
    # Validate required fields
    required_fields = ["employee", "advance_amount", "purpose"]
    missing_fields = []
    
    for field in required_fields:
        if not kwargs.get(field):
            missing_fields.append(field)
    
    if missing_fields:
        frappe.throw(_("Missing required fields: {0}").format(", ".join(missing_fields)))
    
    # Validate employee exists
    employee = kwargs.get("employee")
    if not frappe.db.exists("Employee", employee):
        frappe.throw(_("Employee '{0}' does not exist").format(employee))
    
    # Validate advance amount
    try:
        advance_amount = flt(kwargs.get("advance_amount"))
        if advance_amount <= 0:
            frappe.throw(_("Advance Amount must be greater than 0"))
    except ValueError:
        frappe.throw(_("Invalid value for Advance Amount"))
    
    # Validate advance account if provided
    advance_account = kwargs.get("advance_account")
    if advance_account:
        if advance_account not in ADVANCE_ACCOUNT_OPTIONS:
            frappe.throw(_("Invalid Advance Account. Must be one of: {0}").format(
                ", ".join(ADVANCE_ACCOUNT_OPTIONS)
            ))
    else:
        # Set default advance account
        advance_account = "1610 - Employee Advances - PPE"
    
    # Get exchange rate
    exchange_rate = flt(kwargs.get("exchange_rate", 1.0))
    if exchange_rate <= 0:
        exchange_rate = 1.0
    
    # Handle repay_unclaimed_amount_from_salary checkbox
    repay_unclaimed = kwargs.get("repay_unclaimed_amount_from_salary", 0)
    
    # Convert to integer (0 or 1)
    if isinstance(repay_unclaimed, str):
        repay_unclaimed = 1 if repay_unclaimed.lower() in ["1", "true", "yes"] else 0
    elif isinstance(repay_unclaimed, bool):
        repay_unclaimed = 1 if repay_unclaimed else 0
    else:
        repay_unclaimed = int(repay_unclaimed) if repay_unclaimed else 0
    
    # Prepare document data
    doc_data = {
        "doctype": "Employee Advance",
        "employee": employee,
        "posting_date": posting_date,
        "company": company,
        "purpose": kwargs.get("purpose"),
        "advance_amount": advance_amount,
        "exchange_rate": exchange_rate,
        "repay_unclaimed_amount_from_salary": repay_unclaimed,
        "advance_account": advance_account,
        "remarks": kwargs.get("remarks", ""),
    }
    
    # Add other optional fields if provided
    optional_fields = {
        "mode_of_payment": kwargs.get("mode_of_payment"),
        "currency": kwargs.get("currency"),
        "paid_from_account": kwargs.get("paid_from_account"),
        "paid_from_account_currency": kwargs.get("paid_from_account_currency"),
        "account_currency": kwargs.get("account_currency"),
    }
    
    for field, value in optional_fields.items():
        if value:
            doc_data[field] = value
    
    # Create Employee Advance document
    doc = frappe.get_doc(doc_data)
    
    # Insert draft
    doc.insert(ignore_permissions=True)
    
    # Submit via Workflow or directly
    try:
        # Check if workflow exists for Employee Advance
        workflow_name = frappe.db.get_value("Workflow", {
            "document_type": "Employee Advance",
            "is_active": 1
        }, "name")
        
        if workflow_name:
            frappe.model.workflow.apply_workflow(doc, "Submit")
        else:
            doc.submit()
            
    except Exception as e:
        # Log the error
        frappe.log_error(
            title="Employee Advance Submission Error",
            message=f"Error submitting Employee Advance {doc.name}: {str(e)}\n\nData: {doc_data}"
        )
        
        # Try direct submission if workflow fails
        try:
            doc.submit()
        except Exception as submit_error:
            frappe.throw(_("Failed to submit Employee Advance: {0}").format(str(submit_error)))
    
    doc.reload()
    
    # Get additional info for response
    employee_name = frappe.db.get_value("Employee", employee, "employee_name")
    
    return {
        "success": True,
        "message": "Employee Advance Submitted Successfully",
        "name": doc.name,
        "document_status": doc.docstatus,
        "workflow_state": getattr(doc, 'workflow_state', None),
        "advance_amount": doc.advance_amount,
        "currency": doc.currency if hasattr(doc, 'currency') else doc.company_currency,
        "repay_unclaimed_amount_from_salary": doc.repay_unclaimed_amount_from_salary,
        "company": doc.company,
        "posting_date": str(doc.posting_date),
        "employee": doc.employee,
        "employee_name": employee_name,
        "purpose": doc.purpose
    }


# Additional helper APIs

@frappe.whitelist()
def get_employee_advance_details(advance_name):
    """
    Get details of a specific Employee Advance.
    """
    if not frappe.db.exists("Employee Advance", advance_name):
        frappe.throw(_("Employee Advance '{0}' not found").format(advance_name))
    
    doc = frappe.get_doc("Employee Advance", advance_name)
    
    return {
        "name": doc.name,
        "employee": doc.employee,
        "employee_name": doc.employee_name,
        "company": doc.company,
        "posting_date": str(doc.posting_date),
        "purpose": doc.purpose,
        "advance_amount": doc.advance_amount,
        "currency": doc.currency,
        "workflow_state": doc.workflow_state,
        "status": doc.status,
        "repay_unclaimed_amount_from_salary": doc.repay_unclaimed_amount_from_salary,
        "advance_account": doc.advance_account,
        "mode_of_payment": doc.mode_of_payment
    }


@frappe.whitelist()
def get_employee_advances(employee=None, status=None):
    """
    Get list of Employee Advances for an employee.
    """
    filters = {}
    
    if employee:
        filters["employee"] = employee
    
    if status:
        filters["workflow_state"] = status
    
    advances = frappe.get_all(
        "Employee Advance",
        filters=filters,
        fields=["name", "employee", "employee_name", "posting_date", "purpose",
                "advance_amount", "currency", "workflow_state", "status",
                "company", "repay_unclaimed_amount_from_salary"],
        order_by="posting_date desc",
        limit=50
    )
    
    return {
        "advances": advances,
        "count": len(advances)
    }






# import frappe
# from frappe import _
# from frappe.utils import flt, nowdate

# @frappe.whitelist()
# def submit_employee_advance_from_mobile(**kwargs):
#     """
#     Mobile API to create and submit Employee Advance via Workflow.
#     Includes specific account options and repay_unclaimed_amount_from_salary field.
#     """
    
#     # Account options as per your requirement
#     ADVANCE_ACCOUNT_OPTIONS = [
#         "1610 - Employee Advances - PPE",
#         "1311 - Retention with Clients - PPE", 
#         "1310 - Debtors - PPE",
#         "1611 - Employees Petty cash - PPE"
#     ]
    
#     # Fixed company name
#     COMPANY_NAME = "Pioneer Projects Executer Company"
    
#     # Check if company exists
#     if not frappe.db.exists("Company", COMPANY_NAME):
#         frappe.throw(_("Company '{0}' does not exist. Please create it first.").format(COMPANY_NAME))
    
#     # Set default values for optional fields
#     posting_date = kwargs.get("posting_date", nowdate())
#     company = kwargs.get("company") or COMPANY_NAME
    
#     # Validate required fields - only employee, advance_amount, and purpose are required
#     required_fields = ["employee", "advance_amount", "purpose"]
#     missing_fields = []
    
#     for field in required_fields:
#         if not kwargs.get(field):
#             missing_fields.append(field)
    
#     if missing_fields:
#         frappe.throw(_("Missing required fields: {0}").format(", ".join(missing_fields)))
    
#     # Validate advance amount
#     try:
#         advance_amount = flt(kwargs.get("advance_amount"))
#         if advance_amount <= 0:
#             frappe.throw(_("Advance Amount must be greater than 0"))
#     except ValueError:
#         frappe.throw(_("Invalid value for Advance Amount"))
    
#     # Validate advance account if provided
#     advance_account = kwargs.get("advance_account")
#     if advance_account and advance_account not in ADVANCE_ACCOUNT_OPTIONS:
#         frappe.throw(_("Invalid Advance Account. Must be one of: {0}").format(
#             ", ".join(ADVANCE_ACCOUNT_OPTIONS)
#         ))
    
#     # Get default exchange rate if not provided
#     exchange_rate = flt(kwargs.get("exchange_rate", 1.0))
#     if exchange_rate <= 0:
#         exchange_rate = 1.0
    
#     # Handle checkbox value for repay_unclaimed_amount_from_salary
#     # Mobile apps might send it as string "1"/"0" or boolean True/False
#     repay_unclaimed = kwargs.get("repay_unclaimed_amount_from_salary", 0)
    
#     # Convert string to boolean if needed
#     if isinstance(repay_unclaimed, str):
#         if repay_unclaimed.lower() in ["1", "true", "yes"]:
#             repay_unclaimed = 1
#         else:
#             repay_unclaimed = 0
#     elif isinstance(repay_unclaimed, bool):
#         repay_unclaimed = 1 if repay_unclaimed else 0
#     else:
#         repay_unclaimed = int(repay_unclaimed) if repay_unclaimed else 0
    
#     # Prepare document data
#     doc_data = {
#         "doctype": "Employee Advance",
#         "employee": kwargs.get("employee"),
#         "posting_date": posting_date,
#         "company": company,
#         "purpose": kwargs.get("purpose"),
#         "advance_amount": advance_amount,
#         "exchange_rate": exchange_rate,
#         "repay_unclaimed_amount_from_salary": repay_unclaimed,
#         "remarks": kwargs.get("remarks", ""),
#     }
    
#     # Add advance_account only if provided
#     if advance_account:
#         doc_data["advance_account"] = advance_account
    
#     # Add other optional fields if provided
#     optional_fields = {
#         "mode_of_payment": kwargs.get("mode_of_payment"),
#         "currency": kwargs.get("currency"),
#         "paid_from_account": kwargs.get("paid_from_account"),
#         "paid_from_account_currency": kwargs.get("paid_from_account_currency"),
#         "account_currency": kwargs.get("account_currency"),
#     }
    
#     for field, value in optional_fields.items():
#         if value:
#             doc_data[field] = value
    
#     # Create Employee Advance document
#     doc = frappe.get_doc(doc_data)
    
#     # Insert draft
#     doc.insert(ignore_permissions=True)
    
#     # Submit via Workflow or directly
#     try:
#         # Check if workflow exists for Employee Advance
#         workflow_name = frappe.db.get_value("Workflow", {
#             "document_type": "Employee Advance",
#             "is_active": 1
#         }, "name")
        
#         if workflow_name:
#             frappe.model.workflow.apply_workflow(doc, "Submit")
#         else:
#             doc.submit()
            
#     except Exception as e:
#         # Log the error for debugging
#         error_message = str(e)
#         frappe.log_error(
#             title="Employee Advance Submission Error",
#             message=f"Error submitting Employee Advance {doc.name}: {error_message}\n\nData: {doc_data}"
#         )
        
#         # Try direct submission
#         try:
#             doc.submit()
#         except Exception as submit_error:
#             frappe.throw(_("Failed to submit Employee Advance: {0}").format(str(submit_error)))
    
#     doc.reload()
    
#     return {
#         "success": True,
#         "message": "Employee Advance Submitted Successfully",
#         "name": doc.name,
#         "document_status": doc.docstatus,
#         "workflow_state": getattr(doc, 'workflow_state', None),
#         "advance_amount": doc.advance_amount,
#         "currency": doc.currency if hasattr(doc, 'currency') else doc.company_currency,
#         "repay_unclaimed_amount_from_salary": doc.repay_unclaimed_amount_from_salary,
#         "company": doc.company,
#         "posting_date": str(doc.posting_date)
#     }