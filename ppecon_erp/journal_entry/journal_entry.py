import frappe

@frappe.whitelist()
def get_all_employees_for_jv(doctype, txt, searchfield, start, page_len, filters=None):
    """Get employees for Journal Entry ignoring HR restrictions"""
    
    # Check if user has Accounts Manager role
    if 'Accounts Manager' not in frappe.get_roles(frappe.session.user):
        # For non-account managers, use standard query
        return get_restricted_employees(doctype, txt, searchfield, start, page_len, filters)
    
    # Build query for Accounts Managers
    search_fields = ['name', 'employee_name']
    conditions = []
    params = []
    
    # Active employees
    conditions.append("status = 'Active'")
    
    # Search text
    if txt:
        search_conditions = []
        for field in search_fields:
            search_conditions.append(f"{field} LIKE %s")
            params.append(f"%{txt}%")
        conditions.append(f"({' OR '.join(search_conditions)})")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Direct SQL query to bypass permissions
    query = f"""
        SELECT name, employee_name
        FROM `tabEmployee`
        WHERE {where_clause}
        ORDER BY employee_name
        LIMIT %s, %s
    """
    
    params.extend([start, page_len])
    
    result = frappe.db.sql(query, tuple(params), as_list=True)
    return result

def get_restricted_employees(doctype, txt, searchfield, start, page_len, filters):
    """Standard employee query with HR restrictions"""
    return frappe.db.sql("""
        SELECT name, employee_name 
        FROM `tabEmployee`
        WHERE status = 'Active'
        AND (%(key)s LIKE %(txt)s
            OR employee_name LIKE %(txt)s)
        ORDER BY employee_name
        LIMIT %(start)s, %(page_len)s
    """, {
        'key': searchfield,
        'txt': "%%%s%%" % txt,
        'start': start,
        'page_len': page_len
    })