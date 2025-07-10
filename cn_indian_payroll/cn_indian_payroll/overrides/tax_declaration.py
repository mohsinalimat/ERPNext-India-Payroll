import frappe
from hrms.payroll.doctype.employee_tax_exemption_declaration.employee_tax_exemption_declaration import (
    EmployeeTaxExemptionDeclaration,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

from frappe.utils import flt
from hrms.hr.utils import (
    calculate_annual_eligible_hra_exemption,
    get_total_exemption_amount,
    validate_active_employee,
    validate_duplicate_exemption_for_payroll_period,
    validate_tax_declaration,
)

from datetime import datetime, timedelta
from datetime import date


import json
from frappe.utils import getdate
from dateutil.relativedelta import relativedelta


class CustomEmployeeTaxExemptionDeclaration(EmployeeTaxExemptionDeclaration):

    def before_save(self):

        self.update_json_data_in_declaration()

    def before_update_after_submit(self):

        # self.calculate_hra_breakup()
        # self.update_tax_declaration()
        self.validation_on_section10()
        self.set_total_declared_amount()
        self.set_total_exemption_amount()

    def update_json_data_in_declaration(self):
        total_nps = 0
        total_pf = 0
        total_pt = 0

        for subcategory in self.declarations:
            check_component = frappe.get_doc("Employee Tax Exemption Sub Category", subcategory.exemption_sub_category)

            if check_component.custom_component_type == "NPS":
                total_nps = subcategory.amount

            elif check_component.custom_component_type == "Provident Fund":
                total_pf = subcategory.amount

            elif check_component.custom_component_type == "Professional Tax":
                total_pt = subcategory.amount

        form_data = json.loads(self.custom_declaration_form_data or '[]')

        if not form_data:
            for subcategory in self.declarations:
                check_component = frappe.get_doc("Employee Tax Exemption Sub Category", subcategory.exemption_sub_category)

                form_data.append({
                    "id": subcategory.exemption_sub_category,
                    "sub_category": subcategory.exemption_sub_category,
                    "exemption_category": subcategory.exemption_category,
                    "max_amount": subcategory.max_amount,
                    "amount": subcategory.amount,
                    "value": subcategory.amount
                })

        for entry in form_data:
            subcat = entry.get("sub_category") or entry.get("id")

            component_type = frappe.db.get_value(
                "Employee Tax Exemption Sub Category",
                subcat,
                "custom_component_type"
            )

            if component_type == "NPS":
                entry["amount"] = total_nps
                entry["value"] = total_nps
            elif component_type == "Provident Fund":
                entry["amount"] = total_pf
                entry["value"] = total_pf
            elif component_type == "Professional Tax":
                entry["amount"] = total_pt
                entry["value"] = total_pt

        self.custom_declaration_form_data = json.dumps(form_data)




    def update_json_data(self):
        if self.declarations:
            form_data = json.loads(self.custom_declaration_form_data or "{}")

            # Mapping: name → field
            field_map = {
                "Mediclaim Self, Spouse & Children (Below 60 years)": "amount",
                "Mediclaim Self (Senior Citizen - 60 years & above)": "amount3",
                "Parents (Below 60 years)": "mpAmount3",
                "Parents (Senior Citizen - 60 years & above)": "mpAmount4",
                "Preventive Checkup (Self + Family)": "mp5",
                "Preventive Checkup (Parents)": "mpAmount6",
                "Interest Paid On Home Loan": "hlAmount",
                "Investments In PF(Auto)": "pfValue",
                "Pension Scheme Investments & ULIP": "aValue2",
                "Housing Loan Principal Repayment": "bValue1",
                "PPF - Public Provident Fund": "amount4",
                "Home Loan Account Of National Housing Bank": "dValue1",
                "LIC- Life Insurance Premium Directly Paid By Employee": "eValue1",
                "NSC - National Saving Certificate": "fValue1",
                "Mutual Funds - Notified Under Clause 23D Of Section 10": "gValue1",
                "ELSS - Equity Link Saving Scheme Of Mutual Funds": "hValue1",
                "Tuition Fees For Full Time Education": "iValue1",
                "Fixed Deposits In Banks (Period As Per Income Tax Guidelines)": "jValue1",
                "5 Years Term Deposit An Account Under Post Office Term Deposit Rules": "kValue1",
                "Others": "kValue2",
                "(Medical treatment / insurance of handicapped dependant)": "fourValue",
                "Medical treatment (specified diseases only)": "fiveNumber",
                "Interest repayment of Loan for higher education": "sixNumber",
                "Deduction for Physically Disabled": "sevenNumber",
                "Donation U/S 80G": "eightNumber",
                "NPS Deduction U/S 80CCD(2)(Employer NPS deduction)": "nineNumber",
                "First HSG Loan Interest Ded.(80EE)": "tenNumber",
                "Contribution in National Pension Scheme": "elevenNumber",
                "Tax Incentive for Affordable Housing for Ded U/S 80EEA": "twelveNumber1",
                "Tax Incentives for Electric Vehicles for Ded U/S 80EEB": "fifteenNumber",
                "Donations/contribution made to a political party or an electoral trust": "sixteenNumber",
                "Interest on deposits in saving account for Ded U/S 80TTA": "seventeenNumber",
                "Interest on deposits in saving account for Ded U/S 80TTB": "eighteenNumber",
                "P.T. Paid by employee": "nineteenNumber",
                "Deduction U/S 80GG": "twentyNumber",
                "Rajiv Gandhi Equity Saving Scheme 80CCG": "twentyoneNumber",
                "Uniform Allowance": "twentyFour",
                "Education Allowance": "thirteen",
                "Hostel Allowance": "twentysix",
                "Gratuity": "twentyseven",
                "LTA U/s 10 (5)": "twentyeight",
            }

            for row in self.declarations:
                key = field_map.get(row.exemption_sub_category)
                if key:
                    form_data[key] = round(row.amount)

            self.custom_declaration_form_data = json.dumps(form_data)


    # -----------validate section10 components on employee is eligible or not----------------

    def validation_on_section10(self):
        if self.custom_tax_regime != "Old Regime":
            return

        ss_assignment = frappe.get_list(
            "Salary Structure Assignment",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "company": self.company,
                "custom_payroll_period": self.payroll_period,
            },
            fields=["name", "from_date", "salary_structure"],
            order_by="from_date desc",
            limit=1,
        )

        if not ss_assignment:
            return

        salary_slip_preview = make_salary_slip(
            source_name=ss_assignment[0].salary_structure,
            employee=self.employee,
            print_format="Salary Slip Standard",
            posting_date=ss_assignment[0].from_date,
            for_preview=1,
        )
        # if salary_slip_preview:

        for component in salary_slip_preview.earnings:
            if component and component not in available_components:
                frappe.throw(f"You are not eligible to declare {allowances[key]}")





    def set_total_exemption_amount(self):

        self.total_exemption_amount = flt(
            get_total_exemption_amount(self.declarations),
            self.precision("total_exemption_amount"),
        )
        # frappe.msgprint(str(self.total_exemption_amount))
        if self.annual_hra_exemption:
            self.total_exemption_amount = (
                self.total_exemption_amount + self.annual_hra_exemption
            )


    def on_cancel(self):
        self.cancel_declaration_history()

    def cancel_declaration_history(self):
        history_data = frappe.db.get_list(
            "Tax Declaration History",
            filters={
                "tax_exemption": self.name,
            },
            fields=["*"],
        )

        if len(history_data) > 0:
            data_doc = frappe.get_doc("Tax Declaration History", history_data[0].name)
            frappe.delete_doc("Tax Declaration History", data_doc.name)

    def update_hra_breakup(self):
        if self.monthly_house_rent:
            if self.custom_status in ["Approved"]:
                array = []
                for t1 in self.custom_hra_breakup:
                    array.append(
                        {
                            "month": t1.month,
                            "rent_paid": t1.rent_paid,
                            "basic": t1.earned_basic,
                            "hra": t1.hra_received,
                            "basic_excess": t1.exemption_amount,
                            "exception_amount": t1.exemption_amount,
                        }
                    )

                get_latest_history = frappe.get_list(
                    "Tax Declaration History",
                    filters={"employee": self.employee},
                    fields=["*"],
                    order_by="posting_date desc",
                    limit=1,
                )

                if len(get_latest_history) > 0:
                    each_doc = frappe.get_doc(
                        "Tax Declaration History", get_latest_history[0].name
                    )

                    each_doc.monthly_house_rent = self.monthly_house_rent
                    each_doc.rented_in_metro_city = self.rented_in_metro_city
                    each_doc.hra_as_per_salary_structure = self.salary_structure_hra
                    each_doc.annual_hra_exemption = self.annual_hra_exemption
                    each_doc.monthly_hra_exemption = self.monthly_hra_exemption

                    each_doc.hra_breakup = []

                    for entry in array:
                        each_doc.append(
                            "hra_breakup",
                            {
                                "month": entry["month"],
                                "rent_paid": entry["rent_paid"],
                                "earned_basic": entry["basic"],
                                "hra_received": entry["hra"],
                                "excess_of_rent_paid": entry["basic_excess"],
                                "exemption_amount": entry["exception_amount"],
                            },
                        )

                    each_doc.save()
                    frappe.db.commit()

    def update_tax_declaration(self):
        if self.custom_status in ["Approved"]:
            if len(self.declarations) > 0:
                tax_component = []
                for component in self.declarations:
                    tax_component.append(
                        {
                            "sub_category": component.exemption_sub_category,
                            "category": component.exemption_category,
                            "max_amount": component.max_amount,
                            "amount": component.amount,
                        }
                    )

                hra_component = []
                for hra in self.custom_hra_breakup:
                    hra_component.append(
                        {
                            "month": hra.month,
                            "rent_paid": hra.rent_paid,
                            "earned_basic": hra.earned_basic,
                            "hra_received": hra.hra_received,
                            "excess_of_rent_paid": hra.excess_of_rent_paid,
                            "exemption_amount": hra.exemption_amount,
                        }
                    )

                get_latest_history = frappe.get_list(
                    "Tax Declaration History",
                    filters={
                        "employee": self.employee,
                        "posting_date": self.custom_posting_date,
                    },
                    fields=["*"],
                    limit=1,
                )

                if len(get_latest_history) > 0:
                    each_doc = frappe.get_doc(
                        "Tax Declaration History", get_latest_history[0].name
                    )

                    each_doc.rented_in_metro_city = self.rented_in_metro_city
                    each_doc.hra_as_per_salary_structure = self.salary_structure_hra
                    each_doc.annual_hra_exemption = self.annual_hra_exemption
                    each_doc.monthly_hra_exemption = self.monthly_hra_exemption
                    each_doc.total_declared_amount = self.total_declared_amount
                    each_doc.total_exemption_amount = self.total_exemption_amount
                    each_doc.income_tax = self.custom_income_tax
                    each_doc.monthly_house_rent = self.monthly_house_rent

                    each_doc.declaration_details = []
                    for entry in tax_component:
                        each_doc.append(
                            "declaration_details",
                            {
                                "exemption_sub_category": entry["sub_category"],
                                "exemption_category": entry["category"],
                                "maximum_exempted_amount": entry["max_amount"],
                                "declared_amount": entry["amount"],
                            },
                        )

                    each_doc.hra_breakup = []
                    for hra_entry in hra_component:
                        each_doc.append(
                            "hra_breakup",
                            {
                                "month": hra_entry["month"],
                                "rent_paid": hra_entry["rent_paid"],
                                "earned_basic": hra_entry["earned_basic"],
                                "hra_received": hra_entry["hra_received"],
                                "excess_of_rent_paid": hra_entry["excess_of_rent_paid"],
                                "exemption_amount": hra_entry["exemption_amount"],
                            },
                        )

                    each_doc.save()
                    frappe.db.commit()

                else:
                    insert_history = frappe.get_doc(
                        {
                            "doctype": "Tax Declaration History",
                            "employee": self.employee,
                            "employee_name": self.employee_name,
                            "income_tax": self.custom_income_tax,
                            "company": self.company,
                            "posting_date": self.custom_posting_date,
                            "payroll_period": self.payroll_period,
                            "tax_exemption": self.name,
                            "total_declared_amount": self.total_declared_amount,
                            "total_exemption_amount": self.total_exemption_amount,
                            "monthly_house_rent": self.monthly_house_rent,
                            "rented_in_metro_city": self.rented_in_metro_city,
                            "hra_as_per_salary_structure": self.salary_structure_hra,
                            "annual_hra_exemption": self.annual_hra_exemption,
                            "monthly_hra_exemption": self.monthly_hra_exemption,
                            "declaration_details": [
                                {
                                    "exemption_sub_category": entry["sub_category"],
                                    "exemption_category": entry["category"],
                                    "maximum_exempted_amount": entry["max_amount"],
                                    "declared_amount": entry["amount"],
                                }
                                for entry in tax_component
                            ],
                            "hra_breakup": [
                                {
                                    "month": hra_entry["month"],
                                    "rent_paid": hra_entry["rent_paid"],
                                    "earned_basic": hra_entry["earned_basic"],
                                    "hra_received": hra_entry["hra_received"],
                                    "excess_of_rent_paid": hra_entry[
                                        "excess_of_rent_paid"
                                    ],
                                    "exemption_amount": hra_entry["exemption_amount"],
                                }
                                for hra_entry in hra_component
                            ],
                        }
                    )

                    insert_history.insert()
                    frappe.db.commit()

    def insert_declaration_history(self):
        if self.employee:
            declaration_details = []
            hra_breakup = []

            for i in self.declarations:
                declaration_details.append(
                    {
                        "exemption_sub_category": i.exemption_sub_category,
                        "exemption_category": i.exemption_category,
                        "maximum_exempted_amount": i.max_amount,
                        "declared_amount": i.amount,
                    }
                )

            for j in self.custom_hra_breakup:
                hra_breakup.append(
                    {
                        "month": j.month,
                        "rent_paid": j.rent_paid,
                        "earned_basic": j.earned_basic,
                        "hra_received": j.hra_received,
                        "excess_of_rent_paid": j.excess_of_rent_paid,
                        "exemption_amount": j.exemption_amount,
                    }
                )

            insert_doc = frappe.get_doc(
                {
                    "doctype": "Tax Declaration History",
                    "employee": self.employee,
                    "employee_name": self.employee_name,
                    "income_tax": self.custom_income_tax,
                    "company": self.company,
                    "posting_date": frappe.utils.nowdate(),
                    "payroll_period": self.payroll_period,
                    "monthly_house_rent": self.monthly_house_rent,
                    "rented_in_metro_city": self.rented_in_metro_city,
                    "hra_as_per_salary_structure": self.salary_structure_hra,
                    "total_declared_amount": self.total_declared_amount,
                    "annual_hra_exemption": self.annual_hra_exemption,
                    "monthly_hra_exemption": self.monthly_hra_exemption,
                    "total_exemption_amount": self.total_exemption_amount,
                    "tax_exemption": self.name,
                    "declaration_details": declaration_details,
                    "hra_breakup": hra_breakup,
                }
            )

            insert_doc.insert()

    # --------Insert HRA Breakup Table & Annual HRA and Basic----------------

    def calculate_hra_breakup(self):
        if self.monthly_house_rent and self.custom_check == 0:
            get_company = frappe.get_doc("Company", self.company)
            basic_component = get_company.basic_component
            hra_component = get_company.hra_component

            ss_assignment = frappe.get_list(
                "Salary Structure Assignment",
                filters={
                    "employee": self.employee,
                    "docstatus": 1,
                    "company": self.company,
                    "custom_payroll_period": self.payroll_period,
                },
                fields=[
                    "name",
                    "from_date",
                    "custom_payroll_period",
                    "salary_structure",
                ],
                order_by="from_date desc",
            )

            if ss_assignment:
                first_assignment = next(iter(ss_assignment))
                first_assignment_date = first_assignment.get("from_date")
                first_assignment_structure = first_assignment.get("salary_structure")

                start_date = ss_assignment[-1].from_date
                if ss_assignment[-1].custom_payroll_period:
                    payroll_period = frappe.get_doc(
                        "Payroll Period", ss_assignment[-1].custom_payroll_period
                    )
                    end_date = payroll_period.end_date
                    month_count = (
                        (end_date.year - start_date.year) * 12
                        + end_date.month
                        - start_date.month
                        + 1
                    )

                    cur_basic_amount = 0
                    cur_hra_amount = 0
                    get_salary_slip = frappe.get_list(
                        "Salary Slip",
                        filters={
                            "employee": self.employee,
                            "docstatus": 1,
                            "company": self.company,
                            "custom_payroll_period": self.payroll_period,
                        },
                        fields=["name"],
                    )
                    if len(get_salary_slip) > 0:
                        ss_slip_month_count = len(get_salary_slip)

                        for salary_slip in get_salary_slip:
                            get_salary_doc = frappe.get_doc(
                                "Salary Slip", salary_slip.name
                            )
                            for component in get_salary_doc.earnings:
                                if component.salary_component == basic_component:
                                    cur_basic_amount += component.amount
                                elif component.salary_component == hra_component:
                                    cur_hra_amount += component.amount
                    else:
                        ss_slip_month_count = 0
                    futute_month_count = month_count - ss_slip_month_count

                    new_salary_slip = make_salary_slip(
                        source_name=first_assignment_structure,
                        employee=self.employee,
                        print_format="Salary Slip Standard for CTC",
                        posting_date=first_assignment_date,
                        for_preview=1,
                    )
                    future_basic_amount = 0
                    future_hra_amount = 0

                    for new_earning in new_salary_slip.earnings:
                        if new_earning.salary_component == basic_component:
                            future_basic_amount = (
                                new_earning.amount * futute_month_count
                            ) + cur_basic_amount

                        if new_earning.salary_component == hra_component:
                            future_hra_amount = (
                                new_earning.amount * futute_month_count
                            ) + cur_hra_amount

                    self.salary_structure_hra = round(future_hra_amount)
                    self.custom_basic = round(future_basic_amount)
                    percentage_basic = (future_basic_amount * 10) / 100
                    self.custom_basic_as_per_salary_structure = round(percentage_basic)

                    annual_hra_amount = self.monthly_house_rent * month_count

                    basic_rule2 = round(annual_hra_amount - percentage_basic)
                    if self.rented_in_metro_city == 0:
                        non_metro_or_metro = (future_basic_amount * 40) / 100
                    elif self.rented_in_metro_city == 1:
                        non_metro_or_metro = (future_basic_amount * 50) / 100

                    final_hra_exemption = round(
                        min(basic_rule2, future_hra_amount, non_metro_or_metro)
                    )

                    self.annual_hra_exemption = round(final_hra_exemption)
                    self.monthly_hra_exemption = round(
                        final_hra_exemption / month_count
                    )

                    months = []
                    current_date = start_date

                    while current_date <= end_date:
                        month_name = current_date.strftime("%B")
                        if month_name not in months:
                            months.append(month_name)
                        current_date = (
                            current_date.replace(day=28) + timedelta(days=4)
                        ).replace(day=1)

                    earned_basic = 0
                    if self.rented_in_metro_city == 1:
                        earned_basic = (
                            (self.custom_basic_as_per_salary_structure * 10) * 50 / 100
                        )
                    else:
                        earned_basic = (
                            (self.custom_basic_as_per_salary_structure * 10) * 40 / 100
                        )

                    self.custom_hra_breakup = []
                    for i in range(len(months)):
                        self.append(
                            "custom_hra_breakup",
                            {
                                "month": months[i],
                                "rent_paid": round(annual_hra_amount),
                                "hra_received": round(self.salary_structure_hra),
                                "earned_basic": round(earned_basic),
                                "excess_of_rent_paid": round(basic_rule2),
                                "exemption_amount": final_hra_exemption,
                            },
                        )

        elif self.monthly_house_rent == 0  or self.monthly_house_rent == None and self.custom_check == 0:
            self.custom_basic_as_per_salary_structure = None
            self.salary_structure_hra = None
            self.custom_basic = None
            self.custom_hra_breakup = []
            self.annual_hra_exemption = None
            self.monthly_hra_exemption = None
        elif self.monthly_house_rent == 0  or self.monthly_house_rent == None and self.custom_check == 1:
            self.custom_basic_as_per_salary_structure = None
            self.salary_structure_hra = None
            self.custom_basic = None
            self.custom_hra_breakup = []
            self.annual_hra_exemption = None
            self.monthly_hra_exemption = None
