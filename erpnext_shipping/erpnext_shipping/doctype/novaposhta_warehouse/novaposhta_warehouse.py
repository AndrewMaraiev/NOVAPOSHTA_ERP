# Copyright (c) 2023, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class NovaPoshtaWarehouse(Document):
	pass


@frappe.whitelist()
def warehouse_query(doctype, txt, searchfield, start, page_len, filters):
    ...