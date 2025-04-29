# from datetime import datetime
# import frappe


# def validate(self, method):
#     effective_from = (
#         self.effective_from
#         if isinstance(self.effective_from, datetime)
#         else datetime.strptime(self.effective_from, "%Y-%m-%d")
#     ).date()  # Make it a date object

#     active_employees = frappe.get_all(
#         "Employee", filters={"status": "Active"}, fields=["name"]
#     )

#     if active_employees:
#         for emp in active_employees:
#             ssa_list = frappe.get_list(
#                 "Salary Structure Assignment",
#                 filters={"employee": emp.name, "docstatus": 1},
#                 fields=["name"],
#                 order_by="from_date desc",
#                 limit=1,
#             )

#             if ssa_list:
#                 ssa = frappe.get_doc("Salary Structure Assignment", ssa_list[0].name)

#                 if ssa.from_date <= effective_from:
#                     new_ssa = frappe.new_doc("Salary Structure Assignment")
#                     new_ssa.employee = ssa.employee
#                     new_ssa.salary_structure = ssa.salary_structure
#                     new_ssa.from_date = self.effective_from
#                     new_ssa.income_tax_slab = self.income_tax_slab
#                     new_ssa.company = self.company
#                     new_ssa.custom_payroll_period = self.payroll_period
#                     new_ssa.currency = ssa.currency
#                     new_ssa.base = ssa.base


#                     new_ssa.insert()
#                     new_ssa.submit()

import frappe
from frappe import _
from frappe.utils.background_jobs import enqueue
from frappe.model.document import Document
from datetime import datetime

@frappe.whitelist()
def create_salary_structure_assignment(company, payroll_period, income_tax_slab, effective_date):
    enqueue(
        method=create_salary_structure_assignment_worker,
        queue='default',
        timeout=600,
        is_async=True,
        company=company,
        payroll_period=payroll_period,
        income_tax_slab=income_tax_slab,
        effective_date=effective_date
    )
    return "queued"

def create_salary_structure_assignment_worker(company, payroll_period, income_tax_slab, effective_date):
    try:
        effective_date = datetime.strptime(effective_date, "%Y-%m-%d").date()

        employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name"])
        total = len(employees)

        for idx, emp in enumerate(employees):
            frappe.publish_realtime("ssa_progress", {"progress": int((idx + 1) / total * 100)})

            # ✅ Skip if SSA with same from_date already exists for employee
            if frappe.db.exists("Salary Structure Assignment", {
                "employee": emp.name,
                "from_date": effective_date,
                "docstatus": 1
            }):
                continue

            ssa_list = frappe.get_list(
                "Salary Structure Assignment",
                filters={"employee": emp.name, "docstatus": 1},
                fields=["name"],
                order_by="from_date desc",
                limit=1,
            )

            if not ssa_list:
                continue

            ssa = frappe.get_doc("Salary Structure Assignment", ssa_list[0].name)
            if ssa.from_date <= effective_date:
                new_ssa = frappe.new_doc("Salary Structure Assignment")
                new_ssa.employee = emp.name
                new_ssa.salary_structure = ssa.salary_structure
                new_ssa.from_date = effective_date
                new_ssa.income_tax_slab = income_tax_slab
                new_ssa.company = company
                new_ssa.custom_payroll_period = payroll_period
                new_ssa.currency = ssa.currency
                new_ssa.base = ssa.base

                new_ssa.insert()
                new_ssa.submit()

        frappe.publish_realtime("ssa_progress", {"progress": 100})

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Salary Structure Assignment Creation Failed")
        frappe.publish_realtime("ssa_progress", {"progress": 100})
