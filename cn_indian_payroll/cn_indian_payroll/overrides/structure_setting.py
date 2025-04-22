from datetime import datetime
import frappe


def validate(self, method):
    effective_from = (
        self.effective_from
        if isinstance(self.effective_from, datetime)
        else datetime.strptime(self.effective_from, "%Y-%m-%d")
    ).date()  # Make it a date object

    active_employees = frappe.get_all(
        "Employee", filters={"status": "Active"}, fields=["name"]
    )

    if active_employees:
        for emp in active_employees:
            ssa_list = frappe.get_list(
                "Salary Structure Assignment",
                filters={"employee": emp.name, "docstatus": 1},
                fields=["name"],
                order_by="from_date desc",
                limit=1,
            )

            if ssa_list:
                ssa = frappe.get_doc("Salary Structure Assignment", ssa_list[0].name)

                if ssa.from_date <= effective_from:
                    new_ssa = frappe.new_doc("Salary Structure Assignment")
                    new_ssa.employee = ssa.employee
                    new_ssa.salary_structure = ssa.salary_structure
                    new_ssa.from_date = self.effective_from
                    new_ssa.income_tax_slab = self.income_tax_slab
                    new_ssa.company = self.company
                    new_ssa.custom_payroll_period = self.payroll_period
                    new_ssa.currency = ssa.currency
                    new_ssa.base = ssa.base


                    new_ssa.insert()
                    new_ssa.submit()
