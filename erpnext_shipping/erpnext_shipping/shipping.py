# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies and contributors
# For license information, please see license.txt
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
from erpnext_shipping.erpnext_shipping.doctype.packlink.packlink import PACKLINK_PROVIDER, PackLinkUtils
from erpnext_shipping.erpnext_shipping.doctype.sendcloud.sendcloud import SENDCLOUD_PROVIDER, SendCloudUtils
import requests
from pprint import pprint

@frappe.whitelist()
def get_areas():
    areas = NovaPoshtaUtils().get_areas()
    return areas

@frappe.whitelist()
def fetch_shipping_rates(pickup_from_type, delivery_to_type, pickup_address_name, delivery_address_name,
                         shipment_parcel, description_of_content, pickup_date, value_of_goods,
                         pickup_contact_name=None, delivery_contact_name=None, weight=None, length=None, width=None, height=None):
    shipment_parcel = json.loads(shipment_parcel)
    # Отримання ваги та габаритів вантажу з shipment_parcel
    weight = shipment_parcel[0].get('Weight')
    length = shipment_parcel[0].get('Length')
    width = shipment_parcel[0].get('Width')
    height = shipment_parcel[0].get('Height')
    shipment_prices = []
    novaposhta_enabled = frappe.db.get_single_value('NovaPoshta', 'enabled')
    packlink_enabled = frappe.db.get_single_value('Packlink', 'enabled')
    sendcloud_enabled = frappe.db.get_single_value('SendCloud', 'enabled')
    pickup_address = get_address(pickup_address_name)
    delivery_address = get_address(delivery_address_name)

    if novaposhta_enabled:
        pickup_contact = None
        delivery_contact = None
        if pickup_from_type != 'Company':
            pickup_contact = get_contact(pickup_contact_name)
        else:
            pickup_contact = get_company_contact(user=pickup_contact_name)

        if delivery_to_type != 'Company':
            delivery_contact = get_contact(delivery_contact_name)
        else:
            delivery_contact = get_company_contact(user=delivery_contact_name)

        novaposhta = NovaPoshtaUtils()  # Замініть на відповідний клас NovaPoshtaUtils
        novaposhta_prices = novaposhta.get_available_services(
            delivery_to_type=delivery_to_type,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            shipment_parcel=shipment_parcel,
            description_of_content=description_of_content,
            pickup_date=pickup_date,
            value_of_goods=value_of_goods,
            pickup_contact=pickup_contact,
            delivery_contact=delivery_contact,
        ) or []
        shipment_prices = shipment_prices + novaposhta_prices

    # if packlink_enabled:
    #     packlink = PackLinkUtils()  # Замініть на відповідний клас PackLinkUtils
    #     packlink_prices = packlink.get_available_services(
    #         pickup_address=pickup_address,
    #         delivery_address=delivery_address,
    #         shipment_parcel=shipment_parcel,
    #         pickup_date=pickup_date
    #     ) or []
    #     shipment_prices = shipment_prices + packlink_prices

    # if sendcloud_enabled and pickup_from_type == 'Company':
    #     sendcloud = SendCloudUtils()  # Замініть на відповідний клас SendCloudUtils
    #     sendcloud_prices = sendcloud.get_available_services(
    #         delivery_address=delivery_address,
    #         shipment_parcel=shipment_parcel
    #     ) or []
    #     shipment_prices = shipment_prices + sendcloud_prices[:4]  # remove after fixing scroll issue

    if not shipment_prices:  # check if shipment_prices is empty
        return []
    return shipment_prices


