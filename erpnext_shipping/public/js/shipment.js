frappe.templates['shipment'] = `
{% if (data.preferred_services.length || data.other_services.length) { %}
	<div style="overflow-x:scroll;">
		<h5>{{ __("Preferred Services") }}</h5>
		{% if (data.preferred_services.length) { %}
			<table class="table table-bordered table-hover">
				<thead class="grid-heading-row">
					<tr>
						{% for (var i = 0; i < header_columns.length; i++) { %}
							<th style="padding-left: 12px;">{{ header_columns[i] }}</th>
						{% } %}
					</tr>
				</thead>
				<tbody>
					{% for (var i = 0; i < data.preferred_services.length; i++) { %}
						<tr id="data-preferred-{{i}}">
							<td class="service-info" style="width:20%;">{{ data.preferred_services[i] }}</td>
							<td class="service-info" style="width:20%;">{{ data.preferred_services[i].carrier }}</td>
							<td class="service-info" style="width:40%;">{{ data.preferred_services[i].service_name }}</td>
							<td class="service-info" style="width:20%;">{{ format_currency(data.preferred_services[i].total_price, "UAH", 2) }}</td>
							<td style="width:10%;vertical-align: middle;">
								<button
									data-type="preferred_services"
									id="data-preferred-{{i}}" type="button" class="btn">
									Select
								</button>
							</td>
						</tr>
					{% } %}
				</tbody>
			</table>
		{% } else { %}
			<div style="text-align: center; padding: 10px;">
				<span class="text-muted">
					{{ __("No Preferred Services Available") }}
				</span>
			</div>
		{% } %}
		<h5>{{ __("Other Services") }}</h5>
		{% if (data.other_services.length) { %}
			<table class="table table-bordered table-hover">
				<thead class="grid-heading-row">
					<tr>
						{% for (var i = 0; i < header_columns.length; i++) { %}
							<th style="padding-left: 12px;">{{ header_columns[i] }}</th>
						{% } %}
					</tr>
				</thead>
				<tbody>
					{% for (var i = 0; i < data.other_services.length; i++) { %}
						<tr id="data-other-{{i}}">
							<td class="service-info" style="width:20%;">{{ data.other_services[i].service_provider }}</td>
							<td class="service-info" style="width:20%;">{{ data.other_services[i].carrier_name }}</td>
							<td class="service-info" style="width:40%;">{{ data.other_services[i].service_name }}</td>
							<td class="service-info" style="width:20%;">{{ format_currency(data.other_services[i].Price, "UAH", 2) }}</td>
							<td style="width:10%;vertical-align: middle;">
								<button
									data-type="other_services"
									id="data-other-{{i}}" type="button" class="btn">
									Select
								</button>
							</td>
						</tr>
					{% } %}
				</tbody>
			</table>
		{% } else { %}
			<div style="text-align: center; padding: 10px;">
				<span class="text-muted">
					{{ __("No Services Available") }}
				</span>
			</div>
		{% } %}
	</div>
{% } else { %}
	<div style="text-align: center; padding: 10px;">
		<span class="text-muted">
			{{ __("No Services Available") }}
		</span>
	</div>
{% } %}

<style type="text/css" media="screen">
.modal-dialog {
	width: 750px;
}
.service-info {
	vertical-align: middle !important;
	padding-left: 12px !important;
}
.btn:hover {
	background-color: #dedede;
}
.ship {
	font-size: 16px;
}
</style>


`;
frappe.ui.form.on('Shipment', 'pickup_city', function(frm){
	
	frm.fields_dict.pickup_warehouse.df['filters'] = {city: frm.fields_dict.pickup_city.value}

});
frappe.ui.form.on('Shipment', 'delivery_to_city', function(frm){
	
	frm.fields_dict.delivery_to_warehouse.df['filters'] = {city: ["like", "%" + frm.fields_dict.delivery_to_city.value+"%"]}

});
frappe.ui.form.on('Shipment', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && !frm.doc.shipment_id) {
			frm.add_custom_button(__('Fetch Shipping Rates'), function() {
				return frm.events.fetch_shipping_rates(frm);
			});
		}
		if (frm.doc.shipment_id) {
			frm.add_custom_button(__('Print Shipping Label'), function() {
				return frm.events.print_shipping_label(frm);
			}, __('Tools'));
			if (frm.doc.tracking_status != 'Delivered') {
				frm.add_custom_button(__('Update Tracking'), function() {
					return frm.events.update_tracking(frm, frm.doc.service_provider, frm.doc.shipment_id);
				}, __('Tools'));

				frm.add_custom_button(__('Track Status'), function() {
					if (frm.doc.tracking_url) {
						const urls = frm.doc.tracking_url.split(', ');
						urls.forEach(url => window.open(url));
					} else {
						frappe.msgprint(__('No Tracking URL found'));
					}
				}, __('Tools'));
			}
		}
	},

	fetch_shipping_rates: function(frm) {
		console.log(frm)
		if (!frm.doc.shipment_id) {
			frappe.call({
				method: "erpnext_shipping.erpnext_shipping.shipping.fetch_shipping_rates",
				freeze: true,
				freeze_message: __("Fetching Shipping Rates"),
				args: {
					pickup_from_type: frm.doc.pickup_from_type,
					delivery_to_type: frm.doc.delivery_to_type,
					pickup_city_ref: frm.doc.pickup_city,
					delivery_city_ref: frm.doc.delivery_to_city,
					shipment_parcel: frm.doc.shipment_parcel,
					value_of_goods: frm.doc.value_of_goods
				},
				
				callback: function(r) {
					if (r.message && r.message.length) {
						console.log(r.message);
						select_from_available_services(frm, r.message);
					} else {
						frappe.msgprint({ message: __("No Shipment Services available"), title: __("Note") });
					}
				}
			});
		} else {
			frappe.throw(__("Shipment already created"));
		}
	},

