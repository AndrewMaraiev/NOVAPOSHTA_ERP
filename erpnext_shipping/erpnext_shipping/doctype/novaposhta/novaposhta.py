from __future__ import unicode_literals
import json
import requests
from pprint import pprint
import frappe
import schedule
import time
import math

from frappe import _

from frappe.model.document import Document
from frappe.utils import flt
from requests import post

from erpnext_shipping.erpnext_shipping.doctype.novaposhta.np_client import NovaPoshtaApi

from frappe import whitelist

from decimal import Decimal
from frappe.utils.password import get_decrypted_password
from datetime import datetime
from frappe import enqueue
import schedule


# def test_function1():
#     np = frappe.get_single("NovaPoshta")
#     np.get_waybill(None)
    

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
        page = 1
        limit = 500 

        while True:
            client = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
            cities = client.address.get_cities(page=page)
            cities_data = cities.json().get('data', [])

            if not cities_data:
                break

            for city in cities_data:
                exist = frappe.db.exists({"doctype": 'NovaPoshta cities', 'ref': city.get('Ref')})
                if exist:
                    continue

                new_doc = frappe.get_doc({
                    'doctype': 'NovaPoshta cities',
                    'country': "Ukraine",
                    'city_name': city.get('Description'),
                    'ref': city.get('Ref'),
                    'description': city.get('Description'),
                    'area': city.get('Area'),
                    'settlement_type': city.get('SettlementType')
                })
                new_doc.save()

            page += 1   

    @whitelist()
    def get_warehouses(self):
        client = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        page = 1
        limit = 500

        while True:
            warehouses = client.address.get_warehouses(page=page, limit=limit)
            warehouses_data = warehouses.json().get('data', [])

            if not warehouses_data:
                break

            for warehouse in warehouses_data:
                exist_city = frappe.db.exists({'doctype': 'NovaPoshta cities', 'ref': warehouse.get('CityRef')})
                if not exist_city:
                    continue 

                exist = frappe.db.exists({'doctype': 'NovaPoshta Warehouse', 'ref': warehouse.get('Ref')})
                if exist:
                    continue

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

            page += 1
    
    @whitelist()
    def update_waybill(self):
        api_key = self.get_password(fieldname="api_key", raise_exception=False)
        if api_key:
            self.get_waybill(api_key)
        else:
            print("API key is not configured.")

    def on_update(self):
        enqueue(self.update_waybill)

    @whitelist()
    def get_waybill(self, api_key):
        now = datetime.now()
        current_year = now.year
        date_from = f"01.01.{current_year}"
        date_to = f"31.12.{current_year}"
        api_key = get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key")
        
        all_waybills = []  
        
        def fetch_waybills(document_type):
            total_records = 2000  
            total_pages = math.ceil(total_records / 500)  
            
            for page_number in range(1, total_pages + 1):
                data = {
                    "apiKey": api_key,
                    "modelName": "InternetDocument",
                    "calledMethod": "getDocumentList",
                    "methodProperties": {
                        "DateTimeFrom": date_from,
                        "DateTimeTo": date_to,
                        "Page": str(page_number),
                        "GetFullList": "1",
                        "DateTime": now.strftime("%d.%m.%Y"),
                        "DocumentType": document_type
                    }
                }

                response = requests.post("https://api.novaposhta.ua/v2.0/json/", json=data)

                if response.status_code == 200:
                    result = response.json()
                    waybill_list = result.get("data", [])

                    for waybill_data in waybill_list:
                        if frappe.db.exists('NovaPoshta Waybill', {'tracking_number': waybill_data.get("IntDocNumber")}):
                            continue

                        waybill_doc = frappe.new_doc("NovaPoshta Waybill")
                        waybill_doc.update({
                            "tracking_number": waybill_data.get("IntDocNumber"),
                            "senders_name": waybill_data.get("SenderContactPerson"),
                            "senders_address": waybill_data.get("SenderAddressDescription"),
                            "receivers_name": waybill_data.get("RecipientContactPerson"),
                            "receivers_address": waybill_data.get("RecipientAddressDescription"),
                            "item_description": waybill_data.get("Description"),
                            "quantity": waybill_data.get("CargoType"),
                            "weight": waybill_data.get("Weight"),
                            "redelivery_option": waybill_data.get("ServiceType"),
                            "amended_from": waybill_data.get("DocumentType"),
                            "payment_control": waybill_data.get("AfterpaymentOnGoodsCost"),
                            "backward_delivery": waybill_data.get("BackwardDeliveryMoney"),
                            "status_novaposhta": waybill_data.get("StateName")[:140],
                            "waybill_is_created": waybill_data.get("CreateTime"),
                            "waybill_was_closed": waybill_data.get("DateLastUpdatedStatus"),
                        })
                        waybill_doc.insert()
                        all_waybills.append(waybill_doc)  

        fetch_waybills("Order")
        
        fetch_waybills("OrderResponse")
        
        return all_waybills
        
    def update_waybills(self):
        api_key = get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key")
        self.get_waybill(api_key)
        schedule.every(1).minutes.do(lambda: self.get_waybill(api_key))
    
    @whitelist()
    def update_novaposhta_data(self):
        frappe.enqueue(
            self.update_novaposhta_data_background,
            queue='novaposhta_queue',
            job_name='NovaPoshta data update'
        )

    def update_novaposhta_data_background(self):
        self.get_areas()
        self.get_cities()
        self.get_warehouses()
        
    # def get_active_novaposhta():
    #     return frappe.db.get_value("NovaPoshta", "NovaPoshta", "enabled")    

    # def validate(self):
    #     if not NovaPoshta.get_active_novaposhta():
    #         frappe.throw(_("Please configure and activate NovaPoshta integration first"))   
            
    @whitelist()
    def search_settlements(self, city_name, limit=50, page=1):
        client = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        settlements = client.address.search_settlements(city_name=city_name, limit=limit, page=page)
        settlements_data = settlements.json().get('data', [])
        return settlements_data

    @whitelist()
    def search_settlement_streets(self, street_name, settlement_ref, limit=50):
        client = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        streets = client.address.search_settlement_streets(street_name=street_name, settlement_ref=settlement_ref, limit=limit)
        streets_data = streets.json().get('data', [])
        return streets_data
    
    @whitelist()
    def search_settlements_and_streets(self, city_name, street_name):
        settlements = self.search_settlements(city_name=city_name)
        streets = []
        if settlements:
            streets = self.search_settlement_streets(street_name=street_name, settlement_ref=settlements[0].get('Ref'))
        return {'settlements': settlements, 'streets': streets}
    
