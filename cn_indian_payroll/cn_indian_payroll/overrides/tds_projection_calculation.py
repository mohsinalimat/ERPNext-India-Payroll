import frappe
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from datetime import datetime
from frappe import _
import json



@frappe.whitelist()
def calculate_tds_projection(doc):

    loan_perquisite_component=None
    loan_perquisite_amount=0

    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))

    if doc.get('employee'):
        latest_salary_structure = frappe.get_list(
            "Salary Structure Assignment",
            filters={
                "employee": doc.get('employee'),
                "docstatus": 1,
                "custom_payroll_period": doc.get('payroll_period'),
            },
            fields=["*"],
            order_by="from_date desc",
        )

        if latest_salary_structure:
            assignment = latest_salary_structure[0]
            employee=frappe.get_doc("Employee", assignment.employee)
            get_payroll_period = frappe.get_doc("Payroll Period", assignment.custom_payroll_period)

            effective_start_date = assignment.from_date
            payroll_end_date = get_payroll_period.end_date
            payroll_start_date = get_payroll_period.start_date
            doj = employee.date_of_joining

            start_candidates = [d for d in [effective_start_date, payroll_start_date, doj] if d]
            start = max(datetime.strptime(str(d), "%Y-%m-%d").date() if isinstance(d, str) else d for d in start_candidates)
            end = datetime.strptime(str(payroll_end_date), "%Y-%m-%d").date() if isinstance(payroll_end_date, str) else payroll_end_date

            num_months = (end.year - start.year) * 12 + (end.month - start.month) + 1

            loan_repayments = frappe.get_list(
                "Loan Repayment Schedule",
                filters={
                    "custom_employee": employee,
                    "status": "Active",
                    "docstatus": 1,
                },
                fields=["*"],
            )

            if loan_repayments:
                loan_perquisite_component="Loan Perquisite"
                for repayment in loan_repayments:
                    get_each_perquisite = frappe.get_doc(
                        "Loan Repayment Schedule", repayment.name
                    )
                    if len(get_each_perquisite.custom_loan_perquisite) > 0:
                        for date in get_each_perquisite.custom_loan_perquisite:
                            payment_date = frappe.utils.getdate(
                                date.payment_date
                            )
                            if payroll_start_date <= payment_date <= payroll_end_date:
                                loan_perquisite_amount += date.perquisite_amount

            else:
                loan_perquisite_component="Loan Perquisite"
                loan_perquisite_amount=0

        # get_all_salary_slip = frappe.get_list(
        #     "Salary Slip",
        #     filters={
        #         "employee": doc.get('employee'),
        #         "custom_payroll_period": doc.get('payroll_period'),
        #         "docstatus": ["in", [0, 1]],
        #     },
        #     fields=["*"],
        #     order_by="posting_date desc",
        # )
        # if len(get_all_salary_slip)==0:





