// frappe.ui.form.on('Shipment', {
// 	refresh: function(frm) {
// 		if (frm.doc.docstatus === 1 && !frm.doc.shipment_id) {
// 			frm.add_custom_button(__('Fetch Shipping Rates'), function() {
// 				let d = new frappe.ui.Dialog({
// 					title: 'Enter details',
// 					fields: [
// 						{
// 							label: 'City',
// 							fieldname: 'city_name',
// 							fieldtype: 'Link',
// 							options: "NovaPoshta cities"
// 						},
// 						{
// 							label: 'Warehouse',
// 							fieldname: 'warehouse',
// 							fieldtype: 'Link',
// 							options: "NovaPoshta Warehouse",
// 							// filters: 'city==city_name',
// 							query: 'erpnext_shiping.erpnext_shiping.doctype.novaposhta_warehouse.novaposhta_warehouse.warehouse_query',
// 							filters: {
// 								city: 'null'
// 							}
// 						},
// 						{
// 							label: 'Age',
// 							fieldname: 'age',
// 							fieldtype: 'Int'
// 						}
// 					],
// 					size: 'small', // small, large, extra-large 
// 					primary_action_label: 'Submit',
// 					primary_action(values) {
// 						console.log(values);
// 						d.hide();
// 					},
// 					onkeydown(value){ console.log(value)},
// 					warehouse_query(values){
// 						console.log(values)
// 					}
// 				});

// 				console.log(d)
// 				// d.on('Dialog', {
// 				// 	city_name_query: function(value){
// 				// 		console.log(value)
// 				// 	}
// 				// }
				
// 				// )

				
				
// 				d.show();
// 				// return frm.events.fetch_shipping_rates(frm);
// 			});
// 		}
// 		if (frm.doc.shipment_id) {
// 			frm.add_custom_button(__('Print Shipping Label'), function() {
// 				return frm.events.print_shipping_label(frm);
// 			}, __('Tools'));
// 			if (frm.doc.tracking_status != 'Delivered') {
// 				frm.add_custom_button(__('Update Tracking'), function() {
// 					return frm.events.update_tracking(frm, frm.doc.service_provider, frm.doc.shipment_id);
// 				}, __('Tools'));

// 				frm.add_custom_button(__('Track Status'), function() {
// 					if (frm.doc.tracking_url) {
// 						const urls = frm.doc.tracking_url.split(', ');
// 						urls.forEach(url => window.open(url));
// 					} else {
// 						frappe.msgprint(__('No Tracking URL found'));
// 					}
// 				}, __('Tools'));
// 			}
// 		}
// 	},