@frappe.whitelist()
def create_shipment(shipment, pickup_from_type, delivery_to_type, pickup_address,
                    delivery_address, shipment_parcel, description_of_content, pickup_date,
                    value_of_goods, service_data, shipment_notific_email=None, tracking_notific_email=None,
                    pickup_contact_name=None, delivery_contact_name=None, delivery_notes=[]):
    # Create Shipment for the selected provider
    service_info = json.loads(service_data)
    shipment_info = None
    try:
        novaposhta = NovaPoshtaUtils()
        sender_name = ''  # Set sender name
        sender_phone = ''  # Set sender phone
        sender_address_warehouse_ref = {'Ref': pickup_address}  # Set sender warehouse address reference
        recipient_name = ''  # Set recipient name
        recipient_phone = ''  # Set recipient phone
        recipient_address_warehouse_ref = {'Ref': delivery_address}  # Set recipient warehouse address reference
        weight = shipment_parcel.get('Weight', 0)  # Set weight
        description = description_of_content  # Set description
        cost = value_of_goods  # Set cost
        print('sender_name', sender_name)   
        shipment_info = novaposhta.create_shipment(
            sender_name,
            sender_phone,
            sender_address_warehouse_ref['Ref'],
            recipient_name,
            recipient_phone,
            recipient_address_warehouse_ref['Ref'],
            weight,
            description,
            cost
        )
        print('shipment_info', shipment_info)
    except Exception as e:
        frappe.log_error(str(e))
    
    pickup_contact = None
    delivery_contact = None
    
    shipment_doc = frappe.get_doc('Shipment', shipment)
    
    if pickup_from_type != 'Company':
        pickup_contact = get_contact(pickup_contact_name)
    else:
        pickup_contact = get_company_contact(user=pickup_contact_name)

    if delivery_to_type != 'Company':
        delivery_contact = get_contact(delivery_contact_name)
    else:
        delivery_contact = get_company_contact(user=delivery_contact_name)

    if shipment_doc.carrier_service == 'NovaPoshta':
        novaposhta = NovaPoshtaUtils()
        try:
            shipment_info = novaposhta.create_shipment(
                pickup_address=pickup_address,
                delivery_address=delivery_address,
                shipment_parcel=shipment_parcel,
                description_of_content=description_of_content,
                pickup_date=pickup_date,
                value_of_goods=value_of_goods,
                service_info=service_info,
                pickup_contact=pickup_contact,
                delivery_contact=delivery_contact,
                # shipment_notific_email=shipment_notific_email,
                # tracking_notific_email=tracking_notific_email,
                # delivery_notes=delivery_notes
            )
            print('shipment_info', shipment_info)
        except Exception as e:
            frappe.log_error(str(e))

    # if shipment == 'Packlink service':
    #     packlink = PackLinkUtils()  # Замініть на відповідний клас PackLinkUtils
    #     shipment_info = packlink.create_shipment(
    #         pickup_address=pickup_address,
    #         delivery_address=delivery_address,
    #         shipment_parcel=shipment_parcel,
    #         description_of_content=description_of_content,
    #         pickup_date=pickup_date,
    #         value_of_goods=value_of_goods,
    #         service_info=service_info,
    #         pickup_contact=pickup_contact,
    #         delivery_contact=delivery_contact,
    #         shipment_notific_email=shipment_notific_email,
    #         tracking_notific_email=tracking_notific_email,
    #         delivery_notes=delivery_notes
    #     )

    # if shipment == 'SendCloud service':
    #     sendcloud = SendCloudUtils()  # Замініть на відповідний клас SendCloudUtils
    #     shipment_info = sendcloud.create_shipment(
    #         delivery_address=delivery_address,
    #         shipment_parcel=shipment_parcel,
    #         description_of_content=description_of_content,
    #         value_of_goods=value_of_goods,
    #         service_info=service_info,
    #         shipment_notific_email=shipment_notific_email,
    #         tracking_notific_email=tracking_notific_email,
    #         delivery_notes=delivery_notes
    #     )

     # Додано перевірку на `None` та виведення повідомлення
    if shipment_info is None:
        frappe.msgprint('Failed to create shipment for NovaPoshta')
    else:
        frappe.db.set_value('Shipment', shipment, 'shipment_id', shipment_info)
        frappe.db.set_value('Shipment', shipment, 'status', 'Booked')
        frappe.msgprint('Shipment created for NovaPoshta')
        
    return shipment_info


def get_address(address_name):
    # Get Address details based on Address Name
    address = frappe.get_doc("Address", address_name)
    return address


def get_contact(contact_name):
    # Get Contact details based on Contact Name
    contact = frappe.get_doc("Contact", contact_name)
    return contact


def get_company_contact(user):
    # Get Company Contact details based on User
    company = frappe.get_doc("User", user).company
    contact = frappe.get_list("Contact", filters={"company": company}, limit=1)
    return contact[0] if contact else None


def match_parcel_service_type_carrier(prices, keys):
    # Match Parcel Service, Type, and Carrier names in the list of prices
    matched_prices = {}
    for key in keys:
        matched_prices[key] = []

    for price in prices:
        for key in keys:
            if key in price:
                matched_prices[key].append(price)

    return matched_prices