frappe.ui.form.on('Employee Tax Exemption Declaration', {
    refresh: function (frm) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Employee Tax Exemption Sub Category",
                fields: ["name", "exemption_category", "max_amount", "custom_description","custom_component_type"],
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

                        // Check if the row should be read-only
                        const is_readonly = ["NPS", "Provident Fund", "Professional Tax"].includes(row.custom_component_type);
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

                    const html = `
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
                        input.addEventListener("change", () => {
                            const formData = [];
                            frm.clear_table("declarations");

                            document.querySelectorAll("#declaration-table tbody tr").forEach(row => {
                                const id = row.getAttribute("data-id");
                                const max = parseFloat(row.getAttribute("data-max")) || 0;
                                const exemption_category = row.getAttribute("data-category");
                                let value = parseFloat(row.querySelector("input").value || 0);

                                // Validate only if max > 0
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
                    });
                }
            }
        });
    },

});
