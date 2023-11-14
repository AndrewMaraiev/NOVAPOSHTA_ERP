from __future__ import unicode_literals
import json
import requests
from pprint import pprint
from time import sleep
from frappe import _
from frappe.utils.pdf import get_pdf
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils.password import get_decrypted_password
from requests import post
from . import novaposhta
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

from frappe.utils.response import build_response

import base64

import frappe
from erpnext.stock.doctype import shipment as shipment_doctype, shipment_parcel as shipment_parcel_doctype
from erpnext_shipping.erpnext_shipping.doctype.novaposhta.np_client import NovaPoshtaApi
from erpnext_shipping.erpnext_shipping.doctype.novaposhta_settings.novaposhta_settings import NovaPoshtaSettings
from erpnext_shipping.erpnext_shipping.utils import show_error_alert
from frappe import whitelist
from collections import defaultdict
from decimal import Decimal
from frappe.utils.password import get_decrypted_password



NOVAPOSHTA_PROVIDER = "NovaPoshta"


class NovaPoshta(Document):
    @whitelist()
    def get_areas(self):
        client = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        addresses = client.address
        areas = addresses.get_areas()
        print(areas.json())
        areas_js = areas.json()
        areas_list = areas_js.get('data')
        if not areas_list:
            return
        for area in areas_list:
            exist = frappe.db.exists({"doctype": 'NovaPoshta areas', 'ref': area.get('Ref')})
            if exist:
                continue

            new_doc = frappe.get_doc({
                "doctype": 'NovaPoshta areas',
                'country': "Ukraine",
                'areascenter': area.get('AreasCenter'),
                'description': area.get('Description'),
                'ref': area.get('Ref')
            })
            new_doc.save()

    @whitelist()
    def get_cities(self):
        client = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        cities = client.address.get_cities()
        cities_data = cities.json().get('data', [])

        if not cities_data:
            return

        for city in cities_data:
            exist = frappe.db.exists({"doctype": 'NovaPoshta cities', 'ref': city.get('Ref')})
            if exist:
                continue
            pprint(cities)
            new_doc = frappe.get_doc({
                'doctype': 'NovaPoshta cities',
                'country': "Ukraine",
                'city_name': city.get('Description'),
                'ref': city.get('Ref'),
                'description': city.get('Description'),
                'area': city.get('Area'),
                'settlement_type': city.get('SettlementType')
            }, no_label=True)
            new_doc.save()

    @whitelist()
    def get_warehouses(self):
        client = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        warehouses = client.address.get_warehouses()
        warehouses_data = warehouses.json().get('data', [])

        if not warehouses_data:
            return

        for warehouse in warehouses_data:
            exist = frappe.db.exists({'doctype': 'NovaPoshta Warehouse', 'ref': warehouse.get('Ref')})
            if exist:
                continue
            pprint(warehouse)
            

            new_doc = frappe.get_doc({
                'doctype': 'NovaPoshta Warehouse',
                'country': "Ukraine",
                'warehouse_name': warehouse.get('Description'),
                'ref': warehouse.get('Ref'),
                'description': warehouse.get('Description'),
                'city': warehouse.get('CityRef'),
                'area': warehouse.get('SettlementAreaDescription'),
                'warehouse_index': warehouse.get('WarehouseIndex'),
                
            })
            new_doc.save()


