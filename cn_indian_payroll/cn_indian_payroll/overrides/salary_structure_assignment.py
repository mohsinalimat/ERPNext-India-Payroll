import frappe
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import SalaryStructureAssignment

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from frappe.utils import getdate
from datetime import datetime
from frappe import _
from frappe.utils.pdf import get_pdf

class CustomSalaryStructureAssignment(SalaryStructureAssignment):


    def on_submit(self):
        self.insert_tax_declaration_list()
        self.update_employee_promotion()

    def on_cancel(self):
        self.cancel_declaration()

    def validate(self):
        super().validate()
        self.update_min_wages()


    def before_update_after_submit(self):
        self.update_min_wages()









    def update_min_wages(self):
            if self.custom_minimum_wages_applicable:
                state = frappe.get_doc("State", self.custom_minimum_wages_state)
                if not state:
                    frappe.throw(_("Selected state does not exist."))

                match_found = False
                for wages in state.min_wages:
                    if (
                        wages.zone == self.custom_zone
                        and wages.skill_level == self.custom_skill_level
                    ):
                        self.custom_basic_value = wages.basic_daily_wage
                        self.custom_hra_value = wages.vda_daily_wages
                        match_found = True
                        break

                if not match_found:
                    self.custom_basic_value = 0
                    self.custom_hra_value = 0



    def cancel_declaration(self):
        declarations = frappe.db.get_list(
            'Employee Tax Exemption Declaration',
            filters={
                'payroll_period': self.custom_payroll_period,
                'docstatus': ['in', [0, 1]],
                'employee': self.employee,
                'custom_salary_structure_assignment': self.name,
            },
            fields=['name', 'docstatus']
        )

        if declarations:
            declaration = declarations[0]
            declaration_doc = frappe.get_doc('Employee Tax Exemption Declaration', declaration.name)

            if declaration_doc.docstatus == 0:
                frappe.delete_doc('Employee Tax Exemption Declaration', declaration_doc.name)

            elif declaration_doc.docstatus == 1:
                declaration_doc.cancel()
                frappe.delete_doc('Employee Tax Exemption Declaration', declaration_doc.name)


    def update_employee_promotion(self):
        if self.custom_promotion_id:
            get_promotion_doc=frappe.get_doc("Employee Promotion",self.custom_promotion_id)
            get_promotion_doc.custom_status="Payroll Configured"
            get_promotion_doc.save()


    def insert_tax_declaration_list(self):
        if not self.employee:
            return

        sub_categories = []
        payroll_period = frappe.get_doc("Payroll Period", self.custom_payroll_period)
        from_date = getdate(self.from_date)
        payroll_start_date = getdate(payroll_period.start_date)
        payroll_end_date = getdate(payroll_period.end_date)

        declaration_start_date = max(from_date, payroll_start_date)
        start = declaration_start_date if not isinstance(declaration_start_date, str) else datetime.strptime(declaration_start_date, "%Y-%m-%d").date()
        end = payroll_end_date if not isinstance(payroll_end_date, str) else datetime.strptime(payroll_end_date, "%Y-%m-%d").date()

        num_months = (end.year - start.year) * 12 + (end.month - start.month) + 1

        salary_slip = make_salary_slip(
            source_name=self.salary_structure,
            employee=self.employee,
            print_format='Salary Slip Standard',
            posting_date=self.from_date,
            for_preview=1,
        )

        def add_exemption(component_type, monthly_amount):
            total_amount = monthly_amount * num_months
            exemption_components = frappe.get_all(
                'Employee Tax Exemption Sub Category',
                filters={'custom_component_type': component_type,"is_active":1},
                fields=['name', 'max_amount']
            )
            for comp in exemption_components:
                allowed_amount = min(total_amount, comp.max_amount or total_amount)
                sub_categories.append({
                    "sub_category": comp.name,
                    "max_amount": comp.max_amount,
                    "amount": allowed_amount
                })

        if self.custom_tax_regime == "New Regime" or self.custom_tax_regime == "Old Regime":
            for earning in salary_slip.earnings:
                comp_doc = frappe.get_doc("Salary Component", earning.salary_component)
                if comp_doc.component_type == "NPS" and comp_doc.custom_component_sub_type == "Fixed":
                    add_exemption("NPS", earning.amount)

            if self.custom_tax_regime == "Old Regime":
                for deduction in salary_slip.deductions:
                    comp_doc = frappe.get_doc("Salary Component", deduction.salary_component)
                    if comp_doc.component_type in ["Provident Fund", "Professional Tax"] and comp_doc.custom_component_sub_type == "Fixed":
                        add_exemption(comp_doc.component_type, deduction.amount)

        existing_declaration = frappe.get_list(
            'Employee Tax Exemption Declaration',
            filters={
                'employee': self.employee,
                'payroll_period': self.custom_payroll_period,
                'docstatus': ['in', [0, 1]]
            },
            fields=['name']
        )

        if existing_declaration:
            return

        new_declaration = frappe.get_doc({
            'doctype': 'Employee Tax Exemption Declaration',
            'employee': self.employee,
            'company': self.company,
            'payroll_period': self.custom_payroll_period,
            'currency': self.currency,
            'custom_income_tax': self.income_tax_slab,
            'custom_salary_structure_assignment': self.name,
            'custom_posting_date': self.from_date
        })

        for category in sub_categories:
            new_declaration.append("declarations", {
                "exemption_sub_category": category["sub_category"],
                "max_amount": category["max_amount"],
                "amount": category["amount"]
            })

        new_declaration.insert()
        new_declaration.submit()
        frappe.db.commit()



