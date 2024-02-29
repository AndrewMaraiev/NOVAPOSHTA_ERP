# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
from erpnext.stock.doctype.delivery_note.test_delivery_note import create_delivery_note
import frappe
import json
import ast
from six import string_types
from frappe import _
from frappe.utils import flt
from erpnext.stock.doctype.shipment.shipment import get_company_contact
from erpnext_shipping.erpnext_shipping.utils import get_address, get_contact, match_parcel_service_type_carrier
from erpnext_shipping.erpnext_shipping.doctype.novaposhta.novaposhta import NOVAPOSHTA_PROVIDER, NovaPoshtaUtils
from erpnext_shipping.erpnext_shipping.doctype.packlink.packlink import PACKLINK_PROVIDER, PackLinkUtils
from erpnext_shipping.erpnext_shipping.doctype.sendcloud.sendcloud import SENDCLOUD_PROVIDER, SendCloudUtils
import requests
from pprint import pprint

@frappe.whitelist()
def get_areas():
    areas = NovaPoshtaUtils().get_areas()
    return areas

@frappe.whitelist()
def fetch_shipping_rates(
    pickup_from_type,
    delivery_to_type,
    pickup_city_ref,
    delivery_city_ref,
    shipment_parcel,
    value_of_goods
    ):
    
    shipment_parcel = json.loads(shipment_parcel)
    shipment_prices = []
    novaposhta_enabled = frappe.db.get_single_value('NovaPoshta', 'enabled')

    if novaposhta_enabled:

        novaposhta = NovaPoshtaUtils() 
        novaposhta_prices = novaposhta.get_available_services(
            pickup_city_ref,
            delivery_city_ref,
            shipment_parcel,
            value_of_goods
        ) or []
        shipment_prices = shipment_prices + novaposhta_prices

    if not shipment_prices:  
        return []
    return shipment_prices

<<<<<<< HEAD
=======

>>>>>>> 9d1ae0d9227ebde6f88a702ab8a485108e3ea074

@frappe.whitelist()
def create_shipment(
    shipment,
    pickup_city_ref,
    delivery_city_ref,
    pickup_warehouse_name,
    delivery_warehouse_name,
    shipment_parcel,
    recipient_full_name,
    sender_phone,
    recipient_phone,
    description_of_content,
    pickup_date,
    value_of_goods,
    delivery_payer,  # Додали обов'язковий параметр 'delivery_payer'
    service_info='WarehouseWarehouse'
):
    # Отримання значення поля "Delivery Payer" з аргументу функції
    pprint("Delivery Payer value: {}".format(delivery_payer))

    shipment_info = {}
    pickup_warehouse_object = frappe.get_doc('NovaPoshta Warehouse', pickup_warehouse_name)
    pickup_warehouse_ref = pickup_warehouse_object.ref 
    delivery_warehouse_object = frappe.get_doc('NovaPoshta Warehouse', delivery_warehouse_name)
    delivery_warehouse_ref = delivery_warehouse_object.ref

    # Отримання значень sender_warehouseindex та recipient_warehouseindex
    sender_warehouseindex = pickup_warehouse_object.warehouseindex
    recipient_warehouseindex = delivery_warehouse_object.warehouseindex

    pickup_contact = None
    delivery_contact = None

    shipment_doc = frappe.get_doc('Shipment', shipment)
    
    dn = shipment_doc.shipment_delivery_note
    payment_method = None
    if dn is not None and len(dn) > 0:
        dn = dn[0]
        dn = frappe.get_doc('Delivery Note', {'name': dn.delivery_note})
        
        form = frappe.get_doc('Shipment Form', {'name': dn.custom_shipment_form})
        payment_method = form.payment_method
        

    if shipment_doc.carrier_service == 'NovaPoshta':
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
                delivery_payer=delivery_payer,  #  'Delivery Payer'
                service_info=service_info,
                sender_warehouseindex=sender_warehouseindex,
                recipient_warehouseindex=recipient_warehouseindex,
                payment_method=payment_method,
            )
        except Exception as e:
            frappe.log_error(str(e))
            frappe.msgprint(f'Failed to create shipment for NovaPoshta: {str(e)}')
            raise e

        if not shipment_info:
            frappe.msgprint('Failed to create shipment for NovaPoshta')
        else:
            frappe.db.set_value('Shipment', shipment, 'shipment_id', shipment_info.get('waybill_number'))
            frappe.db.set_value('Shipment', shipment, 'waybill_ref', shipment_info.get('waybill_ref'))
            frappe.db.set_value('Shipment', shipment, 'status', 'Booked')
            frappe.msgprint('Shipment created for NovaPoshta')

    return shipment_info


def get_address(address_name):
    address = frappe.get_doc("Address", address_name)
    return address


def get_contact(contact_name):
    contact = frappe.get_doc("Contact", contact_name)
    return contact


def get_company_contact(user):
    user_object = frappe.get_doc("User", user)
    pprint(dir(user_object))
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
