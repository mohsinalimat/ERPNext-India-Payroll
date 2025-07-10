// frappe.ui.form.on('Employee Tax Exemption Declaration', {
//     refresh: function (frm) {
//         frappe.call({
//             method: "frappe.client.get_list",
//             args: {
//                 doctype: "Employee Tax Exemption Sub Category",
//                 fields: ["name", "exemption_category", "max_amount", "custom_description", "custom_component_type"],
//                 filters: {
//                     is_active: 1
//                 },
//                 order_by: "custom_sequence asc",
//                 limit_page_length: 9999
//             },
//             callback: function (r) {
//                 if (r.message && r.message.length > 0) {

//                     let stored_data = {};
//                     if (frm.doc.custom_declaration_form_data) {
//                         try {
//                             stored_data = JSON.parse(frm.doc.custom_declaration_form_data);
//                         } catch (e) {}
//                     }

//                     let rows_html = '';

//                     r.message.forEach(row => {
//                         const stored_row = Array.isArray(stored_data)
//                             ? stored_data.find(item => item.id === row.name || item.sub_category === row.name)
//                             : null;

//                         const stored_value = stored_row ? stored_row.value || stored_row.amount || '' : '';

//                         // Determine readonly condition based on tax regime
//                         let is_readonly = false;
//                         if (frm.doc.custom_tax_regime === "New Regime") {
//                             is_readonly = true; // All fields disabled
//                         } else if (frm.doc.custom_tax_regime === "Old Regime") {
//                             // Still disable only specific components
//                             is_readonly = ["NPS", "Provident Fund", "Professional Tax"].includes(row.custom_component_type);
//                         }

//                         const readonly_attr = is_readonly ? 'readonly' : '';

//                         rows_html += `
//                             <tr data-id="${row.name}" data-max="${row.max_amount}" data-category="${row.exemption_category}">
//                                 <td>${row.name}</td>
//                                 <td>${row.max_amount || ''}</td>
//                                 <td>${row.exemption_category || ''}</td>
//                                 <td>${row.custom_description || ''}</td>
//                                 <td><input type="number" class="input-field" style="width: 100%" value="${stored_value}" ${readonly_attr} /></td>
//                             </tr>
//                         `;
//                     });

//                     // Inline message if regime is New Regime
//                     let info_message = '';
//                     if (frm.doc.custom_tax_regime === "New Regime") {
//                         info_message = `
//                             <div style="
//                                 background-color: #fff3cd;
//                                 color: #856404;
//                                 padding: 12px;
//                                 margin-bottom: 15px;
//                                 border: 1px solid #ffeeba;
//                                 border-radius: 4px;
//                             ">
//                                 <strong>Note:</strong> All exemption input fields are disabled under <strong>New Regime</strong>.
//                             </div>
//                         `;
//                     }

//                     const html = `
//                         ${info_message}
//                         <style>
//                             .styled-declaration-table {
//                                 width: 100%;
//                                 border-collapse: collapse;
//                                 margin-top: 15px;
//                             }
//                             .styled-declaration-table th, .styled-declaration-table td {
//                                 padding: 12px;
//                                 border: 1px solid #ccc;
//                                 text-align: left;
//                             }
//                             .styled-declaration-table th {
//                                 background-color: #f7f7f7;
//                             }
//                         </style>

//                         <table class="styled-declaration-table" id="declaration-table">
//                             <thead>
//                                 <tr>
//                                     <th>Invested Description</th>
//                                     <th>Maximum Limit</th>
//                                     <th>Section</th>
//                                     <th>Narration</th>
//                                     <th>Amount</th>
//                                 </tr>
//                             </thead>
//                             <tbody>
//                                 ${rows_html}
//                             </tbody>
//                         </table>

//                         <table class="styled-declaration-table" id="summary-table">
//                             <thead>
//                                 <tr>
//                                     <th>Annual HRA Exemption</th>
//                                     <td>${frm.doc.annual_hra_exemption || 0}</td>
//                                 </tr>
//                                 <tr>
//                                     <th>Total Exemption Eligible Amount</th>
//                                     <td>${frm.doc.total_exemption_amount || 0}</td>
//                                 </tr>
//                             </thead>
//                         </table>
//                     `;

//                     frm.fields_dict.custom_declaration_form.$wrapper.html(html);
//                     frm.fields_dict.custom_declaration_form.$wrapper.css("width", "100%");

//                     const inputs = document.querySelectorAll("#declaration-table tbody tr input");

//                     inputs.forEach(input => {
//                         if (!input.hasAttribute("readonly")) {
//                             input.addEventListener("change", () => {
//                                 const formData = [];
//                                 frm.clear_table("declarations");