# @frappe.whitelist()
# def generate_ctc_pdf(employee, salary_structure, print_format=None,  posting_date=None):

#     # Generate salary slip preview with required arguments
#     new_salary_slip = make_salary_slip(
#         source_name=salary_structure,
#         employee=employee,
#         print_format='Salary Slip Standard',
#         posting_date=posting_date,
#         for_preview=1
#     )



#     if not new_salary_slip:
#         frappe.throw("Unable to generate salary breakup. Check Salary Structure or Employee.")

#     earnings_list = []
#     reimbursement_list = []
#     deduction_list = []

#     for e in new_salary_slip.get("earnings", []):
#         comp = frappe.get_doc("Salary Component", e.salary_component)
#         if comp.custom_is_reimbursement:
#             reimbursement_list.append(e)
#         else:
#             earnings_list.append(e)

#     for d in new_salary_slip.get("deductions", []):
#         deduction_list.append(d)

#     context = {
#         "employee": employee,
#         "employee_name": new_salary_slip.get("employee_name"),
#         "department": new_salary_slip.get("department"),
#         "designation": new_salary_slip.get("designation"),
#         "company": new_salary_slip.get("company"),
#         "posting_date": new_salary_slip.get("posting_date"),
#         "salary_structure": new_salary_slip.get("salary_structure"),
#         "earnings": earnings_list,
#         "reimbursements": reimbursement_list,
#         "deductions": deduction_list,
#     }

#     frappe.msgprint(str(context))

# import frappe
# from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
# from frappe.utils.pdf import get_pdf

# @frappe.whitelist()
# def generate_ctc_pdf(employee, salary_structure, posting_date=None, employee_benefits=None):
#     """
#     Generate CTC PDF for a given employee and salary structure.
#     """
#     if employee_benefits is None:
#         employee_benefits = []

#     # Generate Salary Slip preview
#     new_salary_slip = make_salary_slip(
#         source_name=salary_structure,
#         employee=employee,
#         print_format='Salary Slip Standard',
#         posting_date=posting_date,
#         for_preview=1
#     )

#     if not new_salary_slip:
#         frappe.throw("Unable to generate salary breakup. Check Salary Structure or Employee.")

#     # Prepare earnings list
#     normal_earnings = []
#     for e in new_salary_slip.get("earnings", []):
#         e_doc = frappe.get_doc("Salary Component", e.salary_component)
#         if e_doc.custom_is_part_of_ctc:
#             normal_earnings.append({
#                 "salary_component": e.salary_component,
#                 "monthly_amount": e.amount,
#                 "annual_amount": e.amount * 12
#             })



#     # Prepare deductions list
#     deduction_list = []
#     for d in new_salary_slip.get("deductions", []):
#         d_doc = frappe.get_doc("Salary Component", d.salary_component)
#         if d_doc.custom_is_part_of_ctc:
#             deduction_list.append({
#                 "salary_component": d.salary_component,
#                 "monthly_amount": d.amount,
#                 "annual_amount": d.amount * 12
#             })

#     # Prepare reimbursements list
#     reimbursement_list = []
#     for b in employee_benefits:
#         component_name = b if isinstance(b, str) else b.get("salary_component")
#         if frappe.db.exists("Salary Component", component_name):
#             b_doc = frappe.get_doc("Salary Component", component_name)
#             amount = b.get("amount", 0) if isinstance(b, dict) else getattr(b_doc, "amount", 0)
#             reimbursement_list.append({
#                 "salary_component": component_name,
#                 "monthly_amount": amount,
#                 "annual_amount": amount * 12
#             })
#         else:
#             frappe.log_error(f"Salary Component '{component_name}' not found", "CTC PDF Generation")


#     # Context for HTML
#     context = {
#         "employee": employee,
#         "employee_name": new_salary_slip.get("employee_name"),
#         "department": new_salary_slip.get("department"),
#         "designation": new_salary_slip.get("designation"),
#         "company": new_salary_slip.get("company"),
#         "posting_date": new_salary_slip.get("posting_date"),
#         "salary_structure": new_salary_slip.get("salary_structure"),
#         "earnings": normal_earnings,
#         "reimbursements": reimbursement_list,
#         "deductions": deduction_list,
#     }

