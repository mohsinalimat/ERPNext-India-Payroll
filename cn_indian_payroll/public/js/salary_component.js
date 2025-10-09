frappe.ui.form.on('Salary Component', {



	refresh(frm) {


		frm.set_query('custom_lta_taxable_component', function() {
			return {
				filters: {
					component_type:"LTA Taxable"
				}
			};
		});

		frm.set_query('custom_lta_non_taxable_component', function() {
			return {
				filters: {
					component_type:"LTA Non Taxable"
				}
			};
		});

	},






	is_tax_applicable:function(frm)
	{
		if (frm.doc.is_tax_applicable) {
			frm.set_value('custom_tax_exemption_applicable_based_on_regime', 1);
		}
		else
		{
			frm.set_value('custom_tax_exemption_applicable_based_on_regime', 0);
		}

	},


});
