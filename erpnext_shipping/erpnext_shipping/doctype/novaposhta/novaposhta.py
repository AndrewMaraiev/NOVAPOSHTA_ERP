from __future__ import unicode_literals
import json
import requests
from pprint import pprint
from time import sleep
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils.password import get_decrypted_password
from requests import post

import frappe
from erpnext.stock.doctype import shipment, shipment_parcel
from erpnext_shipping.erpnext_shipping.doctype.novaposhta.np_client import ExpressWaybill, NovaPoshtaApi
from erpnext_shipping.erpnext_shipping.doctype.novaposhta_settings.novaposhta_settings import NovaPoshtaSettings
from erpnext_shipping.erpnext_shipping.utils import show_error_alert

NOVAPOSHTA_PROVIDER = "NovaPoshta"


class NovaPoshtaUtils:
    def __init__(self, api_key: str = None):
        
        self.api_key = api_key or get_decrypted_password(
            "NovaPoshta Settings", "NovaPoshta Settings", "api_key", raise_exception=False
        )
        self.enabled = frappe.db.get_value("NovaPoshta", "NovaPoshta", "enabled")
        self.api_endpoint = "https://api.novaposhta.ua/v2.0/json/"
        self.api = NovaPoshtaApi(api_key='ed0b9e715fefe9ba6b2a3ec7cce89a1a')
        if not self.enabled:
            link = frappe.utils.get_link_to_form(
                "NovaPoshta", "NovaPoshta", frappe.bold("NovaPoshta Settings")
            )
            frappe.throw(
                _("Please enable NovaPoshta Integration in {0}".format(link)),
                title=_("Mandatory"),
            )
     
        
    def get_available_services(self, **kwargs):
        print('+'*100)
        print("get_available_services")
        print('+'*100)
        headers = {"content-type": "application/json"}
        kwargs["modelName"] = "InternetDocument"
        kwargs["calledMethod"] = "getDocumentPrice"
        kwargs["apiKey"] = self.api_key

        form = kwargs
        pprint(form.get("Weight"))
        pickup_address = kwargs.get("pickup_address")
        delivery_address = kwargs.get("delivery_address")
        if "Відділення" in pickup_address.address_title and "№" not in pickup_address.address_title:
            pickup_address.address_title = pickup_address.address_title.replace(
            "Відділення ", "Відділення №"
        )
        if "Відділення" in delivery_address.address_title and "№" not in delivery_address.address_title:
            delivery_address.address_title = delivery_address.address_title.replace(
            "Відділення ", "Відділення №"
        )
        
        pickup_warehouse = self.get_warehouse_ref(
            city=pickup_address.city,
            title=pickup_address.address_title,
        )["data"][0]
        pprint(pickup_warehouse)
        delivery_warehouse = self.get_warehouse_ref(
            city=delivery_address.city,
            title=delivery_address.address_title,
        )["data"][0]

        
        # Access the list elements directly without using json.loads()
        shipment_parcel = kwargs["shipment_parcel"]
        weight = shipment_parcel[0].get("weight")
        length = shipment_parcel[0].get("length")
        width = shipment_parcel[0].get("width")
        height = shipment_parcel[0].get("height")
        VolumeGeneral = (length * width * height) / 4000
        
        print(weight)
        print(VolumeGeneral)   
             
        delivery_price_data = self.calculate_delivery_price(
            city_sender=pickup_warehouse["SettlementRef"],
            city_recipient=delivery_warehouse["SettlementRef"],
            weight=shipment_parcel[0].get("weight"),
            cost=kwargs.get("value_of_goods"),
            seats_amount="1",
            pack_count="1",
        )
        
        data = delivery_price_data.get("data", [])
        pprint(delivery_price_data)
        print('*'*100)

        if len(data) == 0:
            return []
        service_data = frappe._dict()
        service_data.service_provider = 'NovaPoshta'
        service_data.carrier = "NovaPoshta"
        service_data.carrier_name = "NovaPoshta"
        service_data.service_name = "WarehouseWarehouse delivery"
        service_data.Price = data[0]['Cost']
        service_data.currency = 'UAH'
        
        return [service_data]
    

    def get_novaposhta_shipping_rates(self, args):
        novaposhta = NovaPoshtaUtils()
        shipment_parcel_data = args.get('shipment_parcel')
        if shipment_parcel_data:
            shipment_parcel_data = json.loads(shipment_parcel_data)
        if shipment_parcel_data:
            shipment_parcel_data = shipment_parcel_data[0]
        else:
            frappe.throw(_('Shipment Parcel data not found'))

        
        weight = frappe.get_doc('Shipment Parcel', shipment_parcel_data.get('shipment_parcel')).weight
        cost_of_goods = flt(args.get('value_of_goods'))

        shipping_rates = novaposhta.get_novaposhta_shipping_rates(
            recipient_city_ref=args.get('recipient_city_ref'),
            sender_city_ref=args.get('sender_city_ref'),
            service_type=args.get('service_type'),
            cargo_type=args.get('cargo_type'),
            weight=flt(weight),
            cost_of_goods=flt(cost_of_goods)
        )
        return shipping_rates
    
    
    def calculate_delivery_price(self, city_sender, city_recipient, weight, cost, seats_amount = '1', pack_count = '1'):
        print('*'*100)
        print("calculate_delivery_price")
        print("_"*100)
        print(weight)
        body = {
            "apiKey": self.api_key,
            "modelName": "InternetDocument",
            "calledMethod": "getDocumentPrice",
            "methodProperties": {
                "CitySender" : city_sender,
                "CityRecipient" : city_recipient,
                "Weight" : weight,
                "ServiceType" : "WarehouseWarehouse",
                "Cost" : cost,
                "CargoType" : "Cargo",
                "SeatsAmount" : seats_amount,
                "RedeliveryCalculate" : {
                    "CargoType":"Money",
                    "Amount":"100"
                },
                "PackCount" : pack_count
            }
        }
        # response = post(self.api_endpoint, json=body)
        # pprint(body)
        return post(self.api_endpoint, json=body).json()
    
    def get_warehouse_ref(self, city, title):
        body = {
            "apiKey": self.api_key,
            "modelName": "Address",
            "calledMethod": "getWarehouses",
            "methodProperties": {
                "CityName" : city,
                "Page" : "1",
                "Limit" : "50",
                "Language" : "UA",
                "FindByString": title
            }
        }
        response = post(self.api_endpoint, json=body)
        return response.json()
    
    def get_city_ref(self, city):
        body = {
            "apiKey": self.api_key,
            "modelName": "Address",
            "calledMethod": "getCities",
            "methodProperties": {
                "FindByString": city,
                "Page": "1",
                "Limit": "50",
            },
        }
        response = requests.post(self.api_endpoint, json=body)
        data = response.json()
        data = data["data"]
        return data[0]["Ref"]
    
    def create_shipment(
        self,
        pickup_address,
        delivery_address,
        shipment_parcel,
        description_of_content,
        pickup_date,
        value_of_goods,
        service_info='WarehouseWarehouse',
        pickup_contact=None,
        delivery_contact=None
    
    ):
        pickup_address_doc = frappe.get_doc("Address", pickup_address)
        pickup_city_ref = self.get_city_ref(pickup_address_doc.city)
        pickup_address_warehouse = self.get_warehouse_ref(pickup_address_doc.city, pickup_address_doc.address_title)
        pickup_address_warehouse_ref = pickup_address_warehouse["data"][0]["Ref"]

        delivery_address_doc = frappe.get_doc("Address", delivery_address)
        delivery_city_ref = self.get_city_ref(delivery_address_doc.city)
        delivery_address_warehouse = self.get_warehouse_ref(delivery_address_doc.city, delivery_address_doc.address_title)
        delivery_address_warehouse_ref = delivery_address_warehouse["data"][0]["Ref"]

        shipment_parcel = json.loads(shipment_parcel)[0]

        sender = post(self.api_endpoint, json={
            "apiKey": self.api_key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterparties",
            "methodProperties": {
                "CounterpartyProperty": "Sender",
                "Page": "1"
            }
        }).json()
        
        pickup_counterparty_ref = sender['data'][0]['Ref']

        recipient = post(self.api_endpoint, json={
            "apiKey": self.api_key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterparties",
            "methodProperties": {
                "CounterpartyProperty": "Recipient",
                "Page": "1"
            }
        }).json()
        delivery_counterparty_ref = recipient['data'][0]['Ref']
        print(delivery_counterparty_ref)

        def get_counterparty_contacts(cp_ref):
            result = post(self.api_endpoint, json={
                "apiKey": self.api_key,
                "modelName": "Counterparty",
                "calledMethod": "getCounterpartyContactPersons",
                "methodProperties": {
                    "Ref": cp_ref,
                    "Page": "1"
                }
            }).json()['data']
            return result

        recipient_contacts = get_counterparty_contacts(delivery_counterparty_ref)
        sender_contact = get_counterparty_contacts(pickup_counterparty_ref)[0]
        sender_contact_ref = sender_contact['Ref']
        sender_phone = sender_contact['Phones']

        def find_contact_by_full_name(
            contact_list: list[dict],
            last_name: str,
            middle_name: str,
            first_name: str,
            email: str,
            phone: str
        ) -> dict | None:
            for contact in contact_list:
                ln = contact.get('LastName', '') if contact.get('LastName', '') else '' 
                fn = contact.get('FirstName', '') if contact.get('FirstName', '') else ''
                mn = contact.get('MiddleName', '') if contact.get('MiddleName', '') else ''
                em = contact.get('Email', '') if contact.get('Email', '') else ''
                ph = contact.get('Phones', '') if contact.get('Phones', '') else ''
                
                if not ph.startswith('+'):
                    ph = '+' + ph
                
                full_name = ln + fn + mn + em + ph
                target_name = last_name + first_name + middle_name + email + phone
                
                if full_name != target_name:
                    continue
                return contact
    
        def create_recipient_contact_person(first_name, middle_name, last_name, phone, email):
            result = post(self.api_endpoint, json={
                "apiKey": self.api_key,
                "modelName": "Counterparty",
                "calledMethod": "save",
                "methodProperties": {
                    "FirstName": first_name,
                    "MiddleName": middle_name,
                    "LastName": last_name,
                    "Phone": phone,
                    "Email": email,
                    "CounterpartyType": "PrivatePerson",
                    "CounterpartyProperty": "Recipient"
                }
            }).json()
            if 'data' in result and result['data']:
                return result['data'][0]
            else:
                raise Exception("Failed to create recipient contact")
        # # Якщо немає такого контакту, то створюємо новий контакт контрагента
        recipient_contact = find_contact_by_full_name(
            recipient_contacts,
            last_name = delivery_contact.last_name,
            middle_name= delivery_contact.middle_name,
            first_name= delivery_contact.first_name,
            email= delivery_contact.email_id,
            phone= delivery_contact.mobile_no
        )
        
        if not recipient_contact:
            result = create_recipient_contact_person(
                last_name = delivery_contact.last_name,
                middle_name= delivery_contact.middle_name,
                first_name= delivery_contact.first_name,
                email= delivery_contact.email_id,
                phone= delivery_contact.mobile_no
            )
            # check result
            if not result:
                print('Failed to create recipient contact')
                raise Exception("Failed to create recipient contact")
        print('AAAAAAAAAAAA')
        recipient_contact_person_ref = recipient_contact['Ref']
        recipient_contact_person_phone = recipient_contact['Phones']
        
        
        def create_express_waybill(
                city_sender_ref,
                sender_ref,
                sender_address_ref,
                sender_contact_ref,
                sender_contact_phone,
                city_recipient_ref,
                recipient_ref,
                recipient_address_ref,
                recipient_contact_ref,
                recipient_contact_phone,
                weight
        ):  
    
            result = post(self.api_endpoint, json={
                "apiKey": self.api_key,
                "modelName": "InternetDocument",
                "calledMethod": "save",
                "methodProperties": {
                    "PayerType": "Recipient",
                    "PaymentMethod": "Cash",
                    "CargoType": "Cargo",
                    "VolumeGeneral": "0.01",
                    "Weight": weight or frappe.get_doc('Shipment Parcel', shipment_parcel).weight,
                    "ServiceType": "WarehouseWarehouse",
                    "SeatsAmount": "1",
                    "Description": "Додатковий опис відправлення",
                    "Cost": value_of_goods,
                    "CitySender": city_sender_ref,
                    "Sender": sender_ref,
                    "SenderAddress": sender_address_ref,
                    "ContactSender": sender_contact_ref,
                    "SendersPhone": sender_contact_phone,
                    "CityRecipient": city_recipient_ref,
                    "Recipient": recipient_ref,
                    "RecipientAddress": recipient_address_ref,
                    "ContactRecipient": recipient_contact_ref,
                    "RecipientsPhone": recipient_contact_phone
                }
            }).json()
            return result
        print('Create waybill')
        
        waybill = create_express_waybill(
            city_sender_ref = pickup_city_ref, 
            sender_ref = pickup_counterparty_ref,
            sender_address_ref = pickup_address_warehouse_ref,
            sender_contact_ref = sender_contact_ref,
            sender_contact_phone = sender_phone,
            city_recipient_ref = delivery_city_ref,
            recipient_ref = delivery_counterparty_ref,
            recipient_address_ref = delivery_address_warehouse_ref,
            recipient_contact_ref = recipient_contact_person_ref,
            recipient_contact_phone = recipient_contact_person_phone,
            weight = 'weight' or frappe.get_doc('Shipment Parcel', shipment_parcel).weight

        )

        waybill_ref = waybill['data'][0]['Ref']
        waybill_number = waybill['data'][0]['IntDocNumber']
        print('AAAAAAAAAAAA')
        print(waybill_ref)
        print('BBBBBBBBBBBB')
        print(waybill_number)
        
        print("Waybill created")
        if waybill_number:
            return waybill_number
        
        raise Exception("Failed to create waybill")

        