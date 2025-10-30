frappe.ui.form.on('Loan Product', {
	onload(frm) {
<<<<<<< HEAD
            if(frm.is_new())
                {
                    frm.set_value("custom_loan_perquisite_threshold_amount",20000)
                }
=======
        if(frm.is_new() && frm.doc.custom_loan_perquisite_threshold_amount==0)
            {
                frm.set_value("custom_loan_perquisite_threshold_amount",20000)
            }
>>>>>>> v2/dev/india_payroll

            },







})
