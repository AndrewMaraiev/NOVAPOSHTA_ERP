frappe.ui.form.on('Ukrposhta', {
    refresh: function(frm) {
        frm.add_custom_button('Ukrpohta Tracking', function() {
            let d = new frappe.ui.Dialog({
                title: 'Enter details',
                fields: [
                    {
                        label: 'Barcode',
                        fieldname: 'barcode',
                        fieldtype: 'Data',
                        reqd: 1 
                    },
                ],
                size: 'small', // small, large, extra-large 
                primary_action_label: 'Submit',
                primary_action(values) {
                    console.log(values.barcode);
                    d.hide();
                    frappe.call({
                        method: 'erpnext_shipping.erpnext_shipping.doctype.ukrposhta.ukrposhta.waybill_tracking', 
                        args: {
                            barcode: values.barcode
                        },
                        callback: function(response) {
                            if (response.message) {
                                frappe.msgprint(response.message);
                            }
                        }
                    });
                }
            });
            
            d.show();
        });
    },

    get_regions: function(frm) {
        frm.call('fetch_and_save_regions');
    },

    get_districts: function(frm) {
        frm.call('fetch_and_save_districts');
    },

    get_cities: function(frm) {
        frm.call('fetch_and_save_cities');
    },

    get_warehouses: function(frm) {
        frm.call('fetch_and_save_warehouses');
    },

    get_streets: function(frm) {
        frm.call('fetch_and_save_streets');
    }

});
