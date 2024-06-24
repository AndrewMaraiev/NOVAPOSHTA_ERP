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
                            <td class="service-info" style="width:20%;">{{ data.preferred_services[i].service_provider }}</td>
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
frappe.ui.form.on('Shipment', {
    onload: function (frm) {
        console.log(frm.doc.docstatus)
        console.log(frm.doc.shipment_id)
	},
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

    create_shipment_from_delivery_note: function(frm) {
        frappe.call({
            method: "erpnext_shipping.erpnext_shipping.shipping.create_shipment_from_delivery_note",
            args: {
                delivery_note: frm.doc.delivery_note 
            },
            callback: function(r) {
                if (r.message) {
                
                }
            }
        });
    },

    fetch_shipping_rates: function(frm) {
        console.log(frm);
        if (!frm.doc.shipment_id) {
            frappe.call({
                method: "erpnext_shipping.erpnext_shipping.shipping.fetch_shipping_rates",
                freeze: true,
                freeze_message: __("Fetching Shipping Rates"),
                args: {
                    service_provider: frm.doc.service_provider,  
                    pickup_from_type: frm.doc.pickup_from_type,
                    delivery_to_type: frm.doc.delivery_to_type,
                    pickup_city_ref: frm.doc.pickup_city,
                    delivery_city_ref: frm.doc.delivery_to_city,
                    shipment_parcel: JSON.stringify(frm.doc.shipment_parcel),
                    value_of_goods: frm.doc.value_of_goods,
                    sender_address: frm.doc.sender_address || 'default_sender_address', 
                    recipient_address: frm.doc.recipient_address || 'default_recipient_address', 
                    shipment_details: JSON.stringify({
                        weight: frm.doc.weight,
                        length: frm.doc.length,
                        width: frm.doc.width,
                        height: frm.doc.height,
                    }),
                    sd: frm.doc
                },
                callback: function(r) {
                    if (r.message && r.message.length) {
                        console.log(r.message);
                        select_from_available_services(frm, r.message);
                    } else {
                        frappe.msgprint({
                            message: __("No shipping rates available for the selected route and parcel type."),
                            title: __("No Rates Found"),
                            indicator: "orange"
                        });
                    }
                }
            });
        } else {
            frappe.msgprint(__("Shipment ID already assigned. Cannot fetch shipping rates."));
        }
    },

    print_shipping_label: function(frm) {
        var shipment_id = frm.doc.shipment_id;
        if (shipment_id) {
            if (frm.doc.service_provider == 'NovaPoshta') {
                frappe.call({
                    method: "erpnext_shipping.erpnext_shipping.doctype.novaposhta.novaposhta.get_label",
                    args: {
                        waybill_number: shipment_id,
                        ref: frm.doc.name // pass other necessary data
                    },
                    callback: function(response) {
                        if (response && response.message) {
                            var label_url = response.message;
                            var mywindow = window.open('', 'PRINT', 'height=100,width=100');
                            mywindow.document.write(label_url);
                            mywindow.onload = function() {
                                mywindow.print();
                            };
                        } else {
                            frappe.msgprint("No label URL found");
                        }
                    }
                });
            } else if (frm.doc.service_provider == 'Ukrposhta') {
                frappe.call({
                    method: "erpnext_shipping.erpnext_shipping.doctype.ukrposhta.ukrposhta.print_label",
                    args: {
                        barcode: shipment_id // Pass the correct parameter
                    },
                    callback: function(response) {
                        if (response && response.message) {
                            var pdf_base64 = response.message;
                            var pdfData = 'data:application/pdf;base64,' + pdf_base64;
                            var mywindow = window.open('', 'PRINT', 'height=100,width=100');
                            mywindow.document.write('<iframe width="100%" height="100%" src="' + pdfData + '"></iframe>');
                            mywindow.onload = function() {
                                mywindow.print();
                            };
                        } else {
                            frappe.msgprint("No label URL found");
                        }
                    }
                });
            } else {
                frappe.msgprint("Unsupported service provider");
            }
        } else {
            frappe.msgprint("Shipment ID not found");
        }
    }
    ,
    
    

    update_tracking: function(frm, service_provider, waybill) {
        if (!waybill || !service_provider) {
            frappe.msgprint("Waybill or Service Provider not provided.");
            return;
        }

        frappe.call({
            method: "erpnext_shipping.erpnext_shipping.doctype.novaposhta.novaposhta.get_tracking_data",
            args: {
                waybill_number: waybill,
                delivery_contact: frm.doc.delivery_contact_name
            },
            callback: function(response) {
                if (response && response.message && response.message.data && response.message.data.length > 0) {
                    const trackingData = response.message.data[0];
                    frm.doc.tracking_status = trackingData.StatusCode;
                    frm.doc.tracking_status_description = getTrackingStatusDescription(trackingData.StatusCode.toString());
                    frm.doc.actual_delivery_date = trackingData.ActualDeliveryDate;
                    frm.doc.city_recipient = trackingData.CityRecipient;
                    frm.doc.city_sender = trackingData.CitySender;
                    frm.save();
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
            return 'Невдала спроба доставки через відсутність Одержувача на адресі або звязку з ним';
        case '112':
            return 'Дата доставки перенесена Одержувачем';
        default:
            return 'Невідомий статус';
    }
}

function select_from_available_services(frm, available_services) {
    // Опрацювання вибору послуги доставки та створення відвантаження...
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
            var custom_delivery_payer = frm.doc.custom_delivery_payer; // Отримання значення поля "Delivery Payer"
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
                    value_of_goods: frm.doc.value_of_goods,
                    custom_delivery_payer: custom_delivery_payer //add custom_delivery_payer
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
