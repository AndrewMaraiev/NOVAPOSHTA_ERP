// Copyright (c) 2024, Frappe and contributors
// For license information, please see license.txt

// frappe.ui.form.on('Ukrposhta Tracking', {
//     refresh: function(frm) {
        
//     }
// });

frappe.ui.form.on('Ukrposhta tracking', {
    refresh: function(frm) {
        frm.add_custom_button(__('Tracking Status'), function() {
            frappe.call({
                method: 'ukrposhta_tracking.waybill_tracking',
                args: {
                    barcode: frm.doc.waybill_tracking
                },
                callback: function(response) {
                    if (response.message) {
                        frappe.msgprint(__('Tracking Status: ' + JSON.stringify(response.message)));
                    }
                }
            });
        });
    }
});

