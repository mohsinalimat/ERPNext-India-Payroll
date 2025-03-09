import frappe
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry


class CustomPayrollEntry(PayrollEntry):


    def on_cancel(self):
        self.delete_benefit_accrual()

    def delete_benefit_accrual(self):
        data=frappe.db.get_list('Employee Benefit Accrual',
            filters={
                'docstatus': ['in', [0, 1]],
                'payroll_entry':self.name,
                },
            fields=['*'],
            
        )
        if len(data)>0:
            for i in data:
                data_doc=frappe.get_doc('Employee Benefit Accrual',i.name)
                if data_doc.docstatus==0:
                    frappe.delete_doc('Employee Benefit Accrual', data_doc.name)

                if data_doc.docstatus==1:
                    data_doc.docstatus=2
                    data_doc.save()
                    frappe.delete_doc('Employee Benefit Accrual', data_doc.name)



