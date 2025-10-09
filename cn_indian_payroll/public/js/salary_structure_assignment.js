

frappe.ui.form.on('Salary Structure Assignment', {


    onload: function(frm) {
            if (frm.doc.custom_promotion_id && frm.is_new()) {
                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: "Employee Promotion",
                        filters: { "name": frm.doc.custom_promotion_id }
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.after_ajax(() => {
                                setTimeout(() => {
                                    frm.set_value("salary_structure", r.message.custom_current_structure);
                                    frm.set_value("from_date",r.message.promotion_date)
                                    frm.set_value("currency",r.message.custom_currency)


                                }, 100);
                            });
                        }
                    }
                });
            }
    },


    refresh(frm)
    {

        if (frm.doc.custom_promotion_id) {
            frm.add_custom_button(__('View Employee Promotion'), function() {
                frappe.set_route('Form', 'Employee Promotion', frm.doc.custom_promotion_id);
            }, __('Actions'));
        }

        frm.add_custom_button(__('View CTC BreakUp'), async function() {
            frappe.call({
                method: "cn_indian_payroll.cn_indian_payroll.overrides.salary_structure_assignment.generate_ctc_pdf",
                args: {
                    employee: frm.doc.employee,
                    salary_structure: frm.doc.salary_structure,
                    print_format: 'Salary Slip Standard',
                    posting_date: frm.doc.from_date,
                    employee_benefits: frm.doc.employee_benefits
                },
                callback: function(r) {
                    if (r.message && r.message.pdf_url) {
                        window.open(r.message.pdf_url, '_blank'); // Opens PDF
                    } else {
                        frappe.msgprint("Failed to generate PDF");
                    }
                }
            });
        }, __('Actions'));









        if (frm.doc.custom_lwf_state) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "State",
                    name: frm.doc.custom_lwf_state
                },
                callback: function(res) {
                    if (res.message && res.message.frequency) {


                        let frequency_array = res.message.frequency.map(row => row.frequency);


                        frm.set_value("custom_frequency", frequency_array[0]);

                        frm.set_query("custom_frequency", function() {
                            return {
                                filters: {
                                    name: ["in", frequency_array]
                                }
                            };
                        });
                    }
                }
            });
        }





    },


    custom_cubic_capacity_of_company(frm)
    {

            if(frm.doc.custom_cubic_capacity_of_company=="Car < 1600 CC" )
            {
                frm.set_value("custom_car_perquisite_as_per_rules",1800)
            }

            else if (frm.doc.custom_cubic_capacity_of_company=="Car > 1600 CC")
            {
                frm.set_value("custom_car_perquisite_as_per_rules",2400)
            }


    },

    custom_lwf_state: function(frm) {
        if (frm.doc.custom_lwf_state) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "State",
                    name: frm.doc.custom_lwf_state
                },
                callback: function(res) {
                    if (res.message && res.message.frequency) {


                        let frequency_array = res.message.frequency.map(row => row.frequency);


                        frm.set_value("custom_frequency", frequency_array[0]);

                        frm.set_query("custom_frequency", function() {
                            return {
                                filters: {
                                    name: ["in", frequency_array]
                                }
                            };
                        });
                    }
                }
            });
        }
    },




    custom_driver_provided_by_company(frm)
    {
        if(frm.doc.custom_driver_provided_by_company==1)
        {
            frm.set_value("custom_driver_perquisite_as_per_rules",900)
        }
        else
        {
            frm.set_value("custom_driver_perquisite_as_per_rules",undefined)
        }
    },


    custom__car_perquisite(frm)
    {
        if (frm.doc.custom__car_perquisite==1)
            {
                if(frm.doc.custom_cubic_capacity_of_company=="Car > 1600 CC")
                    {

                        frm.set_value("custom_car_perquisite_as_per_rules",2400)
                    }

            }

            else
            {
                frm.set_value("custom_car_perquisite_as_per_rules",undefined)

            }
    },


})