class NovaPoshtaUtils:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or get_decrypted_password(
            "NovaPoshta Settings", "NovaPoshta Settings", "api_key", raise_exception=False
        )
        self.enabled = frappe.db.get_value("NovaPoshta", "NovaPoshta", "enabled")
        self.api_endpoint = "https://api.novaposhta.ua/v2.0/json/"
        self.api = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        if not self.enabled:
            link = frappe.utils.get_link_to_form(
                "NovaPoshta", "NovaPoshta", frappe.bold("NovaPoshta Settings")
            )
            frappe.throw(
                _("Please enable NovaPoshta Integration in {0}".format(link)),
                title=_("Mandatory"),
            )
            
    def get_available_services(
        self,
        pickup_city_ref, 
        delivery_city_ref,
        shipment_parcel: dict,
        value_of_goods: Decimal,
        ):
        
        body = {
            "mmodelName" : "InternetDocument",
            "calledMethod" : "getDocumentPrice",
            "apiKey" : self.api_key
        }
    
        
        headers = {"content-type": "application/json"}
        
        weight = shipment_parcel[0].get("weight")
        length = shipment_parcel[0].get("length")
        width = shipment_parcel[0].get("width")
        height = shipment_parcel[0].get("height")
        VolumeGeneral = (length * width * height) / 4000

             
        delivery_price_data = self.calculate_delivery_price(
            city_sender=pickup_city_ref,
            city_recipient=delivery_city_ref,
            weight=weight,
            cost=value_of_goods,
            seats_amount="1",
            pack_count="1", # TODO implement getting data from form
        )
        
        data = delivery_price_data.get("data", [])
        pprint(delivery_price_data)

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

    def calculate_delivery_price(self, city_sender, city_recipient, weight, cost, seats_amount='1', pack_count='1'):
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
        pickup_city_ref,
        delivery_city_ref,
        pickup_warehouse_ref,
        delivery_warehouse_ref,
        shipment_parcel,
        recipient_full_name,
        sender_phone,
        recipient_phone,
        description_of_content,
        pickup_date,
        value_of_goods,
        service_info='WarehouseWarehouse',
    ):
        

        if isinstance(shipment_parcel, str):
            try:
                shipment_parcel = json.loads(shipment_parcel)
            except json.JSONDecodeError as e:
                raise Exception("Invalid shipment_parcel JSON format") from e
            
        shipment_parcel = shipment_parcel[0]
        
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
        print(pickup_counterparty_ref)

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

        recipient_contacts = self.get_counterparty_contacts(delivery_counterparty_ref)
        sender_contact = self.get_counterparty_contacts(pickup_counterparty_ref)[0]
        sender_contact_ref = sender_contact['Ref']
        sender_phone = sender_contact['Phones']
    
        first, last, middle = recipient_full_name.split(' ')

        recipient_contact = self.find_contact_by_full_name(
            recipient_contacts,
            last_name = last,
            middle_name= middle,
            first_name= first,
            phone= recipient_phone
        )
        print("RCP: ",recipient_contact)
        
        if not recipient_contact:
            recipient_contact = self.create_recipient_contact_person(
                last_name = last,
                middle_name= middle,
                first_name= first,
                email= '',
                phone=recipient_phone
            )
            print("RCP: ",recipient_contact)
            
            if not recipient_contact:
                print('Failed to create recipient contact')
                raise Exception("Failed to create recipient contact")
        recipient_contact_person_ref = recipient_contact['Ref']
        recipient_contact_person_phone = recipient_contact['Phones']
        
        print('Create waybill')
        print(shipment_parcel)
        
        length = shipment_parcel.get("length")
        width = shipment_parcel.get("width")
        height = shipment_parcel.get("height")        
        VolumeGeneral = ((length /100) * (width /100) * (height /100))
        
        print(VolumeGeneral)
        print(shipment_parcel.get("weight"))
        
        
        waybill = self.create_express_waybill(
            city_sender_ref = pickup_city_ref, 
            sender_ref = pickup_counterparty_ref,
            sender_address_ref = pickup_warehouse_ref,
            sender_contact_ref = sender_contact_ref,
            sender_contact_phone = sender_phone,
            city_recipient_ref = delivery_city_ref,
            recipient_ref = delivery_counterparty_ref,
            recipient_address_ref = delivery_warehouse_ref,
            recipient_contact_ref = recipient_contact_person_ref,
            recipient_contact_phone = recipient_contact_person_phone,
            description_of_content=description_of_content,
            weight=shipment_parcel.get("weight"),
            volume_general=VolumeGeneral,
            value_of_goods=value_of_goods
        )
        print(waybill)

        waybill_ref = waybill['data'][0]['Ref']
        waybill_number = waybill['data'][0]['IntDocNumber']
        print(waybill_ref)
        print(waybill_number)
        
        print("Waybill created")
        if waybill_number:
            return {'waybill_number': waybill_number, 'waybill_ref': waybill_ref}
        raise Exception("Failed to create waybill")
    
    @staticmethod
    def find_contact_by_full_name(
            contact_list: list[dict],
            last_name: str,
            middle_name: str,
            first_name: str,
            phone: str
        ) -> dict | None:
            for contact in contact_list:
                ln = contact.get('LastName', '') if contact.get('LastName', '') else '' 
                fn = contact.get('FirstName', '') if contact.get('FirstName', '') else ''
                mn = contact.get('MiddleName', '') if contact.get('MiddleName', '') else ''
                ph = contact.get('Phones', '') if contact.get('Phones', '') else ''
                
                if not ph.startswith('+'):
                    ph = '+' + ph
                
                full_name = ln + fn + mn + ph
                target_name = last_name + first_name + middle_name + phone
                
                if full_name != target_name:
                    continue
                return contact
         
    def get_counterparty_contacts(self, cp_ref):
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
        
    def create_recipient_contact_person(self, first_name, middle_name, last_name, phone, email):
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
    
    def create_express_waybill(
            self,
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
            description_of_content,
            weight,
            volume_general,
            value_of_goods
        ):  
    
            result = post(self.api_endpoint, json={
                "apiKey": self.api_key,
                "modelName": "InternetDocument",
                "calledMethod": "save",
                "methodProperties": {
                    "PayerType": "Recipient",
                    "PaymentMethod": "Cash",
                    "CargoType": "Cargo",
                    "VolumeGeneral": volume_general,
                    "Weight": weight,
                    "ServiceType": "WarehouseWarehouse",
                    "SeatsAmount": "1",
                    "Description": description_of_content,
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
        
@frappe.whitelist()      
def get_label(waybill_number):
    api_key = get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key")
    api_endpoint = 'https://my.novaposhta.ua/orders/printMarking100x100'

    html_print_url = f'{api_endpoint}/orders/printMarking100x100/orders[]/{waybill_number}/type/html/apiKey/{api_key}/zebra'

    # Виконання запиту на отримання HTML-файлу з маркуванням
    response = requests.post(html_print_url)

    if response.status_code == 200:
        # Повернення HTML-файлу з маркуванням
        return response.text
    else:
        # Якщо отримання HTML не вдалося, викидаємо виняток
        raise Exception('Failed to retrieve label HTML')

@frappe.whitelist() 
def get_tracking_data(waybill_number, delivery_contact):
    api_endpoint = "https://api.novaposhta.ua/v2.0/json/"

    api_key = get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key")

    body = {
        "apiKey": api_key,
        "modelName": "TrackingDocument",
        "calledMethod": "getStatusDocuments",
        "methodProperties": {
            "Documents": [
                {
                    "DocumentNumber": waybill_number,
                    "Phone": delivery_contact
                }
            ]
        }
    }

    response = requests.post(api_endpoint, json=body)
    pprint(requests)

    if response.status_code != 200:
        raise Exception(f"Error getting tracking data for {waybill_number}: {response.status_code}")

    return response.json()