@frappe.whitelist()
def get_doc_data(doc_name, employee, company, payroll_period):
    old_taxable_component = 0
    new_taxable_component = 0

    old_future_amount = 0
    new_future_amount = 0

    perquisite_component = []
    perquisite_amount = []

    epf_amount = 0
    pt_amount = 0
    nps_amount = 0

    start = None
    end = None

    if employee:
        latest_salary_structure = frappe.get_list(
            "Salary Structure Assignment",
            filters={
                "employee": employee,
                "docstatus": 1,
                "custom_payroll_period": payroll_period,
            },
            fields=["*"],
            order_by="from_date desc",
            # limit=1
        )

        if len(latest_salary_structure) > 0:
            get_payroll_period = frappe.get_doc(
                "Payroll Period", latest_salary_structure[0].custom_payroll_period
            )
            effective_start_date = latest_salary_structure[-1].from_date
            payroll_end_date = get_payroll_period.end_date
            payroll_start_date = get_payroll_period.start_date
            doj = latest_salary_structure[0].custom_date_of_joining

            start_date = max(effective_start_date, payroll_start_date, doj)

            if isinstance(start_date, str):
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start = start_date

            if isinstance(payroll_end_date, str):
                end = datetime.strptime(payroll_end_date, "%Y-%m-%d").date()
            else:
                end = payroll_end_date

            num_months = (end.year - start.year) * 12 + (end.month - start.month) + 1

            if (
                latest_salary_structure[0].custom__car_perquisite == 1
                and latest_salary_structure[0].custom_car_perquisite_as_per_rules
            ):
                perquisite_amount.append(
                    latest_salary_structure[0].custom_car_perquisite_as_per_rules
                    * num_months
                )

                perquisite_component.append("Car Perquisite")
            else:
                perquisite_component.append("Car Perquisite")
                perquisite_amount.append(0)

            # DRIVER PERQUISITE
            old_regime_driver_perquisite = 0

            if (
                latest_salary_structure[0].custom_driver_provided_by_company == 1
                and latest_salary_structure[0].custom_driver_perquisite_as_per_rules
            ):
                perquisite_amount.append(
                    latest_salary_structure[0].custom_driver_perquisite_as_per_rules
                    * num_months
                )
                perquisite_component.append("Driver Perquisite")
            else:
                perquisite_component.append("Driver Perquisite")
                perquisite_amount.append(0)

            # LOAN PERQUISITE
            annual_perquisite = 0

            if payroll_period:
                get_payroll_period_period = frappe.get_list(
                    "Payroll Period",
                    filters={"company": company, "name": payroll_period},
                    fields=["*"],
                )

                if get_payroll_period_period:
                    start_date = frappe.utils.getdate(get_payroll_period_period[0].start_date)
                    end_date = frappe.utils.getdate(get_payroll_period_period[0].end_date)

                    loan_repayments = frappe.get_list(
                        "Loan Repayment Schedule",
                        filters={
                            "custom_employee": employee,
                            "status": "Active",
                            "docstatus": 1,
                        },
                        fields=["*"],
                    )

                    if loan_repayments:
                        perquisite_component.append("Loan Perquisite")
                        for repayment in loan_repayments:
                            get_each_perquisite = frappe.get_doc(
                                "Loan Repayment Schedule", repayment.name
                            )
                            if len(get_each_perquisite.custom_loan_perquisite) > 0:
                                for date in get_each_perquisite.custom_loan_perquisite:
                                    payment_date = frappe.utils.getdate(
                                        date.payment_date
                                    )
                                    if start_date <= payment_date <= end_date:
                                        annual_perquisite += date.perquisite_amount

                        perquisite_amount.append(annual_perquisite)

                    else:
                        perquisite_component.append("Loan Perquisite")
                        perquisite_amount.append(0)

        accrued_data = {}

        accrued_component_array = []

        get_company_doc = frappe.get_doc("Company", company)
        if get_company_doc.custom_accrued_component:
            for accrued_component in get_company_doc.custom_accrued_component:
                accrued_component_array.append(accrued_component.accrued_componets)
        else:
            accrued_component_array = []

        get_accrued_bonus = frappe.get_list(
            "Employee Bonus Accrual",
            filters={
                "docstatus": 1,
                "is_paid": 0,
                "employee": employee,
                "salary_component": ["in", accrued_component_array],
            },
            fields=["salary_component", "amount"],
        )

        if get_accrued_bonus:
            for bonus in get_accrued_bonus:
                if bonus.salary_component in accrued_data:
                    accrued_data[bonus.salary_component] += bonus.amount
                else:
                    accrued_data[bonus.salary_component] = bonus.amount

                    # Convert to list of dicts if needed
        accrued_data_list = [
            {"component": k, "amount": v, "future_amount": 0}
            for k, v in accrued_data.items()
        ]

        get_all_salary_slip = frappe.get_list(
            "Salary Slip",
            filters={
                "employee": employee,
                "custom_payroll_period": payroll_period,
                "docstatus": ["in", [0, 1]],
            },
            fields=["*"],
            order_by="posting_date desc",
        )

        if len(get_all_salary_slip) > 0:
            salary_slip_count = len(get_all_salary_slip)

            end_month_name = get_all_salary_slip[0].get("custom_month")
            start_month_name = get_all_salary_slip[-1].get("custom_month")

            for salary_list in get_all_salary_slip:
                get_salary_doc = frappe.get_doc("Salary Slip", salary_list.name)

                for component in get_salary_doc.earnings:
                    taxable_component = frappe.get_doc(
                        "Salary Component", component.salary_component
                    )

                    # All Basic Taxable Components
                    if (
                        taxable_component.is_tax_applicable == 1
                        and taxable_component.custom_perquisite == 0
                        and taxable_component.custom_tax_exemption_applicable_based_on_regime
                        == 1
                        and taxable_component.custom_regime == "All"
                    ):
                        old_taxable_component += component.amount
                        new_taxable_component += component.amount

                    # Food Coupon - Old Regime
                    if (
                        taxable_component.is_tax_applicable == 1
                        and taxable_component.custom_perquisite == 0
                        and taxable_component.custom_tax_exemption_applicable_based_on_regime
                        == 1
                        and taxable_component.custom_regime == "Old Regime"
                    ):
                        old_taxable_component += component.amount

                    # Food Coupon - New Regime
                    if (
                        taxable_component.is_tax_applicable == 1
                        and taxable_component.custom_perquisite == 0
                        and taxable_component.custom_tax_exemption_applicable_based_on_regime
                        == 1
                        and taxable_component.custom_regime == "New Regime"
                    ):
                        new_taxable_component += component.amount

                    # NPS
                    if (
                        taxable_component.is_tax_applicable == 1
                        and taxable_component.component_type == "NPS"
                    ):
                        nps_amount += component.amount

                for deduction in get_salary_doc.deductions:
                    taxable_component = frappe.get_doc(
                        "Salary Component", deduction.salary_component
                    )
                    # EPF
                    if taxable_component.component_type == "Provident Fund":
                        epf_amount += deduction.amount
                    # PT
                    if taxable_component.component_type == "Professional Tax":
                        pt_amount += deduction.amount

        else:
            salary_slip_count = 0
            start_month_name = start.strftime("%B")
            end_month_name = end.strftime("%B")

        new_salary_slip = make_salary_slip(
            source_name=latest_salary_structure[0].salary_structure,
            employee=employee,
            print_format="Salary Slip Standard",
            for_preview=1,
            posting_date=latest_salary_structure[0].from_date,
        )

        processed_components = set()

        for new_earning in new_salary_slip.earnings:
            taxable_component = frappe.get_doc(
                "Salary Component", new_earning.salary_component
            )

            if taxable_component.name in processed_components:
                continue

            # STANDARD COMPONENT
            if (
                taxable_component.is_tax_applicable == 1
                and taxable_component.custom_perquisite == 0
                and taxable_component.custom_tax_exemption_applicable_based_on_regime
                == 1
                and taxable_component.custom_regime == "All"

            ):
                old_future_amount += new_earning.amount * (
                    num_months - salary_slip_count
                )
                new_future_amount += new_earning.amount * (
                    num_months - salary_slip_count
                )

            if taxable_component.custom_is_accrual == 1:
                component_name = taxable_component.name
                monthly_bonus = new_earning.amount
                annual_bonus_amount = monthly_bonus * 12

                # Find and update the existing item in accrued_data_list
                found = False
                for item in accrued_data_list:
                    if item["component"] == component_name:
                        item["future_amount"] = annual_bonus_amount - item["amount"]
                        found = True
                        break

                # If not found, assume accrued = 0 and add a new entry
                if not found:
                    accrued_data_list.append(
                        {
                            "component": component_name,
                            "amount": 0,
                            "future_amount": annual_bonus_amount,
                        }
                    )

                # FOOD COUPON
            if (
                taxable_component.is_tax_applicable == 1
                and taxable_component.custom_perquisite == 0
                and taxable_component.custom_tax_exemption_applicable_based_on_regime
                == 1
                and taxable_component.custom_regime == "Old Regime"

            ):
                old_future_amount += new_earning.amount * (
                    num_months - salary_slip_count
                )

            if (
                taxable_component.is_tax_applicable == 1
                and taxable_component.custom_perquisite == 0
                and taxable_component.custom_tax_exemption_applicable_based_on_regime
                == 1
                and taxable_component.custom_regime == "New Regime"

            ):
                new_future_amount += new_earning.amount * (
                    num_months - salary_slip_count
                )

                # NPS
            if (
                taxable_component.is_tax_applicable == 1
                and taxable_component.component_type == "NPS"

            ):
                nps_amount += new_earning.amount * (num_months - salary_slip_count)

            processed_components.add(taxable_component.name)

        for deduction in new_salary_slip.deductions:
            taxable_component = frappe.get_doc(
                "Salary Component", deduction.salary_component
            )

            if taxable_component.name in processed_components:
                continue

            # EPF
            if (
                taxable_component.component_type == "Provident Fund"

            ):
                epf_amount += deduction.amount * (num_months - salary_slip_count)

                # Professional Tax
            if (
                taxable_component.component_type == "Professional Tax"

            ):
                pt_amount += deduction.amount * (num_months - salary_slip_count)

            processed_components.add(taxable_component.name)

        # frappe.msgprint(str(old_future_amount))
        latest_tax_slab = frappe.get_list(
            "Income Tax Slab",
            filters={
                "company": company,
                "docstatus": 1,
                "disabled": 0,
                "custom_select_regime": "Old Regime",
            },
            fields=["name", "custom_select_regime", "standard_tax_exemption_amount"],
            order_by="effective_from DESC",
            limit=1,
        )

        old_standard_value = 0

        if latest_tax_slab:
            for slab in latest_tax_slab:
                old_standard_value = slab.standard_tax_exemption_amount

        latest_tax_slab = frappe.get_list(
            "Income Tax Slab",
            filters={
                "company": company,
                "docstatus": 1,
                "disabled": 0,
                "custom_select_regime": "New Regime",
            },
            fields=["name", "custom_select_regime", "standard_tax_exemption_amount"],
            order_by="effective_from DESC",
            limit=1,
        )

        new_standard_value = 0

        if latest_tax_slab:
            for slab in latest_tax_slab:
                new_standard_value = slab.standard_tax_exemption_amount

    return {
        "from_month": start_month_name,
        "to_month": end_month_name,
        "current_old_value": old_taxable_component,
        "current_new_value": new_taxable_component,
        "future_old_value": old_future_amount,
        "future_new_value": new_future_amount,
        "perquisite_component": perquisite_component,
        "perquisite_amount": perquisite_amount,
        "old_standard": old_standard_value,
        "new_standard": new_standard_value,
        "pt": pt_amount,
        "nps": nps_amount,
        "epf": epf_amount,
        "num_months": num_months,
        "salary_slip_count": salary_slip_count,
        "accrued_data_list": accrued_data_list,
    }


