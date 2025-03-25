frappe.ui.form.on('Payroll Entry', {

    refresh(frm) 
    {
        if(frm.doc.docstatus==1)
            {
                frm.add_custom_button(__("View Salary Register"),function(frm)
                {

                    frappe.set_route("query-report", "Salary Register");
                })
            }

        if(frm.doc.custom_bonus_payment_mode=="Bonus Payout")

                {
                    if( frm.doc.custom_additional_salary_submitted==0)
                        {
                            
                            frm.page.clear_primary_action();

                        }
                    
                }


        if(frm.doc.salary_slips_created==1)
            {
            if (frm.doc.custom_bonus_payment_mode == "Bonus Accrual" && frm.doc.custom_bonus_accrual_created == 0)
                {

                    create_bonus_accrual_entry(frm)

                }


        }

    if(frm.doc.custom_bonus_accrual_created==1 && frm.doc.custom_bonus_accrual_submit==0)
        {

            if (frm.doc.custom_bonus_payment_mode == "Bonus Accrual" )
            {

            frm.add_custom_button(__("Submit Bonus Accrual"),function()
                {

                     frappe.call({

                        "method":"cn_indian_payroll.cn_indian_payroll.overrides.accrual_bonus.get_submit",
                        args:{

                                payroll_entry: frm.doc.name

                            },
                        callback :function(res)
                        {
                            if(res.message)
                                {
                                    frm.set_value("custom_bonus_accrual_submit",1)
                                    frm.save('Update');
                                }

                        }

            })
                    
                })

            }

           

        }



        if (frm.doc.custom_bonus_payment_mode == "Bonus Payout") 
            
            {

                if(frm.doc.custom_additional_salary_created==0 && frm.doc.custom_additional_salary_submitted==0&&frm.doc.employees.length>0)

                {
                    frm.add_custom_button(__('Create Additional Salary'), function() {
                    
                            frappe.call({
                                method: 'cn_indian_payroll.cn_indian_payroll.overrides.additional_salary.get_additional_salary',
                                args: {
                                    payroll_id:frm.doc.name,
                                    company:frm.doc.company
                                },
                                callback: function(response) {

                                    if(response.message)
                                    {
                                        frm.set_value("custom_additional_salary_created",1)
                                        frm.save();
                                    }
                               }
                            });
                        
                    });

                }
        }



        if (frm.doc.custom_bonus_payment_mode == "Bonus Payout") 
            
            {

                if(frm.doc.custom_additional_salary_created==1 &&frm.doc.custom_additional_salary_submitted==0 &&frm.doc.employees.length>0)

                {

                    frm.add_custom_button(__("Submit Additional Salary"),function()
                    {
                        
    
                        frappe.call({
    
                            "method":"cn_indian_payroll.cn_indian_payroll.overrides.additional_salary.additional_salary_submit",
                            args:{
    
                                additional: frm.doc.name
    
                            },
                            callback :function(res)
                            {

                                
                                        frm.set_value("custom_additional_salary_submitted",1)
                                        frm.save();
                                        
                            }
    
                        })
                        
                    })




                }
            }


    },


    after_save(frm)
    {
        if(frm.doc.custom_bonus_accrual_created==1 && frm.doc.custom_bonus_accrual_submit==0)
            {
                msgprint("Employee Bonus Accrual Created")


            }


            if(frm.doc.custom_bonus_accrual_submit==1)
                {
                    msgprint("Employee Bonus Accrual Submitted")
    
    
                }
    }
});



function create_bonus_accrual_entry(frm)
{
    frm.add_custom_button(__("Create Bonus Accrual Entry"),function()
    {

         frappe.call({

            "method":"cn_indian_payroll.cn_indian_payroll.overrides.accrual_bonus.accrual_created",
            args:{

                payroll_entry_doc_id: frm.doc.name,
                company_name :frm.doc.company

            },
            callback: function(res)
            {
                frm.set_value("custom_bonus_accrual_created",1)
                frm.save('Update');
                msgprint("Bonus Accrual is Created")
                
            }
            

            })
        
    })


}

