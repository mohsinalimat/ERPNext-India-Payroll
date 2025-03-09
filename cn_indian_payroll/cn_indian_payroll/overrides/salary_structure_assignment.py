import frappe
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import SalaryStructureAssignment

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from frappe.utils import getdate


class CustomSalaryStructureAssignment(SalaryStructureAssignment):


    def on_submit(self):
        self.insert_tax_declaration_list()
        self.update_employee_promotion()


   

    def on_cancel(self):
        self.cancel_declaration()

    def cancel_declaration(self):
        data=frappe.db.get_list('Employee Tax Exemption Declaration',
            filters={
                'payroll_period': self.custom_payroll_period,
                'docstatus': ['in', [0, 1]],
                'employee':self.employee,
                'custom_salary_structure_assignment':self.name,

            },
            fields=['*'],
            
        )
        if len(data)>0:
            data_doc=frappe.get_doc('Employee Tax Exemption Declaration',data[0].name)
            if data_doc.docstatus==0:
                frappe.delete_doc('Employee Tax Exemption Declaration', data_doc.name)

            if data_doc.docstatus==1:
                data_doc.docstatus=2
                data_doc.save()
                frappe.delete_doc('Employee Tax Exemption Declaration', data_doc.name)



    def update_employee_promotion(self):
        if self.custom_promotion_id:
            get_promotion_doc=frappe.get_doc("Employee Promotion",self.custom_promotion_id)
            get_promotion_doc.custom_new_salary_structure_assignment_id=self.name
            get_promotion_doc.custom_new_effective_from=self.from_date
            get_promotion_doc.revised_ctc=self.base
            get_promotion_doc.custom_status="Payroll Configured"
            get_promotion_doc.save()

            # get_promotion_doc.reload()

            # frappe.db.commit()



    def insert_tax_declaration_list(self):
        if self.employee:
            sub_category=[]
            get_payroll_period = frappe.get_doc("Payroll Period", self.custom_payroll_period)
            from_date = getdate(self.from_date)
            payroll_start_date = getdate(get_payroll_period.start_date)
            payroll_end_date=getdate(get_payroll_period.end_date)
            declaration_date = max(from_date, payroll_start_date)
            start_date=declaration_date
            end_date=payroll_end_date

            if isinstance(start_date, str):
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start = start_date  

            if isinstance(end_date, str):
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
            else:
                end = end_date  
            num_months = (end.year - start.year) * 12 + (end.month - start.month)+1

            new_salary_slip = make_salary_slip(
                            source_name=self.salary_structure,
                            employee=self.employee,
                            print_format='Salary Slip Standard for CTC',  
                            posting_date=self.from_date,
                            for_preview=1,
                        )
            

            if self.custom_tax_regime == "New Regime":
                for new_earning in new_salary_slip.earnings:
                    nps_component = frappe.get_doc("Salary Component", new_earning.salary_component)
                    if nps_component.component_type == "NPS":
                        nps_amount_year = new_earning.amount * num_months
                        nps_components = frappe.get_list('Employee Tax Exemption Sub Category',
                                                        filters={'custom_component_type': "NPS"},
                                                        fields=['name'])
                        for component in nps_components:
                            sub_category.append({
                                "sub_category": component.name,
                                "max_amount": nps_amount_year,
                                "amount": nps_amount_year
                            })

                get_all_declaration = frappe.get_list('Employee Tax Exemption Declaration',
                                                    filters={'employee': self.employee, 'payroll_period': self.custom_payroll_period, 'docstatus': ['in', [0, 1]]},
                                                    fields=['name'])

                if not get_all_declaration:
                    insert_declaration = frappe.get_doc({
                        'doctype': 'Employee Tax Exemption Declaration',
                        'employee': self.employee,
                        'company': self.company,
                        'payroll_period': self.custom_payroll_period,
                        'currency': self.currency,
                        'custom_income_tax': self.income_tax_slab,
                        'custom_salary_structure_assignment': self.name,
                        'custom_posting_date': self.from_date
                    })

                    for category in sub_category:
                        doc2_child1 = insert_declaration.append("declarations", {})
                        doc2_child1.exemption_sub_category = category["sub_category"]
                        doc2_child1.max_amount = category["max_amount"]
                        doc2_child1.amount = category["amount"]

                    insert_declaration.insert()
                    insert_declaration.submit()
                    frappe.db.commit()
                    frappe.msgprint("Tax Exemption declaration is created")
                else:
                    frappe.msgprint(f"Declaration for {self.custom_payroll_period} payroll period is already created") 

            if self.custom_tax_regime == "Old Regime":
                for new_earning in new_salary_slip.earnings:
                    earning_salary_component = frappe.get_doc("Salary Component", new_earning.salary_component)
                    if earning_salary_component.component_type == "NPS":
                        nps_amount_year = new_earning.amount * num_months
                        nps_components = frappe.get_list('Employee Tax Exemption Sub Category',
                                                        filters={'custom_component_type': "NPS"},
                                                        fields=['*'])
                        for component in nps_components:
                            sub_category.append({
                                "sub_category": component.name,
                                "max_amount": nps_amount_year,
                                "amount": nps_amount_year
                            })

                    

                for new_deduction in new_salary_slip.deductions:
                    deduction_salary_component = frappe.get_doc("Salary Component", new_deduction.salary_component)
                    if deduction_salary_component.component_type == "EPF":
                        epf_amount_year = new_deduction.amount * num_months
                        epf_components = frappe.get_list('Employee Tax Exemption Sub Category',
                                                        filters={'custom_component_type': "EPF"},
                                                        fields=['*'])
                        for component in epf_components:
                            sub_category.append({
                                "sub_category": component.name,
                                "max_amount": epf_amount_year,
                                "amount": epf_amount_year
                            })

                    if deduction_salary_component.component_type == "Professional Tax":
                        pt_amount_year = new_deduction.amount * num_months
                        pt_components = frappe.get_list('Employee Tax Exemption Sub Category',
                                                        filters={'custom_component_type': "Professional Tax"},
                                                        fields=['*'])
                        for component in pt_components:
                            sub_category.append({
                                "sub_category": component.name,
                                "max_amount": pt_amount_year,
                                "amount": pt_amount_year
                            })

                get_all_declaration = frappe.get_list('Employee Tax Exemption Declaration',
                                                    filters={'employee': self.employee, 'payroll_period': self.custom_payroll_period, 'docstatus': ['in', [0, 1]]},
                                                    fields=['name'])

                if not get_all_declaration:
                    insert_declaration = frappe.get_doc({
                        'doctype': 'Employee Tax Exemption Declaration',
                        'employee': self.employee,
                        'company': self.company,
                        'payroll_period': self.custom_payroll_period,
                        'currency': self.currency,
                        'custom_income_tax': self.income_tax_slab,
                        'custom_salary_structure_assignment': self.name,
                        'custom_posting_date': self.from_date
                    })

                    for category in sub_category:
                        doc2_child1 = insert_declaration.append("declarations", {})
                        doc2_child1.exemption_sub_category = category["sub_category"]
                        doc2_child1.max_amount = category["max_amount"]
                        doc2_child1.amount = category["amount"]

                    insert_declaration.insert()
                    insert_declaration.submit()
                    frappe.db.commit()
                    frappe.msgprint("Tax Exemption declaration is created")
                else:
                    frappe.msgprint(f"Declaration for {self.custom_payroll_period} payroll period is already created") 
 




                


    
                

                


            
        
        
        

       
                