// 	fetch_shipping_rates: function(frm) {
// 		if (!frm.doc.shipment_id) {
// 			frappe.call({
// 				method: "erpnext_shipping.erpnext_shipping.shipping.fetch_shipping_rates",
// 				freeze: true,
// 				freeze_message: __("Fetching Shipping Rates"),
// 				args: {
// 					pickup_from_type: frm.doc.pickup_from_type,
// 					delivery_to_type: frm.doc.delivery_to_type,
// 					pickup_address_name: frm.doc.pickup_address_name,
// 					delivery_address_name: frm.doc.delivery_address_name,
// 					shipment_parcel: frm.doc.shipment_parcel,
// 					description_of_content: frm.doc.description_of_content,
// 					pickup_date: frm.doc.pickup_date,
// 					pickup_contact_name: frm.doc.pickup_from_type === 'Company' ? frm.doc.pickup_contact_person : frm.doc.pickup_contact_name,
// 					delivery_contact_name: frm.doc.delivery_contact_name,
// 					value_of_goods: frm.doc.value_of_goods
// 				},
// 				callback: function(r) {
// 					if (r.message && r.message.length) {
// 						console.log(r.message);
// 						select_from_available_services(frm, r.message);
// 					} else {
// 						frappe.msgprint({ message: __("No Shipment Services available"), title: __("Note") });
// 					}
// 				}
// 			});
// 		} else {
// 			frappe.throw(__("Shipment already created"));
// 		}
// 	},

	print_shipping_label: function(frm) {
		var shipment_id = frm.doc.shipment_id;
		if (shipment_id) {
			// window.open("/api/method/erpnext_shipping.erpnext_shipping.doctype.novaposhta.novaposhta.get_label");

			frappe.call({
				method: "erpnext_shipping.erpnext_shipping.doctype.novaposhta.novaposhta.get_label",
				args: {
					waybill_number: shipment_id,
					ref: frm.d
				},
				callback: function(response) {
					if (response) {
						var label_url = response.message;
						console.log(response)
						// var printWindow = window.open(label_url, "_blank");
						var mywindow = window.open('', 'PRINT', 'height=100,width=100');
						mywindow.document.write(label_url)
						mywindow.onload = function() {
							mywindow.print();
						};
					} else {
						frappe.msgprint("No label URL found");
					}
				}
			});
		} else {
			frappe.msgprint("Shipment ID not found");
		}
	},

	update_tracking: function(frm, service_provider, waybill) {
		// Check if the waybill and service provider are provided
		if (!waybill || !service_provider) {
			frappe.msgprint("Waybill or Service Provider not provided.");
			return;
		}
	
		// Implement the code to fetch tracking information using the NovaPoshtaUtils API
		frappe.call({
			method: "erpnext_shipping.erpnext_shipping.doctype.novaposhta.novaposhta.get_tracking_data",
			args: {
				api_key: 'ed0b9e715fefe9ba6b2a3ec7cce89a1a', // Replace with your Nova Poshta API key
				waybill_number: waybill,
				delivery_contact: frm.doc.delivery_contact_name
			},
			callback: function(response) {
				if (response && response.message && response.message.data && response.message.data.length > 0) {
					const trackingData = response.message.data[0];
					// Update the tracking information in the Shipment document
					frm.doc.tracking_status = trackingData.StatusCode;
					frm.doc.tracking_status_description = getTrackingStatusDescription(trackingData.StatusCode.toString());
	
					// Optionally, you can also update other relevant information as needed
					frm.doc.actual_delivery_date = trackingData.ActualDeliveryDate;
					frm.doc.city_recipient = trackingData.CityRecipient;
					frm.doc.city_sender = trackingData.CitySender;
	
					// Save the updated document
					frm.save();
					// frappe.msgprint("Tracking information updated successfully.");
					frappe.msgprint(getTrackingStatusDescription(trackingData.StatusCode));
				} else {
					frappe.msgprint("Failed to update tracking information.");
				}
			}
		});
	}
	});