//                                 document.querySelectorAll("#declaration-table tbody tr").forEach(row => {
//                                     const id = row.getAttribute("data-id");
//                                     const max = parseFloat(row.getAttribute("data-max")) || 0;
//                                     const exemption_category = row.getAttribute("data-category");
//                                     let value = parseFloat(row.querySelector("input").value || 0);

//                                     if (max > 0 && value > max) {
//                                         frappe.msgprint(`Amount for "${id}" exceeds the max (${max}). Resetting to 0.`);
//                                         value = 0;
//                                         row.querySelector("input").value = 0;
//                                     }

//                                     if (value > 0) {
//                                         formData.push({
//                                             id: id,
//                                             sub_category: id,
//                                             exemption_category: exemption_category,
//                                             max_amount: max,
//                                             amount: value,
//                                             value: value
//                                         });

//                                         const d = frm.add_child("declarations");
//                                         d.exemption_sub_category = id;
//                                         d.exemption_category = exemption_category;
//                                         d.max_amount = max;
//                                         d.amount = value;
//                                     }
//                                 });

//                                 frm.set_value("custom_declaration_form_data", JSON.stringify(formData));
//                                 frm.refresh_field("declarations");
//                             });
//                         }
//                     });
//                 }
//             }
//         });

//         frm.trigger("change_tax_regime");

//     }
// });



// function change_tax_regime(frm)
// {

//     console.log("kkkkkkkkkkkk")
//     if (!frm.is_new())
//         {
//             frm.add_custom_button("Choose Regime",function()
//             {

//               let d = new frappe.ui.Dialog({
//                 title: 'Enter details',
//                 fields: [

//                     {
//                         label: 'Select Regime',
//                         fieldname: 'select_regime',
//                         fieldtype: 'Select',
//                         options:['Old Regime','New Regime'],
//                         reqd:1,
//                         default:frm.doc.custom_tax_regime,
//                         description: `Your current tax regime is ${frm.doc.custom_tax_regime}`

//                     },
//                 ],
//                 size: 'small',
//                 primary_action_label: 'Submit',
//                 primary_action(values) {

//                     frappe.call({
//                       "method":"cn_indian_payroll.cn_indian_payroll.overrides.declaration.choose_regime",
//                       args:{

//                           doc_id: frm.doc.name,
//                           employee:frm.doc.employee,
//                           company:frm.doc.company,
//                           payroll_period:frm.doc.payroll_period,
//                           regime:values.select_regime


//                       },
//                       callback :function(res)
//                       {
//                           frm.reload_doc();
//                       }

//                   })

//                     d.hide();
//                 }
//             });
//             d.show();
//             })
//             frm.change_custom_button_type('Choose Regime', null, 'primary');
//         }
// }


