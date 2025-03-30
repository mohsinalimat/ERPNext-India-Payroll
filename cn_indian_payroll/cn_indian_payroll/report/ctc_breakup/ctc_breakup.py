import frappe
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

def get_all_employee(filters=None):
    if filters is None:
        filters = {}

    conditions1 = {"docstatus": 1}

    if filters.get("employee"):
        conditions1["employee"] = filters["employee"]
    if filters.get("payroll_period"):
        conditions1["custom_payroll_period"] = filters["payroll_period"]
    if filters.get("from_date"):
        conditions1["from_date"] = (">=", filters["from_date"])


    get_all_ssa = frappe.get_list('Salary Structure Assignment',
                filters=conditions1,
                fields=['*']
            )

    salary_components = set()  
    reimbursement_components = set()  
    data = []
    
    ctc_components = frappe.get_all("Salary Component", filters={"custom_is_part_of_ctc": 1}, fields=["*"],order_by="custom_sequence asc")
    ctc_components_set = set(component.name for component in ctc_components)

    for each_employee in get_all_ssa:
        # Initialize row data
        row = {
            'employee': each_employee.get("employee"),
            'employee_name': each_employee.get("employee_name"),
            'from_date': each_employee.get("from_date"),
            'doj': each_employee.get("custom_date_of_joining"),
            'base': each_employee.get("base"),
            
            'regime': each_employee.get("income_tax_slab"),
        }

        

        
        
        salary_slip = make_salary_slip(
            source_name=each_employee.get("salary_structure"),
            employee=each_employee.get("employee"),
            print_format='Salary Slip Standard for CTC',
            
            posting_date=each_employee.get("from_date"),
            for_preview= 1, 
             
        )

        
        for earning in salary_slip.earnings:
            component_name = earning.salary_component
            if component_name in ctc_components_set:
                amount = earning.amount
                salary_components.add(component_name)
                row[component_name] = round(row.get(component_name, 0) + amount)

        # Process deductions
        for deduction in salary_slip.deductions:
            component_name = deduction.salary_component
            if component_name in ctc_components_set:
                amount = deduction.amount
                salary_components.add(component_name)
                row[component_name] = round(row.get(component_name, 0) + amount)


        data.append(row)

    # Define columns with employee details, salary components, and allowances
    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Effective From", "fieldname": "from_date", "fieldtype": "Date", "width": 200},
        {"label": "Date of Joining", "fieldname": "doj", "fieldtype": "Date", "width": 200},
        {"label": "Total Amount", "fieldname": "base", "fieldtype": "Data", "width": 200},
        
        {"label": "Income Tax Regime", "fieldname": "regime", "fieldtype": "Data", "width": 200}

        
        
    ]
    
    # Adding salary components to the columns
    for component in salary_components:
        columns.append({
            "label": component,
            "fieldname": component,
            "fieldtype": "Currency",
            "width": 150
        })

    

    # Adding reimbursement components to the columns
    for component in reimbursement_components:
        columns.append({
            "label": component,
            "fieldname": component,
            "fieldtype": "Currency",
            "width": 150
        })

    return columns, data

def execute(filters=None):
    columns, data = get_all_employee(filters)
    return columns, data