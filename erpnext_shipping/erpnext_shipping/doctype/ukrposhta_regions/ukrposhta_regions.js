// Copyright (c) 2024, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Ukrposhta', {
    refresh: function(frm) {
        // додаємо обробник натискання на кнопку
        frm.add_custom_button(__('Get regions'), function() {
            // Виклик методу
            frappe.call({
                method: "erpnext_shipping.erpnext_shipping.doctype.ukrposhta.ukrposhta.fetch_and_save_regions",
                callback: function(r) {
                    if (!r.exc) {
                        // Виводимо повідомлення про успішне виконання
                        frappe.msgprint(__('Regions have been successfully fetched and saved.'));
                    }
                }
            });
        });
    }
});
