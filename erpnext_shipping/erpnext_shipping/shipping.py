from __future__ import unicode_literals
from erpnext.stock.doctype.delivery_note.test_delivery_note import create_delivery_note
import frappe
import json
from six import string_types
from frappe import _
from frappe.utils import flt
from erpnext.stock.doctype.shipment.shipment import get_company_contact
from erpnext_shipping.erpnext_shipping.utils import get_address, get_contact, match_parcel_service_type_carrier
from erpnext_shipping.erpnext_shipping.doctype.novaposhta.novaposhta import NOVAPOSHTA_PROVIDER, NovaPoshtaUtils
from erpnext_shipping.erpnext_shipping.doctype.ukrposhta.ukrposhta import UKRPOSHTA_PROVIDER, UkrposhtaUtils
import requests
from pprint import pprint

@frappe.whitelist()
def get_areas():
    areas = NovaPoshtaUtils().get_areas()
    return areas

@frappe.whitelist()
def fetch_shipping_rates(**kwargs):
    service_provider = kwargs.get('service_provider')
    shipment_parcel = kwargs.get('shipment_parcel')
    value_of_goods = kwargs.get('value_of_goods')
    pickup_city_ref  = kwargs.get('pickup_city_ref')
    delivery_city_ref  = kwargs.get('delivery_city_ref')
    sender_address = kwargs.get('sender_address')
    recipient_address = kwargs.get('recipient_address')
    shipment_details = kwargs.get('shipment_details')
    sd = kwargs.get('sd')
        
    frappe.logger().debug(f"service_provider: {service_provider}")

    shipment_parcel = json.loads(shipment_parcel) if isinstance(shipment_parcel, str) else shipment_parcel
    shipment_details = json.loads(shipment_details) if isinstance(shipment_details, str) else shipment_details
    sd = json.loads(sd) if isinstance(sd, str) else sd

    if sender_address and sender_address not in ['default_sender_address']:
        sender_address = json.loads(sender_address) if isinstance(sender_address, str) else sender_address
    else:
        sender_address = {}

    if recipient_address and recipient_address not in ['default_recipient_address']:
        recipient_address = json.loads(recipient_address) if isinstance(recipient_address, str) else recipient_address
    else:
        recipient_address = {}

    sender_postcode = sender_address.get('postcode') if sender_address else None
    recipient_postcode = recipient_address.get('postcode') if recipient_address else None

    shipment_prices = []

    if service_provider == 'NovaPoshta' and frappe.db.get_single_value('NovaPoshta', 'enabled'):
        novaposhta = NovaPoshtaUtils()
        novaposhta_prices = novaposhta.get_available_services(
            pickup_city_ref,
            delivery_city_ref,
            shipment_parcel,
            value_of_goods
        ) or []
        shipment_prices.extend(novaposhta_prices)

    elif service_provider == 'Ukrposhta' and frappe.db.get_single_value('Ukrposhta', 'enabled'):
        ukrposhta = UkrposhtaUtils()
        ukrposhta_prices = ukrposhta.get_available_services(
            sd,
            value_of_goods,
            sender_postcode,
            recipient_postcode,
            shipment_parcel
        ) or []
        shipment_prices.extend(ukrposhta_prices)

    if not shipment_prices:
        frappe.msgprint(_("No shipping rates available for the selected route and parcel type."))
        return []

    return shipment_prices

