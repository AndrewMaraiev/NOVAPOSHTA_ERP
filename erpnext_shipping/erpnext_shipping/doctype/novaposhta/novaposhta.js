// Copyright (c) 2020, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('NovaPoshta', {
	// refresh: function(frm) {

	// }
	get_areas : function(frm){
		frm.call('get_areas')
		},

	get_warehouses : function(frm){
		frm.call('get_warehouses')
		},

	get_cities : function(frm){
		frm.call('get_cities')
		},

	get_waybill : function(frm){
		frm.call('get_waybill')
	}
});
