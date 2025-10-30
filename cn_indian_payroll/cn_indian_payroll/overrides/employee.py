import frappe


def validate(self, method):
    if self.custom_zone and self.custom_skill_level:
        frappe.msgprint("Calculating Minimum Wages based on Zone and Skill Level")
        salary_structure_assignments = frappe.db.get_list(
            "Salary Structure Assignment",
            filters={
                "employee": self.employee,
                "docstatus": 1
            },
            fields=["name", "custom_minimum_wages_state"],
            order_by="from_date desc",
            limit=1
        )

<<<<<<< HEAD
        self.set_cpl()
        self.reimbursement_amount()
        



    def set_cpl(self):
        components = ["Vehicle Maintenance Reimbursement", "Petrol Reimbursement", "Leave Travel Allowance"]
        array=[]
        
        if self.custom_employee_reimbursements:
            for i in self.custom_employee_reimbursements:
                if i.reimbursements in components:
                    
                    array.append(i.reimbursements)

            
            if len(array)==3:
                self.custom_is_car_petrol_lta=1
               
            else:
                self.custom_is_car_petrol_lta=0



    def reimbursement_amount(self):
        total_amount = 0
        if self.custom_employee_reimbursements:
            for reimbursement in self.custom_employee_reimbursements:
                total_amount += reimbursement.monthly_total_amount

        self.custom_statistical_amount = total_amount
        




                


    
                

                


            
        
        
        

       
                
=======
        if salary_structure_assignments:
            ssa = salary_structure_assignments[0]
>>>>>>> v2/dev/india_payroll

            if ssa.custom_minimum_wages_state:
                state = frappe.get_doc("State", ssa.custom_minimum_wages_state)

                if state.min_wages:
                    for row in state.min_wages:
                        if row.skill_level == self.custom_skill_level and row.zone == self.custom_zone:
                            self.custom_basic_value = row.basic_daily_wage
                            self.custom_vda_value = row.vda_daily_wages
                            break
                        else:
                            self.custom_basic_value = 0
                            self.custom_vda_value = 0
    else:
        self.custom_basic_value = 0
        self.custom_vda_value = 0