class NovaPoshtaUtils:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or get_decrypted_password(
            "NovaPoshta", "NovaPoshta", "api_key", raise_exception=False
        )
        self.enabled = frappe.db.get_value("NovaPoshta", "NovaPoshta", "enabled")
        self.api_endpoint = "https://api.novaposhta.ua/v2.0/json/"
        self.api = NovaPoshtaApi(api_key=get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key"))
        if not self.enabled:
            link = frappe.utils.get_link_to_form(
                "NovaPoshta", "NovaPoshta", frappe.bold("NovaPoshta")
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
            pack_count="1", # TODO 
        )
        
        data = delivery_price_data.get("data", [])
        print(delivery_price_data)

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
    
    def get_counterparty_addresses(self, ref, counterparty_property):
        body = {
            "apiKey": self.api_key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterpartyAddresses",
            "methodProperties": {
                "Ref": ref,
                "CounterpartyProperty": counterparty_property
            }
        }

        response = post(self.api_endpoint, json=body)
        
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            raise Exception(f"Failed to get counterparty addresses: {response.status_code}")
        
    def is_payment_control_available(self, city_ref):
        body = {
            "apiKey": self.api_key,
            "modelName": "InternetDocument",
            "calledMethod": "getDocumentDeliveryDate",
            "methodProperties": {
                "CitySender": city_ref
            }
        }
        response = post(self.api_endpoint, json=body)
        data = response.json()

        if data.get('success') and data.get('data'):
            return data.get('data')[0].get('AvailableService').get('isControlledBySender')

        return False    
    
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
        custom_delivery_payer=None,
        service_info='WarehouseWarehouse',
        sender_warehouseindex=None,
        recipient_warehouseindex=None,
        payment_method=None,
        sender_EDRPOU=None,
        backward_delivery_data=None
    ):
        if isinstance(shipment_parcel, str):
            try:
                shipment_parcel = json.loads(shipment_parcel)
            except json.JSONDecodeError as e:
                raise Exception("Invalid shipment_parcel JSON format") from e

        shipment_parcel = shipment_parcel[0]

        sender = self.get_sender_counterparty()
        pickup_counterparty_ref = sender['data'][0]['Ref']
        sender_EDRPOU = sender['data'][0].get('EDRPOU')
        sender_type = 'legal' if sender_EDRPOU else 'private'
        
        recipient = self.get_recipient_counterparty()
        delivery_counterparty_ref = recipient['data'][0]['Ref']
        recipient_EDRPOU = recipient['data'][0].get('EDRPOU')

        recipient_contacts = self.get_counterparty_contacts(delivery_counterparty_ref)
        sender_contact = self.get_counterparty_contacts(pickup_counterparty_ref)[0]
        sender_contact_ref = sender_contact['Ref']
        sender_contact_phone = sender_contact['Phones']
        first, last, middle = recipient_full_name.split(' ')

        recipient_contact = self.find_contact_by_full_name(
            contact_list=recipient_contacts,
            last_name=last,
            middle_name=middle,
            first_name=first,
            phone=recipient_phone
        )

        if not recipient_contact:
            recipient_contact = self.create_recipient_contact_person(
                last_name=last,
                middle_name=middle,
                first_name=first,
                email='',
                phone=recipient_phone
            )
            if not recipient_contact:
                print('Failed to create recipient contact')
                raise Exception("Failed to create recipient contact")
        recipient_contact_person_ref = recipient_contact["ContactPerson"]["data"][0]['Ref']
        recipient_contact_person_phone = recipient_contact.get("Phones", recipient_phone)

        print('Create waybill')
        print(shipment_parcel)

        length = shipment_parcel.get("length")
        width = shipment_parcel.get("width")
        height = shipment_parcel.get("height")
        VolumeGeneral = ((length / 100) * (width / 100) * (height / 100))

        
        afterpayment_on_goods_cost = None
        backward_delivery_data = None
        
        if payment_method and payment_method == "in_department":
            print(f'{sender_type=}')
            if sender_type == "legal":
                afterpayment_on_goods_cost = str(value_of_goods)
            else:
                backward_delivery_data = [{
                    "PayerType": "Recipient",
                    "CargoType": "Money",
                    "RedeliveryString": str(value_of_goods)
                }]
        elif payment_method == "card":
            
            afterpayment_on_goods_cost = None
            backward_delivery_data = None


        waybill = self.create_express_waybill(
            pickup_city_ref=pickup_city_ref,
            sender_ref=pickup_counterparty_ref,
            sender_address_ref=pickup_warehouse_ref,
            sender_contact_ref=sender_contact_ref,
            sender_contact_phone=sender_contact_phone,
            delivery_city_ref=delivery_city_ref,
            recipient_ref=delivery_counterparty_ref,
            recipient_address_ref=delivery_warehouse_ref,
            recipient_contact_ref=recipient_contact_person_ref,
            recipient_contact_phone=recipient_contact_person_phone,
            description_of_content=description_of_content,
            weight=shipment_parcel.get("weight"),
            volume_general=VolumeGeneral,
            value_of_goods=value_of_goods,
            sender_warehouseindex=sender_warehouseindex,
            recipient_warehouseindex=recipient_warehouseindex,
            width=width,
            length=length,
            height=height,
            afterpayment_on_goods_cost=afterpayment_on_goods_cost,
            backward_delivery_data=backward_delivery_data,
            intended_delivery_date=pickup_date,
            sender_EDRPOU=sender_EDRPOU,
            custom_delivery_payer=custom_delivery_payer,
            sender_type=sender_type,
            payment_method=payment_method  
        )
        
        pprint(waybill)
        print(waybill)

        waybill_ref = waybill['data'][0]['Ref']
        waybill_number = waybill['data'][0]['IntDocNumber']
        print(waybill_ref)
        print(waybill_number)
        

        if waybill_number:
            return {'waybill_number': waybill_number, 'waybill_ref': waybill_ref}
        raise Exception("Failed to create waybill")

    def get_sender_counterparty(self):
        return post(self.api_endpoint, json={
            "apiKey": self.api_key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterparties",
            "methodProperties": {
                "CounterpartyProperty": "Sender",
                "Page": "1"
            }
        }).json()

    def get_recipient_counterparty(self):
        return post(self.api_endpoint, json={
            "apiKey": self.api_key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterparties",
            "methodProperties": {
                "CounterpartyProperty": "Recipient",
                "Page": "1"
            }
        }).json()

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

    def create_express_waybill(
        self,
        pickup_city_ref,
        sender_ref,
        sender_address_ref,
        sender_contact_ref,
        sender_contact_phone,
        delivery_city_ref,
        recipient_ref,
        recipient_address_ref,
        recipient_contact_ref,
        recipient_contact_phone,
        description_of_content,
        weight,
        volume_general,
        value_of_goods,
        sender_warehouseindex=None,
        recipient_warehouseindex=None,
        width=None,
        length=None,
        height=None,
        backward_delivery_data=None,
        afterpayment_on_goods_cost=None,
        intended_delivery_date=None,
        sender_EDRPOU=None,
        custom_delivery_payer=None,
        sender_type='legal',
        payment_method=None
    ):
        method_properties = {
            "PayerType": custom_delivery_payer.capitalize(),
            "PaymentMethod": "Cash",
            "CargoType": "Cargo",
            "VolumeGeneral": str(volume_general),
            "Weight": str(weight),
            "ServiceType": "WarehouseWarehouse",
            "SeatsAmount": "1",
            "Description": description_of_content,
            "Cost": str(value_of_goods),
            "CitySender": pickup_city_ref,
            "Sender": sender_ref,  
            "SenderAddress": sender_address_ref,  
            "ContactSender": sender_contact_ref,  
            "SendersPhone": sender_contact_phone,  
            "CityRecipient": delivery_city_ref,
            "Recipient": recipient_ref,  
            "RecipientAddress": recipient_address_ref,  
            "ContactRecipient": recipient_contact_ref,  
            "RecipientsPhone": recipient_contact_phone,  
            "AfterpaymentOnGoodsCost": afterpayment_on_goods_cost, 
            "BackwardDeliveryData": backward_delivery_data,
            "OptionsSeat": [
                {
                    "volumetricVolume": str(volume_general),
                    "volumetricWidth": str(width),
                    "volumetricLength": str(length),
                    "volumetricHeight": str(height),
                    "weight": str(weight)
                }
            ],
        }
        pprint(method_properties)
        result = post(self.api_endpoint, json={
            "apiKey": self.api_key,
            "modelName": "InternetDocument",
            "calledMethod": "save",
            "methodProperties": method_properties
        }).json()

        return result
    
@frappe.whitelist()      
def get_label(waybill_number):
    api_key = get_decrypted_password("NovaPoshta", "NovaPoshta", "api_key")
    api_endpoint = 'https://my.novaposhta.ua/orders/printMarking100x100'
    html_print_url = f'{api_endpoint}/orders/printMarking100x100/orders[]/{waybill_number}/type/html/apiKey/{api_key}/zebra'
    response = requests.get(html_print_url)

    if response.status_code == 200:
        return response.content.decode('utf-8')
    else:
        response.raise_for_status()
        
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