function getTrackingStatusDescription(statusCode) {
    switch (statusCode) {
        case '1':
            return 'Відправник самостійно створив цю накладну, але ще не надав до відправки';
        case '2':
            return 'Видалено';
        case '3':
            return 'Номер не знайдено';
        case '4':
            return 'Відправлення у місті ХХXХ. (Статус для міжобласних відправлень)';
        case '41':
            return 'Відправлення у місті ХХXХ. (Статус для послуг локал стандарт і локал експрес - доставка в межах віста)';

            return 'Відправлення у місті ХХXХ. (Статус для межобластных отправлений)';
        case '41':
            return 'Відправлення у місті ХХXХ. (Статус для услуг локал стандарт и локал экспресс - доставка в пределах города)';

        case '5':
            return 'Відправлення прямує до міста YYYY';
        case '6':
            return 'Відправлення у місті YYYY, орієнтовна доставка до ВІДДІЛЕННЯ-XXX dd-mm. Очікуйте додаткове повідомлення про прибуття';
        case '7':
            return 'Прибув на відділення';
        case '8':
            return 'Прибув на відділення (завантажено в Поштомат)';
        case '9':
            return 'Відправлення отримано';
        case '10':
            return 'Відправлення отримано %DateReceived%. Протягом доби ви одержите SMS-повідомлення про надходження грошового переказу та зможете отримати його в касі відділення «Нова пошта»';
        case '11':
            return 'Відправлення отримано %DateReceived%. Грошовий переказ видано одержувачу.';
        case '12':
            return 'Нова Пошта комплектує ваше відправлення';
        case '101':
            return 'На шляху до одержувача';
        case '102':
            return 'Відмова від отримання (Відправником створено замовлення на повернення)';
        case '103':
            return 'Відмова одержувача (отримувач відмовився від відправлення)';
        case '104':
            return 'Змінено адресу';
        case '105':
            return 'Припинено зберігання';
        case '106':
            return 'Одержано і створено ЄН зворотньої доставки';
        case '111':
            return 'Невдала спроба доставки через відсутність Одержувача на адресі або зв\'язку з ним';
        case '112':
            return 'Дата доставки перенесена Одержувачем';
        default:
            return 'Невідомий статус';
    }
}

function select_from_available_services(frm, available_services) {
	var headers = [ __("Service Provider"), __("Parcel Service"), __("Parcel Service Type"), __("Price"), "" ];

	const arranged_services = available_services.reduce((prev, curr) => {
		if (curr.is_preferred) {
			prev.preferred_services.push(curr);
		} else {
			prev.other_services.push(curr);
		}
		return prev;
	}, { preferred_services: [], other_services: [] });

	frm.render_available_services = function(dialog, headers, arranged_services) {
		console.log(arranged_services);
		dialog.fields_dict.available_services.$wrapper.html(
			frappe.render_template('shipment', { 'header_columns': headers, 'data': arranged_services })
		);
	};

	const dialog = new frappe.ui.Dialog({
		title: __("Select Service to Create Shipment"),
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: "available_services",
				label: __('Available Services')
			}
		]
	});

	let delivery_notes = [];
	(frm.doc.shipment_delivery_note || []).forEach((d) => {
		delivery_notes.push(d.delivery_note);
	});

	frm.render_available_services(dialog, headers, arranged_services);

	dialog.$body.on('click', '.btn', function() {
		let service_type = $(this).attr("data-type");
		let service_index = cint($(this).attr("id").split("-")[2]);
		let service_data = arranged_services[service_type][service_index];
		frm.select_row(service_data);
	});

	frm.select_row = function(service_data) {
		// Check if the 'service_data' object has the 'service_provider' property defined
		if (service_data.service_provider) {
			console.log(frm)
			frappe.call({
				method: "erpnext_shipping.erpnext_shipping.shipping.create_shipment",
				freeze: true,
				freeze_message: __("Creating Shipment"),
				args: {
					shipment: frm.doc.name,
					pickup_city_ref: frm.doc.pickup_city,
					delivery_city_ref: frm.doc.delivery_to_city,
					pickup_warehouse_name: frm.doc.pickup_warehouse,
					delivery_warehouse_name: frm.doc.delivery_to_warehouse,
					shipment_parcel: frm.doc.shipment_parcel,
					recipient_full_name: frm.doc.recipient_full_name,
					sender_phone: frm.doc.sender_phone,
					recipient_phone: frm.doc.recipient_phone,
					description_of_content: frm.doc.description_of_content,
					pickup_date: frm.doc.pickup_date,
					value_of_goods: frm.doc.value_of_goods
			},
			callback: function(r) {
				console.log(r);
				if (!r.exc) {
					frm.reload_doc();
					frappe.msgprint({
						message: __("Shipment {1} has been created with {0}.", [r.message.service_provider, r.message.shipment_id.bold()]),
						title: __("Shipment Created"),
						indicator: "green"
					});
					frm.events.update_tracking(frm, r.message.service_provider, r.message.shipment_id);
				}
			}
		});
		dialog.hide();
    } else {
        // Handle the case when 'service_provider' property is not defined
        frappe.msgprint(__("Service provider information is missing."));
    }
};
	dialog.show();
}