#     # Render HTML using template
#     html = frappe.render_template(
#         "cn_indian_payroll/templates/ctc_breakup_pdf.html",
#         context
#     )

#     # Generate PDF bytes
#     pdf_bytes = get_pdf(html)

#     # Save PDF as File document
#     file_doc = frappe.get_doc({
#         "doctype": "File",
#         "file_name": f"CTC_Breakup_{employee}.pdf",
#         "attached_to_doctype": "Employee",
#         "attached_to_name": employee,
#         "content": pdf_bytes,
#         "is_private": 0
#     })
#     file_doc.insert(ignore_permissions=True)

#     return {"pdf_url": file_doc.file_url}

import frappe
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from frappe.utils.pdf import get_pdf
import json

@frappe.whitelist()
def generate_ctc_pdf(employee, salary_structure, posting_date=None, employee_benefits=None):
    """
    Generate CTC PDF for a given employee and salary structure.
    """

    # Generate Salary Slip preview
    slip = make_salary_slip(
        source_name=salary_structure,
        employee=employee,
        print_format='Salary Slip Standard',
        posting_date=posting_date,
        for_preview=1
    )

    if not slip:
        frappe.throw("Unable to generate salary breakup. Check Salary Structure or Employee.")

    # --- Prepare earnings list and totals ---
    earnings_list = []
    total_monthly_earnings = 0
    total_annual_earnings = 0
    for e in slip.get("earnings", []):
        comp_doc = frappe.get_doc("Salary Component", e.salary_component)
        if comp_doc.custom_is_part_of_ctc:
            amount = e.amount or 0
            earnings_list.append({
                "salary_component": e.salary_component,
                "monthly_amount": amount,
                "annual_amount": amount * 12
            })
            total_monthly_earnings += amount
            total_annual_earnings += amount * 12

    # --- Prepare deductions list and totals ---
    deduction_list = []
    total_monthly_ded = 0
    total_annual_ded = 0
    for d in slip.get("deductions", []):
        comp_doc = frappe.get_doc("Salary Component", d.salary_component)
        if comp_doc.custom_is_part_of_ctc:
            amount = d.amount or 0
            deduction_list.append({
                "salary_component": d.salary_component,
                "monthly_amount": amount,
                "annual_amount": amount * 12
            })
            total_monthly_ded += amount
            total_annual_ded += amount * 12

    # --- Prepare reimbursements list and totals ---


    if employee_benefits:
        if isinstance(employee_benefits, str):
            try:
                employee_benefits = json.loads(employee_benefits)
            except Exception:
                employee_benefits = []

    reimbursement_list = []
    total_monthly_reim = 0
    total_annual_reim = 0

    for r in employee_benefits:
        # Each r is now a dict (from JSON)
        comp_name = r.get("salary_component")
        amount = r.get("amount", 0)
        if comp_name:
            reimbursement_list.append({
                "salary_component": comp_name,
                "monthly_amount": amount / 12,
                "annual_amount": amount
            })
            total_monthly_reim += amount / 12
            total_annual_reim += amount



    # --- Calculate final CTC ---
    total_monthly_ctc = total_monthly_earnings + total_monthly_reim + total_monthly_ded
    total_annual_ctc = total_annual_earnings + total_annual_reim + total_annual_ded

    # --- Context for HTML ---
    context = {
        "employee": employee,
        "employee_name": slip.get("employee_name") or "",
        "department": slip.get("department") or "",
        "designation": slip.get("designation") or "",
        "company": slip.get("company") or "",
        "posting_date": slip.get("posting_date") or "",
        "salary_structure": slip.get("salary_structure") or "",
        "earnings": earnings_list,
        "reimbursements": reimbursement_list,
        "deductions": deduction_list,
        "total_monthly_earnings": total_monthly_earnings,
        "total_annual_earnings": total_annual_earnings,
        "total_monthly_reim": total_monthly_reim,
        "total_annual_reim": total_annual_reim,
        "total_monthly_ded": total_monthly_ded,
        "total_annual_ded": total_annual_ded,
        "total_monthly_ctc": total_monthly_ctc,
        "total_annual_ctc": total_annual_ctc
    }

    # Render HTML template
    html = frappe.render_template(
        "cn_indian_payroll/templates/ctc_breakup_pdf.html",
        context
    )

    # Generate PDF
    pdf_bytes = get_pdf(html)

    # Save PDF
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"CTC_Breakup_{employee}.pdf",
        "attached_to_doctype": "Employee",
        "attached_to_name": employee,
        "content": pdf_bytes,
        "is_private": 0
    })
    file_doc.insert(ignore_permissions=True)

    return {"pdf_url": file_doc.file_url}