@frappe.whitelist()
def create_shipment(**kwargs):
    shipment = kwargs.get('shipment')
    pickup_city_ref = kwargs.get('pickup_city_ref')
    delivery_city_ref = kwargs.get('delivery_city_ref')
    pickup_warehouse_name = kwargs.get('pickup_warehouse_name')
    delivery_warehouse_name = kwargs.get('delivery_warehouse_name')
    shipment_parcel = kwargs.get('shipment_parcel')
    recipient_full_name = kwargs.get('recipient_full_name')
    description_of_content = kwargs.get('description_of_content')
    pickup_date = kwargs.get('pickup_date')
    value_of_goods = kwargs.get('value_of_goods')
    custom_delivery_payer = kwargs.get('custom_delivery_payer')
    service_info = 'WarehouseWarehouse'
    
    shipment_doc = frappe.get_doc('Shipment', shipment)
    frappe.logger().debug(f"Shipment Doc: {shipment_doc}")

    sender_phone = kwargs.get('sender_phone', shipment_doc.get('custom_sender_mobile_phone'))
    recipient_phone = kwargs.get('recipient_phone', shipment_doc.get('custom_recipient_mobile_phone'))

    dn = shipment_doc.shipment_delivery_note
    payment_method = None
    if dn is not None and len(dn) > 0:
        dn = dn[0]
        dn = frappe.get_doc('Delivery Note', {'name': dn.delivery_note})
        form = frappe.get_doc('Shipment Form', {'name': dn.custom_shipment_form})
        payment_method = form.payment_method

    def log_and_raise_error(error_message, title):
        max_length = 140
        truncated_title = title[:max_length]
        truncated_error_message = error_message[:max_length]
        frappe.log_error(message=truncated_error_message, title=truncated_title)
        frappe.msgprint(f'{truncated_title}: {truncated_error_message}')
        raise Exception(truncated_error_message)

    shipment_info = None

    frappe.logger().debug(f"Carrier Service: {shipment_doc.carrier_service}")
    if shipment_doc.service_provider == 'NovaPoshta':
        pickup_warehouse_object = frappe.get_doc('NovaPoshta Warehouse', pickup_warehouse_name)
        pickup_warehouse_ref = pickup_warehouse_object.ref
        delivery_warehouse_object = frappe.get_doc('NovaPoshta Warehouse', delivery_warehouse_name)
        delivery_warehouse_ref = delivery_warehouse_object.ref

        sender_warehouseindex = pickup_warehouse_object.warehouseindex
        recipient_warehouseindex = delivery_warehouse_object.warehouseindex

        novaposhta = NovaPoshtaUtils()
        try:
            shipment_info = novaposhta.create_shipment(
                pickup_city_ref=pickup_city_ref,
                delivery_city_ref=delivery_city_ref,
                pickup_warehouse_ref=pickup_warehouse_ref,
                delivery_warehouse_ref=delivery_warehouse_ref,
                shipment_parcel=shipment_parcel,
                recipient_full_name=recipient_full_name,
                sender_phone=sender_phone,
                recipient_phone=recipient_phone,
                description_of_content=description_of_content,
                pickup_date=pickup_date,
                value_of_goods=value_of_goods,
                custom_delivery_payer=custom_delivery_payer,
                service_info=service_info,
                sender_warehouseindex=sender_warehouseindex,
                recipient_warehouseindex=recipient_warehouseindex,
                payment_method=payment_method,
            )
            frappe.logger().debug(f"NovaPoshta Shipment Info: {shipment_info}")
        except Exception as e:
            log_and_raise_error(str(e), "NovaPoshta Shipment Creation Error")
            
            print('Shipment Doc from UTILS:', shipment_doc)
            print(shipment_info)

        if not shipment_info:
            frappe.msgprint('Failed to create shipment for NovaPoshta')
        else:
            frappe.db.set_value('Shipment', shipment, 'shipment_id', shipment_info.get('waybill_number'))
            frappe.db.set_value('Shipment', shipment, 'waybill_ref', shipment_info.get('waybill_ref'))
            frappe.db.set_value('Shipment', shipment, 'status', 'Booked')
            frappe.msgprint('Shipment created for NovaPoshta')

    elif shipment_doc.service_provider == 'Ukrposhta':
        ukrposhta = UkrposhtaUtils()
        
        sender_postcode = shipment_doc.get('custom_pickup_postcode')
        recipient_postcode = shipment_doc.get('custom_delivery_posctode')
    
        try:
            shipment_info = ukrposhta.create_shipment(
                shipment_doc={
                    'custom_sender_mobile_phone': sender_phone,
                    'custom_recipient_mobile_phone': recipient_phone,
                    'custom_pickup_postcode': sender_postcode,
                    'custom_delivery_posctode': recipient_postcode,
                    'shipment_parcel': json.loads(shipment_parcel),
                    'description': description_of_content,
                    'value_of_goods': value_of_goods
                }
            )
            
        
            frappe.logger().debug(f"Ukrposhta Shipment Info: {shipment_info}")
            print('Shipment Doc from UTILS:', shipment_doc)
            print(shipment_info)
        except Exception as e:
            frappe.log_error(str(e))
            frappe.msgprint(f'Failed to create shipment for Ukrposhta: {str(e)}')
            raise e

        if not shipment_info:
            frappe.msgprint('Failed to create shipment for Ukrposhta')
        else:
            try:
                frappe.db.set_value('Shipment', shipment, 'shipment_id', shipment_info['parcels'][0]['barcode'])
                frappe.db.set_value('Shipment', shipment, 'waybill_ref', shipment_info['parcels'][0]['uuid'])
                frappe.db.set_value('Shipment', shipment, 'status', 'Booked')
                frappe.msgprint('Shipment created for Ukrposhta')
            except Exception as e:
                frappe.log_error(f"Error updating shipment status: {str(e)}")
                frappe.msgprint(f"Failed to update shipment status: {str(e)}")

    else:
        print(shipment_doc.carrier_service)

    return shipment_info

def get_address(address_name):
    address = frappe.get_doc("Address", address_name)
    return address

def get_contact(contact_name):
    contact = frappe.get_doc("Contact", contact_name)
    return contact

def get_company_contact(user):
    user_object = frappe.get_doc("User", user)
    print(dir(user_object))
    company = user_object.company
    contact = frappe.get_list("Contact", filters={"company": company}, limit=1)
    return contact[0] if contact else None

def match_parcel_service_type_carrier(prices, keys):
    matched_prices = {}
    for key in keys:
        matched_prices[key] = []

    for price in prices:
        for key in keys:
            if key in price:
                matched_prices[key].append(price)

    return matched_prices
