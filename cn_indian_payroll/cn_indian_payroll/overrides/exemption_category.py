import frappe
from frappe import _

def validate(self, method):
    if not self.custom_select_section:
        return

    validate_doc = frappe.get_list(
        "Employee Tax Exemption Category",
        filters={
            "custom_select_section": self.custom_select_section,
            "is_active": 1,
            "name": ["!=", self.name]
        },
        fields=["name"]
    )

    if validate_doc:
        frappe.throw(
            _("An active Exemption Category with type '{0}' already exists.").format(self.custom_select_section)
        )
