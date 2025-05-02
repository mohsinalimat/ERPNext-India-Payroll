import frappe

def get_salary_slips(filters=None):
    if filters is None:
        filters = {}

    conditions = {"docstatus": ["in", [0, 1]]}

    if filters.get("month"):
        conditions["custom_month"] = filters["month"]

    if filters.get("payroll_period"):
        conditions["custom_payroll_period"] = filters["payroll_period"]

    if filters.get("company"):
        conditions["company"] = filters["company"]

        try:
            company_doc = frappe.get_doc("Company", filters["company"])
        except frappe.DoesNotExistError:
            frappe.throw("Invalid company specified.")

        if not company_doc.basic_component or not company_doc.custom_da_component:
            frappe.throw("Please set Basic Component and DA Component in Company Master.")

        basic_component = company_doc.basic_component
        da_component = company_doc.custom_da_component
    else:
        frappe.throw("Company is a mandatory filter.")

    salary_slips = frappe.get_list(
        'Salary Slip',
        fields=["name", "employee", "custom_month", "custom_payroll_period", "company", "gross_pay"],
        filters=conditions,
        order_by="name DESC",
    )

    detailed_salary_slips = []

    for slip in salary_slips:
        each_salary_slip = frappe.get_doc('Salary Slip', slip["name"])
        each_employee = frappe.get_doc("Employee", each_salary_slip.employee)

        # Get salary structure assignment to check EPF eligibility
        pf_account = frappe.get_value(
            "Salary Structure Assignment",
            {"employee": each_salary_slip.employee},
            ["name", "custom_is_epf"],
            as_dict=True
        )

        if not pf_account or not pf_account.custom_is_epf:
            continue  # Skip if not EPF eligible

        # Initialize basic and DA
        basic = 0
        da = 0
        epf_amount_employee = 0
        epf_amount_employer=0
        eps_amount=0

        for earning in each_salary_slip.earnings:
            if earning.salary_component == basic_component:
                basic = earning.amount
            if earning.salary_component == da_component:
                da = earning.amount

        for deduction in each_salary_slip.deductions:
            get_epf_component=frappe.get_doc("Salary Component", deduction.salary_component)
            if get_epf_component.component_type=="Provident Fund":
                epf_amount_employee= deduction.amount




        eligible_wage = min(round(float(basic or 0) + float(da or 0)), 15000)
        epf_amount_employer = eligible_wage * 8.33 / 100
        eps_amount = eligible_wage * 3.67 / 100

        detailed_salary_slips.append({
            "employee": each_salary_slip.employee,
            "employee_name": each_salary_slip.employee_name,
            "custom_month": each_salary_slip.custom_month,
            "custom_payroll_period": each_salary_slip.custom_payroll_period,
            "company": each_salary_slip.company,
            "uan": getattr(each_employee, "custom_uan", None),
            "gross_pay": each_salary_slip.gross_pay,
            "epf_wages": eligible_wage,
            "eps_wages": eligible_wage,
            "edli_wages": eligible_wage,
            "ncp_days": each_salary_slip.custom_total_leave_without_pay or 0,
            "refund": 0,
            "epf_amount_employee": epf_amount_employee,
            "epf_amount_employer": epf_amount_employer,
            "eps_amount": eps_amount,

        })

    return detailed_salary_slips

def execute(filters=None):
    columns = [
        {"fieldname": "uan", "label": "UAN", "fieldtype": "Data", "width": 150},
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 200},
        {"fieldname": "custom_month", "label": "Month", "fieldtype": "Data", "width": 100},
        {"fieldname": "custom_payroll_period", "label": "Payroll Period", "fieldtype": "Data", "width": 150},
        {"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 150},
        {"fieldname": "gross_pay", "label": "Gross Pay", "fieldtype": "Currency", "width": 150},
        {"fieldname": "epf_wages", "label": "EPF Wages", "fieldtype": "Currency", "width": 150},
        {"fieldname": "eps_wages", "label": "EPS Wages", "fieldtype": "Currency", "width": 150},
        {"fieldname": "edli_wages", "label": "EDLI Wages", "fieldtype": "Currency", "width": 150},
        {"fieldname": "epf_amount_employee", "label": "EPF Employee Contribution", "fieldtype": "Currency", "width": 150},
        {"fieldname": "epf_amount_employer", "label": "EPF Employer Contribution", "fieldtype": "Currency", "width": 150},
        {"fieldname": "eps_amount", "label": "EPS Contribution", "fieldtype": "Currency", "width": 150},
        {"fieldname": "ncp_days", "label": "NCP Days", "fieldtype": "Float", "width": 120},
        {"fieldname": "refund", "label": "Refund Of Advances", "fieldtype": "Currency", "width": 150},
    ]

    data = get_salary_slips(filters)

    return columns, data



@frappe.whitelist()
def download_ecr_txt(filters=None):
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)

    salary_data = get_salary_slips(filters)
    lines = []

    def r(value):
        return str(round(value or 0))

    for row in salary_data:
        line = "\t".join([
            str(row.get("uan", "")),
            row.get("employee_name", ""),
            r(row.get("gross_pay")),
            r(row.get("epf_wages")),
            r(row.get("eps_wages")),
            r(row.get("edli_wages")),
            r(row.get("epf_amount_employee")),
            r(row.get("epf_amount_employer")),
            r(row.get("eps_amount")),
            r(row.get("ncp_days")),
            r(row.get("refund")),
        ])
        lines.append(line)

    return "\n".join(lines)