frappe.ui.form.on('Employee Tax Exemption Declaration', {
    refresh(frm) {
        frm.trigger("change_tax_regime");
        frm.trigger("display_declaration_form");
        frm.trigger("tds_projection_html");
    },

    change_tax_regime(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button("Choose Regime", function () {
                let d = new frappe.ui.Dialog({
                    title: 'Choose Tax Regime',
                    fields: [
                        {
                            label: 'Select Regime',
                            fieldname: 'select_regime',
                            fieldtype: 'Select',
                            options: ['Old Regime', 'New Regime'],
                            reqd: 1,
                            default: frm.doc.custom_tax_regime,
                            description: `Your current tax regime is <strong>${frm.doc.custom_tax_regime}</strong>`
                        }
                    ],
                    size: 'small',
                    primary_action_label: 'Submit',
                    primary_action(values) {
                        frappe.call({
                            method: "cn_indian_payroll.cn_indian_payroll.overrides.declaration.choose_regime",
                            args: {
                                doc_id: frm.doc.name,
                                employee: frm.doc.employee,
                                company: frm.doc.company,
                                payroll_period: frm.doc.payroll_period,
                                regime: values.select_regime
                            },
                            callback: function (res) {
                                frm.reload_doc();
                            }
                        });
                        d.hide();
                    }
                });
                d.show();
            });

            frm.change_custom_button_type('Choose Regime', null, 'primary');
        }
    },

    display_declaration_form(frm) {

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Employee Tax Exemption Sub Category",
                fields: ["name", "exemption_category", "max_amount", "custom_description", "custom_component_type"],
                filters: {
                    is_active: 1
                },
                order_by: "custom_sequence asc",
                limit_page_length: 9999
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {

                    let stored_data = {};
                    if (frm.doc.custom_declaration_form_data) {
                        try {
                            stored_data = JSON.parse(frm.doc.custom_declaration_form_data);
                        } catch (e) {}
                    }

                    let rows_html = '';

                    r.message.forEach(row => {
                        const stored_row = Array.isArray(stored_data)
                            ? stored_data.find(item => item.id === row.name || item.sub_category === row.name)
                            : null;

                        const stored_value = stored_row ? stored_row.value || stored_row.amount || '' : '';

                        // Determine readonly condition based on tax regime
                        let is_readonly = false;
                        if (frm.doc.custom_tax_regime === "New Regime") {
                            is_readonly = true; // All fields disabled
                        } else if (frm.doc.custom_tax_regime === "Old Regime") {
                            // Still disable only specific components
                            is_readonly = ["NPS", "Provident Fund", "Professional Tax"].includes(row.custom_component_type);
                        }

                        const readonly_attr = is_readonly ? 'readonly' : '';

                        rows_html += `
                            <tr data-id="${row.name}" data-max="${row.max_amount}" data-category="${row.exemption_category}">
                                <td>${row.name}</td>
                                <td>${row.max_amount || ''}</td>
                                <td>${row.exemption_category || ''}</td>
                                <td>${row.custom_description || ''}</td>
                                <td><input type="number" class="input-field" style="width: 100%" value="${stored_value}" ${readonly_attr} /></td>
                            </tr>
                        `;
                    });

                    // Inline message if regime is New Regime
                    let info_message = '';
                    if (frm.doc.custom_tax_regime === "New Regime") {
                        info_message = `
                            <div style="
                                background-color: #fff3cd;
                                color: #856404;
                                padding: 12px;
                                margin-bottom: 15px;
                                border: 1px solid #ffeeba;
                                border-radius: 4px;
                            ">
                                <strong>Note:</strong> All exemption input fields are disabled under <strong>New Regime</strong>.
                            </div>
                        `;
                    }

                    const html = `
                        ${info_message}
                        <style>
                            .styled-declaration-table {
                                width: 100%;
                                border-collapse: collapse;
                                margin-top: 15px;
                            }
                            .styled-declaration-table th, .styled-declaration-table td {
                                padding: 12px;
                                border: 1px solid #ccc;
                                text-align: left;
                            }
                            .styled-declaration-table th {
                                background-color: #f7f7f7;
                            }
                        </style>

                        <table class="styled-declaration-table" id="declaration-table">
                            <thead>
                                <tr>
                                    <th>Invested Description</th>
                                    <th>Maximum Limit</th>
                                    <th>Section</th>
                                    <th>Narration</th>
                                    <th>Amount</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${rows_html}
                            </tbody>
                        </table>

                        <table class="styled-declaration-table" id="summary-table">
                            <thead>
                                <tr>
                                    <th>Annual HRA Exemption</th>
                                    <td>${frm.doc.annual_hra_exemption || 0}</td>
                                </tr>
                                <tr>
                                    <th>Total Exemption Eligible Amount</th>
                                    <td>${frm.doc.total_exemption_amount || 0}</td>
                                </tr>
                            </thead>
                        </table>
                    `;

                    frm.fields_dict.custom_declaration_form.$wrapper.html(html);
                    frm.fields_dict.custom_declaration_form.$wrapper.css("width", "100%");

                    const inputs = document.querySelectorAll("#declaration-table tbody tr input");

                    inputs.forEach(input => {
                        if (!input.hasAttribute("readonly")) {
                            input.addEventListener("change", () => {
                                const formData = [];
                                frm.clear_table("declarations");

                                document.querySelectorAll("#declaration-table tbody tr").forEach(row => {
                                    const id = row.getAttribute("data-id");
                                    const max = parseFloat(row.getAttribute("data-max")) || 0;
                                    const exemption_category = row.getAttribute("data-category");
                                    let value = parseFloat(row.querySelector("input").value || 0);

                                    if (max > 0 && value > max) {
                                        frappe.msgprint(`Amount for "${id}" exceeds the max (${max}). Resetting to 0.`);
                                        value = 0;
                                        row.querySelector("input").value = 0;
                                    }

                                    if (value > 0) {
                                        formData.push({
                                            id: id,
                                            sub_category: id,
                                            exemption_category: exemption_category,
                                            max_amount: max,
                                            amount: value,
                                            value: value
                                        });

                                        const d = frm.add_child("declarations");
                                        d.exemption_sub_category = id;
                                        d.exemption_category = exemption_category;
                                        d.max_amount = max;
                                        d.amount = value;
                                    }
                                });

                                frm.set_value("custom_declaration_form_data", JSON.stringify(formData));
                                frm.refresh_field("declarations");
                            });
                        }
                    });
                }
            }
        });

    },

    tds_projection_html(frm) {
        if (frm.doc.docstatus === 1) {
            frappe.call({
                method: "cn_indian_payroll.cn_indian_payroll.overrides.tds_projection_calculation.calculate_tds_projection",
                args: {
                    doc: frm.doc
                },
                callback: function (res) {
                    console.log("TDS Projection Calculated");
                }
            });
        }
    }


});