@frappe.whitelist()
def slab_calculation(
    employee, company, payroll_period, old_annual_slab, new_annual_slab
):
    old_annual_slab = float(old_annual_slab)
    new_annual_slab = float(new_annual_slab)

    latest_tax_slab = frappe.get_list(
        "Income Tax Slab",
        filters={
            "company": company,
            "docstatus": 1,
            "disabled": 0,
            "custom_select_regime": "Old Regime",
        },
        fields=["*"],
        order_by="effective_from DESC",
        limit=1,
    )

    if latest_tax_slab:
        for slab in latest_tax_slab:
            income_doc = frappe.get_doc("Income Tax Slab", slab.name)

            total_value = []
            from_amount = []
            to_amount = []
            percentage = []
            difference = []
            total_array = []

            total_sum = 0
            old_rebate_value = 0
            old_surcharge_m = 0
            old_education_cess = 0

            old_regime_marginal_relief_min_value = 0
            old_regime_marginal_relief_max_value = 0


            old_rebate = income_doc.custom_taxable_income_is_less_than
            old_max_amount = income_doc.custom_maximum_amount

            if (
                income_doc.custom_marginal_relief_applicable
                and income_doc.custom_minmum_value
                and income_doc.custom_maximun_value
            ):
                old_regime_marginal_relief_min_value = income_doc.custom_minmum_value
                old_regime_marginal_relief_max_value = income_doc.custom_maximun_value

            if old_annual_slab > old_rebate:
                # Store all slab details in a structured list
                for i in income_doc.slabs:
                    total_array.append(
                        {
                            "from": i.from_amount,
                            "to": i.to_amount,
                            "percent": i.percent_deduction,
                        }
                    )

                # Iterate through the slabs to calculate tax
                for slab in total_array:
                    if slab["to"] == 0.0:  # Upper limit not defined
                        if round(old_annual_slab) >= slab["from"]:
                            taxable_amount = round(old_annual_slab) - slab["from"]

                            tax_percent = slab["percent"]
                            tax_amount = round((taxable_amount * tax_percent) / 100)

                            remaining_slabs = [
                                s for s in total_array if s["from"] < slab["from"]
                            ]
                            for rem_slab in remaining_slabs:
                                from_amount.append(rem_slab["from"])
                                to_amount.append(rem_slab["to"])
                                percentage.append(rem_slab["percent"])
                                difference.append(rem_slab["to"] - rem_slab["from"])
                                total_value.append(
                                    round(
                                        (rem_slab["to"] - rem_slab["from"])
                                        * rem_slab["percent"]
                                        / 100
                                    )
                                )

                            from_amount.append(slab["from"])
                            to_amount.append(slab["to"])
                            percentage.append(tax_percent)
                            difference.append(taxable_amount)
                            total_value.append(tax_amount)

                    else:  # Standard slab range
                        if slab["from"] <= round(old_annual_slab) <= slab["to"]:
                            taxable_amount = round(old_annual_slab) - slab["from"]
                            tax_percent = slab["percent"]
                            tax_amount = round((taxable_amount * tax_percent) / 100)

                            # Process lower slabs
                            remaining_slabs = [
                                s for s in total_array if s["from"] < slab["from"]
                            ]
                            for rem_slab in remaining_slabs:
                                from_amount.append(rem_slab["from"])
                                to_amount.append(rem_slab["to"])
                                percentage.append(rem_slab["percent"])
                                difference.append(rem_slab["to"] - rem_slab["from"])
                                total_value.append(
                                    round(
                                        (rem_slab["to"] - rem_slab["from"])
                                        * rem_slab["percent"]
                                        / 100
                                    )
                                )

                            from_amount.append(slab["from"])
                            to_amount.append(slab["to"])
                            percentage.append(tax_percent)
                            difference.append(taxable_amount)
                            total_value.append(tax_amount)

                total_sum = sum(total_value)

                final_value = 0
                if (
                    income_doc.custom_marginal_relief_applicable
                    and income_doc.custom_minmum_value
                    and income_doc.custom_maximun_value
                ):
                    if (
                        income_doc.custom_minmum_value
                        < old_annual_slab
                        < income_doc.custom_maximun_value
                    ):
                        old_rebate_value = total_sum - (
                            old_annual_slab - income_doc.custom_minmum_value
                        )
                        final_value = total_sum - old_rebate_value

                        old_education_cess = final_value * 4 / 100

                    else:
                        if old_annual_slab < old_rebate:
                            old_rebate_value = total_sum

                        else:
                            old_rebate_value = 0

                        if old_annual_slab > 5000000:
                            old_surcharge_m = round((total_sum * 10) / 100)
                            old_education_cess = round(
                                (old_surcharge_m + total_sum) * 4 / 100
                            )

                        else:
                            old_surcharge_m = 0
                            old_education_cess = round((0 + total_sum) * 4 / 100)
                else:
                    if old_annual_slab < old_rebate:
                        old_rebate_value = total_sum

                    else:
                        old_rebate_value = 0

                    if old_annual_slab > 5000000:
                        old_surcharge_m = round((total_sum * 10) / 100)
                        old_education_cess = round(
                            (old_surcharge_m + total_sum) * 4 / 100
                        )

                    else:
                        old_surcharge_m = 0
                        old_education_cess = round((0 + total_sum) * 4 / 100)
            else:
                old_rebate_value = 0
                old_surcharge_m = 0
                old_education_cess = 0

    latest_tax_slab_new = frappe.get_list(
        "Income Tax Slab",
        filters={
            "company": company,
            "docstatus": 1,
            "disabled": 0,
            "custom_select_regime": "New Regime",
        },
        fields=["name", "custom_select_regime", "standard_tax_exemption_amount"],
        order_by="effective_from DESC",
        limit=1,
    )

    if latest_tax_slab_new:
        for slab_new in latest_tax_slab_new:
            income_doc_new = frappe.get_doc("Income Tax Slab", slab_new.name)

            # Initialize Lists
            total_value_new = []
            from_amount_new = []
            to_amount_new = []
            percentage_new = []
            difference_new = []
            total_array_new = []

            total_sum_new = 0  # Initialize early to avoid UnboundLocalError
            new_rebate_value = 0
            new_surcharge_m = 0
            new_education_cess = 0

            new_regime_marginal_relief_min_value = 0
            new_regime_marginal_relief_max_value = 0

            # Retrieve Exemption & Maximum Values
            new_rebate = income_doc_new.custom_taxable_income_is_less_than
            new_max_amount = income_doc_new.custom_maximum_amount

            if (
                income_doc_new.custom_marginal_relief_applicable
                and income_doc_new.custom_minmum_value
                and income_doc_new.custom_maximun_value
            ):
                new_regime_marginal_relief_min_value = (
                    income_doc_new.custom_minmum_value
                )
                new_regime_marginal_relief_max_value = (
                    income_doc_new.custom_maximun_value
                )

            if new_annual_slab > new_rebate:
                # Store all slab details in a structured list
                for i in income_doc_new.slabs:
                    total_array_new.append(
                        {
                            "from": i.from_amount,
                            "to": i.to_amount,
                            "percent": i.percent_deduction,
                        }
                    )

                for slab_new in total_array_new:
                    if slab_new["to"] == 0.0:  # Upper limit not defined
                        if round(new_annual_slab) >= slab_new["from"]:
                            taxable_amount_new = (
                                round(new_annual_slab) - slab_new["from"]
                            )
                            tax_percent_new = slab_new["percent"]
                            tax_amount_new = round(
                                (taxable_amount_new * tax_percent_new) / 100
                            )

                            remaining_slabs_new = [
                                s
                                for s in total_array_new
                                if s["from"] < slab_new["from"]
                            ]
                            for rem_slab in remaining_slabs_new:
                                from_amount_new.append(rem_slab["from"])
                                to_amount_new.append(rem_slab["to"])
                                percentage_new.append(rem_slab["percent"])
                                difference_new.append(rem_slab["to"] - rem_slab["from"])
                                total_value_new.append(
                                    round(
                                        (rem_slab["to"] - rem_slab["from"])
                                        * rem_slab["percent"]
                                        / 100
                                    )
                                )

                            from_amount_new.append(slab_new["from"])
                            to_amount_new.append(slab_new["to"])
                            percentage_new.append(tax_percent_new)
                            difference_new.append(taxable_amount_new)
                            total_value_new.append(tax_amount_new)

                    else:  # Standard slab range
                        if slab_new["from"] <= round(new_annual_slab) <= slab_new["to"]:
                            taxable_amount_new = (
                                round(new_annual_slab) - slab_new["from"]
                            )
                            tax_percent_new = slab_new["percent"]
                            tax_amount_new = round(
                                (taxable_amount_new * tax_percent_new) / 100
                            )

                            # Process lower slabs
                            remaining_slabs = [
                                s
                                for s in total_array_new
                                if s["from"] < slab_new["from"]
                            ]
                            for rem_slab in remaining_slabs:
                                from_amount_new.append(rem_slab["from"])
                                to_amount_new.append(rem_slab["to"])
                                percentage_new.append(rem_slab["percent"])
                                difference_new.append(rem_slab["to"] - rem_slab["from"])
                                total_value_new.append(
                                    round(
                                        (rem_slab["to"] - rem_slab["from"])
                                        * rem_slab["percent"]
                                        / 100
                                    )
                                )

                            from_amount_new.append(slab_new["from"])
                            to_amount_new.append(slab_new["to"])
                            percentage_new.append(tax_percent_new)
                            difference_new.append(taxable_amount_new)
                            total_value_new.append(tax_amount_new)

                total_sum_new = sum(total_value_new)

                if (
                    income_doc_new.custom_marginal_relief_applicable
                    and income_doc_new.custom_minmum_value
                    and income_doc_new.custom_maximun_value
                ):
                    if (
                        income_doc_new.custom_minmum_value
                        < new_annual_slab
                        < income_doc_new.custom_maximun_value
                    ):
                        new_rebate_value = total_sum_new - (
                            new_annual_slab - income_doc_new.custom_minmum_value
                        )
                        final_value = total_sum_new - new_rebate_value

                        new_education_cess = final_value * 4 / 100

                    else:
                        if new_annual_slab < new_rebate:
                            new_rebate_value = total_sum_new

                        else:
                            new_rebate_value = 0

                        if new_annual_slab > 5000000:
                            new_surcharge_m = round((total_sum_new * 10) / 100)
                            new_education_cess = round(
                                (new_surcharge_m + total_sum_new) * 4 / 100
                            )

                        else:
                            new_surcharge_m = 0
                            new_education_cess = round((0 + total_sum_new) * 4 / 100)

                else:
                    if new_annual_slab < new_rebate:
                        new_rebate_value = total_sum_new

                    else:
                        new_rebate_value = 0

                    if new_annual_slab > 5000000:
                        new_surcharge_m = round((total_sum_new * 10) / 100)
                        new_education_cess = round(
                            (new_surcharge_m + total_sum_new) * 4 / 100
                        )

                    else:
                        new_surcharge_m = 0
                        new_education_cess = round((0 + total_sum_new) * 4 / 100)

    tax_already_paid = 0

    get_all_salary_slip = frappe.get_list(
        "Salary Slip",
        filters={
            "employee": employee,
            "docstatus": ["in", [1]],
            "custom_payroll_period": payroll_period,
        },
        fields=["current_month_income_tax"],  # Fetch only the required field
    )

    # Sum up current_month_income_tax values
    tax_already_paid = sum(slip.current_month_income_tax for slip in get_all_salary_slip)

    return {
        "from_amount": from_amount,
        "to_amount": to_amount,
        "percentage": percentage,
        "total_value": total_value,
        "total_sum": total_sum,
        "rebate": old_rebate,
        "max_amount": old_max_amount,
        "old_rebate_value": old_rebate_value,
        "old_surcharge_m": old_surcharge_m,
        "old_education_cess": old_education_cess,
        "from_amount_new": from_amount_new,
        "to_amount_new": to_amount_new,
        "percentage_new": percentage_new,
        "total_value_new": total_value_new,
        "total_sum_new": total_sum_new,
        "rebate_new": new_rebate,
        "max_amount_new": new_max_amount,
        "new_regime_marginal_relief_min_value": new_regime_marginal_relief_min_value,
        "new_regime_marginal_relief_max_value": new_regime_marginal_relief_max_value,
        "old_regime_marginal_relief_min_value": old_regime_marginal_relief_min_value,
        "old_regime_marginal_relief_max_value": old_regime_marginal_relief_max_value,
        "new_rebate_value": new_rebate_value,
        "new_surcharge_m": new_surcharge_m,
        "new_education_cess": new_education_cess,
        "tax_already_paid": tax_already_paid,
    }
