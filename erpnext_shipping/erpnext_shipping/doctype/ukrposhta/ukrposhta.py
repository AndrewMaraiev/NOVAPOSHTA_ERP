# -*- coding: utf-8 -*-
import frappe
import requests
import json
import base64
from frappe import _
from frappe.model.document import Document
from requests.exceptions import RequestException
from decimal import Decimal
from frappe.utils.password import get_decrypted_password
from frappe.utils import flt
from pprint import pprint

UKRPOSHTA_PROVIDER = 'Ukrposhta'

class Ukrposhta(Document):
    api_endpoint = "https://www.ukrposhta.ua"

    def make_request(self, method, endpoint, params=None, data=None):
        bearer_token = self.get_password("sand_bearer_token")
        headers = {
            # "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json"
        }

        url = f"{self.api_endpoint}/{endpoint.strip('/')}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
        except RequestException as e:
            error_msg = f"Error during {method} at {url}: {str(e)}"
            frappe.log_error(error_msg, 'Ukrposhta API Error')
            raise

    @frappe.whitelist()
    def fetch_and_save_regions(self):
        params = None
        regions_response = self.make_request('GET', 'address-classifier-ws/get_regions_by_region_ua', params=params if params else None)

        for region in regions_response.get('Entries', {}).get('Entry', []):
            if not frappe.db.exists('Ukrposhta Regions', {'custom_region_id': region['REGION_ID']}):
                doc = frappe.get_doc({
                    'doctype': 'Ukrposhta Regions',
                    'region_id': region['REGION_ID'],
                    'region_name': region['REGION_UA']
                })
                doc.insert(ignore_permissions=True)
                doc.save()
                
        frappe.msgprint(_("Завантаження списку областей пройшло успішно"))

    @frappe.whitelist()
    def fetch_and_save_districts(self, region_id=None, district_ua=None):
        params = {
            'region_id': region_id,
            'district_ua': district_ua
        }
        params = {k: v for k, v in params.items() if v is not None}

        districts_response = self.make_request('GET', 'address-classifier-ws/get_districts_by_region_id_and_district_ua', params=params)
        districts_json = frappe.as_json(districts_response.get('Entries', {}).get('Entry', []))

        for district in districts_response.get('Entries', {}).get('Entry', []):
            district_id = district.get('DISTRICT_ID')
            district_ua = district.get('DISTRICT_UA')
            region_id = district.get('REGION_ID')

            if district_id and region_id and not frappe.db.exists('Ukrposhta Districts', {'district_id': district_id}):
                doc = frappe.get_doc({
                    'doctype': 'Ukrposhta Districts',
                    'district_id': district_id,
                    'name1': district_ua,
                    'region_id': region_id,
                    'json_data': districts_json
                })
                doc.insert(ignore_permissions=True)
                doc.save()

        frappe.msgprint(_("Завантаження списку районів пройшло успішно"))

    @frappe.whitelist()
    def fetch_and_save_cities(self, region_id=None, district_id=None, city_ua=None):
        limit = 500
        offset = 0
        params = {
            'region_id': region_id,
            'district_id': district_id,
            'city_ua': city_ua
        }
        params = {k: v for k, v in params.items() if v is not None}

        cities_response = self.make_request('GET', 'address-classifier-ws/get_city_by_region_id_and_district_id_and_city_ua', params=params)
        cities_json = frappe.as_json(cities_response.get('Entries', {}).get('Entry', []))

        for city in cities_response.get('Entries', {}).get('Entry', []):
            region_id = city.get('REGION_ID')
            district_id = city.get('DISTRICT_ID')
            city_ua = city.get('CITY_UA')
            koatuu = city.get('KOATUU')
            katottg = city.get('KATOTTG')

            if region_id and district_id and city_ua and not frappe.db.exists('Ukrposhta Cities', {'region_id': region_id, 'district_id': district_id, 'city_name': city_ua}):
                doc = frappe.get_doc({
                    'doctype': 'Ukrposhta Cities',
                    'region_id': region_id,
                    'district_id': district_id,
                    'city_name': city_ua,
                    'koatuu': koatuu,
                    'katottg': katottg,
                    'json_data': cities_json
                })
                doc.insert(ignore_permissions=True)
                doc.save()
            
            offset += limit
            
        frappe.msgprint(_("Завантаження списку міст пройшло успішно"))

    @frappe.whitelist()
    def fetch_and_save_streets(self):
        all_cities = frappe.get_all('Ukrposhta Cities', fields=['city_ua', 'district_id', 'region_id', 'koatuu', 'katottg'])

        if not all_cities:
            frappe.throw(_("Please provide at least one parameter to search for streets"))

        for city in all_cities:
            region_id = city.get('region_id')
            district_id = city.get('district_id')
            city_name = city.get('city_ua')
            
            params = {}
            if region_id:
                params['region_id'] = region_id
            if district_id:
                params['district_id'] = district_id
            if city_name:
                params['city_id'] = city_name
            
            if not params:
                continue

            try:
                street_response = self.make_request('GET', 'address-classifier-ws/get_street_by_region_id_and_district_id_and_city_id_and_street_ua', params=params)
                streets_json = street_response.get('Entries', {}).get('Entry', [])

                for street in streets_json:
                    street_id = street.get('STREET_ID')
                    street_name = street.get('STREET_UA')

                    if street_id and not frappe.db.exists('Ukrposhta Streets', {'street_id': street_id}):
                        doc = frappe.get_doc({
                            'doctype': 'Ukrposhta Streets',
                            'street_id': street_id,
                            'region_id': region_id,
                            'district_id': district_id,
                            'city_id': city_name,
                            'street_name': street_name,
                            'json_data': frappe.as_json(street)
                        })
                        doc.insert(ignore_permissions=True)
                        doc.save()

            except Exception as e:
                error_msg = str(e)
                if len(error_msg) > 140:
                    error_msg = error_msg[:137] + "..."
                frappe.log_error(error_msg, 'Ukrposhta API Error')

        frappe.msgprint(_("Successfully fetched street data."))

    @frappe.whitelist()
    def fetch_and_save_warehouses(self, city_id=None, district_id=None, region_id=None):
        params = {
            'city_id': city_id,
            'district_id': district_id,
            'region_id': region_id
        }

        params = {k: v for k, v in params.items() if v is not None}

        try:
            warehouse_response = self.make_request('GET', 'address-classifier-ws/get_postoffices_by_city_id', params=params)
            warehouses_json = warehouse_response.get('Entries', {}).get('Entry', [])

            for warehouse in warehouses_json:
                if not frappe.db.exists('Ukrposhta Warehouses', {'id': warehouse['ID']}):
                    doc = frappe.get_doc({
                        'doctype': 'Ukrposhta Warehouses',
                        'warehouse_id': warehouse['ID'],
                        'region_id': warehouse['REGION_ID'],
                        'district_id': warehouse.get('DISTRICT_ID'),
                        'city_id': warehouse.get('CITY_ID'),
                        'pi': warehouse['POSTINDEX'],
                        'address': warehouse['ADDRESS'],
                    })
                    doc.insert(ignore_permissions=True)
                    doc.save()

            frappe.msgprint(_("Завантаження списку відділень пройшло успішно"))
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 140:
                error_msg = error_msg[:137] + "..."
            frappe.log_error(error_msg, 'Ukrposhta API Error')
            frappe.throw(_("Error fetching warehouses: ") + error_msg)

class UkrposhtaUtils:
    def __init__(self):
        self.api_endpoint = 'https://www.ukrposhta.ua/ecom/0.0.1'
        self.api_key = get_decrypted_password("Ukrposhta", "Ukrposhta", "sand_bearer_token", raise_exception=True)
        self.sand_counterparty_token = get_decrypted_password("Ukrposhta", "Ukrposhta", "sand_counterparty_token", raise_exception=True)
        self.form_url = "https://www.ukrposhta.ua/forms/ecom/0.0.1"
        print('UTILS #1')

    def make_request(self, method, endpoint, params=None, data=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        url = f"{self.api_endpoint}/{endpoint.strip('/')}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
        except RequestException as e:
            error_msg = f"Error during {method} at {url}: {str(e)}"
            if len(error_msg) > 140:
                error_msg = error_msg[:137] + '...'
            frappe.log_error(error_msg, 'Ukrposhta API Error')
            raise

    def get_available_services(self, shipment_doc, value_of_goods, sender_postcode, recipient_postcode, shipment_parcel: dict):
        try:
            if isinstance(shipment_doc, str):
                shipment_doc = json.loads(shipment_doc)

            custom_sender_mobile_phone = shipment_doc.get('custom_sender_mobile_phone')
            custom_recipient_mobile_phone = shipment_doc.get('custom_recipient_mobile_phone')

            if not custom_sender_mobile_phone:
                frappe.throw(_('Missing sender phone number'))
            if not custom_recipient_mobile_phone:
                frappe.throw(_('Missing recipient phone number'))

            sender_data = self.get_or_create_counterparty(custom_sender_mobile_phone, shipment_doc, "sender")
            recipient_data = self.get_or_create_counterparty(custom_recipient_mobile_phone, shipment_doc, "recipient")

            # pprint(sender_data)
            # pprint(recipient_data)

            sender_postcode = shipment_doc.get('custom_pickup_postcode')
            recipient_postcode = shipment_doc.get('custom_delivery_posctode')

            weight = shipment_parcel[0].get("weight")
            length = shipment_parcel[0].get("length")
            width = shipment_parcel[0].get("width")
            height = shipment_parcel[0].get("height")

            delivery_price_data = self.calculate_delivery_price(
                sender_postcode=sender_postcode,
                recipient_postcode=recipient_postcode,
                weight=weight,
                length=length,
                declared_price=value_of_goods,
            )
            print(delivery_price_data)
            service_data = frappe._dict()
            service_data.service_provider = 'Ukrposhta'
            service_data.carrier = 'Ukrposhta'
            service_data.carrier_name = "Ukrposhta"
            service_data.service_name = "W2W"
            service_data.currency = 'UAH'
            service_data.Price = delivery_price_data['rawDeliveryPrice']

            print(f"{service_data:}")
            return [service_data]

        except json.JSONDecodeError:
            frappe.log_error("Error parsing JSON data for shipment_doc", "Ukrposhta API Error")
            raise ValueError("Invalid JSON format for shipment_doc")
        except Exception as e:
            frappe.log_error(str(e)[:139], "Ukrposhta API Error")
            raise

    def calculate_delivery_price(self, sender_postcode, recipient_postcode, weight, length, declared_price):
        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        body = {
            "addressFrom": {"postcode": sender_postcode},
            "addressTo": {"postcode": recipient_postcode},
            "type": "EXPRESS",
            "deliveryType": "W2W",
            "weight": weight,
            "length": length,
            "declaredPrice": declared_price,
            "postPay": declared_price,
            # "discounts": [{"description": "Discount 20%", "rate": 20}],
            "sms": True,
            "documentBack": True,
            "documentBackDeliveryType": "D2D"
        }
        print(body)
        response = requests.post(f"{self.api_endpoint}/domestic/delivery-price", headers=headers, json=body)
        print(response.text)
        response.raise_for_status()
        pprint(response.json())
        return response.json()

    def get_ukrposhta_shipping_rates(self, args):
        shipment_parcel_data = args.get('shipment_parcel')

        if isinstance(shipment_parcel_data, str):
            shipment_parcel_data = json.loads(shipment_parcel_data)

        if isinstance(shipment_parcel_data, list):
            shipment_parcel_data = shipment_parcel_data[0]

        if not shipment_parcel_data:
            frappe.throw(_('Shipment Parcel data not found'))

        shipping_rates = self.get_available_services(
            args.get('shipment_doc'),
            args.get('value_of_goods'),
            shipment_parcel_data
        )

        return shipping_rates

    def get_counterparty_by_phone(self, phone_number):
        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        endpoint = "clients/phone"
        params = {
            "token": self.sand_counterparty_token,
            "countryISO3166": "UA",
            "phoneNumber": phone_number
        }

        try:
            print(f"Making GET request to {endpoint} with params: {params}")
            response = requests.get(f"{self.api_endpoint}/{endpoint.strip('/')}", headers=headers, params=params)
            response.raise_for_status()
            response_json = response.json()
            pprint(response_json)
            return response_json
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            error_msg = f"Error during GET request: {str(e)}"
            if len(error_msg) > 140:
                error_msg = error_msg[:137] + '...'
            print(error_msg)
            frappe.log_error(error_msg, 'Ukrposhta API Error')
            raise

    def create_client(self, shipment_doc, counterparty_type):

        delivery_contact_doc = frappe.get_doc("Contact", {"name": shipment_doc.get('delivery_contact_name')})
        addressId = self.fetch_address_object_by_raw_params(
                region_id=shipment_doc.get(f"custom_{counterparty_type}_region"),
                district_id=0,
                city_id=0,
                street='',
                street_number=0
            )
        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        endpoint = "clients"
        params = {"token": self.sand_counterparty_token}
        data = {
                "firstName": delivery_contact_doc.first_name,
                "middleName": delivery_contact_doc.middle_name,
                "lastName": delivery_contact_doc.last_name,
                "addressId": addressId,
                "phoneNumber": shipment_doc.get('recipient_phone'),
                "type": "INDIVIDUAL",
                "resident": True
            }
        

        try:
            response = requests.post(f"{self.api_endpoint}/{endpoint.strip('/')}", headers=headers, json=data, params=params)

            
            response.raise_for_status()
            
            return response.json()
        except RequestException as e:
            error_msg = f"Error creating client: {str(e)}"
            if len(error_msg) > 140:
                error_msg = error_msg[:137] + '...'
            frappe.log_error(error_msg, 'Ukrposhta API Error')
            raise frappe.ValidationError(_("Failed to create client: ") + error_msg)
        
    def fetch_address_object_by_raw_params(self, region_id, district_id, city_id, street, street_number):
        
        return 6617157

    def get_or_create_counterparty(self, phone_number, shipment_doc, counterparty_type):
        try:
            counterparty_data = self.get_counterparty_by_phone(phone_number)
            if counterparty_data:
                return counterparty_data
            
            counterparty_data = self.create_client(shipment_doc, counterparty_type=counterparty_type)
            pprint(counterparty_data)
            return counterparty_data
        except RequestException as e:
            frappe.log_error(f"Error in get_or_create_counterparty: {str(e)}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("Failed to get or create counterparty: ") + str(e))

    def create_shipment(self, shipment_doc):
        try:
            sender = self.get_or_create_counterparty(
                phone_number=shipment_doc['custom_sender_mobile_phone'], 
                shipment_doc=shipment_doc, 
                counterparty_type='sender'
            )
            recipient = self.get_or_create_counterparty(
                phone_number=shipment_doc['custom_recipient_mobile_phone'], 
                shipment_doc=shipment_doc, 
                counterparty_type='recipient'
            )

            shipment_parcel = shipment_doc['shipment_parcel'][0]
            
            data = {
                "type": "EXPRESS",
                "sender": {"uuid": sender[0].get('uuid')},
                "recipient": {"uuid": recipient[0].get('uuid')},
                "deliveryType": "W2W",
                "parcels": [{
                    "weight": shipment_parcel['weight'],
                    "length": shipment_parcel['length'],
                    "declaredPrice": shipment_doc['value_of_goods']
                }],
                "postPay": 0,
                "paidByRecipient": False,
                "postPayPaidByRecipient": True,
                "description": shipment_doc['description'],
                "fragile": True,
                "sms": False,
                "checkOnDelivery": False
            }
            
            headers = {
                "Content-type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }
            
            print("Request data:", json.dumps(data, indent=4, ensure_ascii=False))
            
            url = f"{self.api_endpoint}/shipments"
            response = requests.post(url, headers=headers, json=data, params={"token": self.sand_counterparty_token})

            print("Response status code:", response.status_code)
            print("Response text:", response.text)
            
            response.raise_for_status()
            response_data = response.json()
            
            if 'parcels' not in response_data or not response_data['parcels']:
                raise KeyError("Response from create_shipment is missing 'parcels' or 'parcels' is empty")

            parcels = response_data['parcels'][0]
            parcel_barcode = parcels.get('barcode')
            parcel_uuid = parcels.get('uuid')
            print(parcel_uuid)
            print(parcel_barcode)
            
            waybill_doc = frappe.get_doc({
                "doctype": "Ukrposhta Waybill",
                "uuid": parcel_uuid,
                "barcode": parcel_barcode,
                "sender": sender[0].get('uuid'),
                "recipient": recipient[0].get('uuid'),
                "description": shipment_doc['description'],
                "parcels": json.dumps(data['parcels']),
                "deliveryType": data['deliveryType'],
                "postPay": data['postPay'],
                "paidByRecipient": data['paidByRecipient'],
                "postPayPaidByRecipient": data['postPayPaidByRecipient'],
                "fragile": data['fragile'],
                "sms": data['sms'],
                "checkOnDelivery": data['checkOnDelivery']
            })
            waybill_doc.insert()
            waybill_doc.save()
            
            return response_data
        except KeyError as key_err:
            frappe.log_error(f"Key error: {key_err}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("Key error occurred: ") + str(key_err))
        except requests.exceptions.HTTPError as http_err:
            frappe.log_error(f"HTTP error occurred: {http_err}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("HTTP error occurred: ") + str(http_err))
        except requests.exceptions.RequestException as req_err:
            frappe.log_error(f"Request error occurred: {req_err}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("Request error occurred: ") + str(req_err))
        except Exception as err:
            frappe.log_error(f"An error occurred: {err}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("An error occurred: ") + str(err))

        
    def create_ukrposhta_waybill(self, parcels):
        try:
            sender_data = self.get_or_create_counterparty("sender_phone_number", {}, "sender")
            recipient_data = self.get_or_create_counterparty("recipient_phone_number", {}, "recipient")

            data = {
                "type": "EXPRESS",
                "sender": {"uuid": sender_data[0].get('uuid')},
                "recipient": {"uuid": recipient_data[0].get('uuid')},
                "deliveryType": "W2W",
                "parcels": parcels,  
                "postPay": 0,
                "paidByRecipient": False,
                "postPayPaidByRecipient": True,
                "description": "Тестова накладна",
                "fragile": True,
                "sms": False,
                "checkOnDelivery": False
            }
            
            headers = {
                "Content-type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }
            # url = "https://www.ukrposhta.ua/ecom/0.0.1/shipments"
            url = f"{self.api_endpoint}/shipments"
            response = requests.post(url, headers=headers, json=data, params={"token": self.sand_counterparty_token})
            response.raise_for_status()
            waybill_response = response.json()
            print(waybill_response)
            
            if not waybill_response.get('data'):
                raise KeyError("No 'data' key found in the response")

            waybill_data = waybill_response['data'][0]
            if 'uuid' not in waybill_data or 'barcode' not in waybill_data:
                raise KeyError("Response from create_ukrposhta_waybill is missing 'uuid' or 'barcode'")

            waybill_doc = frappe.get_doc({
                "doctype": "Ukrposhta Waybill",
                "uuid": waybill_data['uuid'],
                "barcode": waybill_data['barcode'],
                "sender": sender_data[0].get('uuid'),
                "recipient": recipient_data[0].get('uuid'),
                "description": "Тестова накладна",
                "parcels": parcels,
                "deliveryType": "W2W",
                "postPay": 0,
                "paidByRecipient": False,
                "postPayPaidByRecipient": True,
                "fragile": True,
                "sms": False,
                "checkOnDelivery": False
            })
            waybill_doc.insert()
            waybill_doc.save()

            return waybill_data
        except requests.exceptions.HTTPError as http_err:
            frappe.log_error(f"HTTP error occurred: {http_err}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("HTTP error occurred: ") + str(http_err))
        except requests.exceptions.RequestException as req_err:
            frappe.log_error(f"Request error occurred: {req_err}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("Request error occurred: ") + str(req_err))
        except Exception as err:
            frappe.log_error(f"An error occurred: {err}", 'Ukrposhta API Error')
            raise frappe.ValidationError(_("An error occurred: ") + str(err))
        
@frappe.whitelist()
def print_label(barcode):
    api_key = get_decrypted_password("Ukrposhta", "Ukrposhta", "sand_bearer_token", raise_exception=True)
    counterparty_key = get_decrypted_password("Ukrposhta", "Ukrposhta", "sand_counterparty_token", raise_exception=True)
    form_url = "https://www.ukrposhta.ua/forms/ecom/0.0.1"

    url = f"{form_url}/shipments/{barcode}/sticker?token={counterparty_key}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    pdf_content = base64.b64encode(response.content).decode('utf-8')
    return pdf_content

    
@frappe.whitelist()
def waybill_tracking(barcode):
    try:
        api_key = get_decrypted_password("Ukrposhta", "Ukrposhta", "prodaction_bearer_status_tracking")
        
        endpoint = "statuses/last"
        url = f"https://www.ukrposhta.ua/status-tracking/0.0.1/{endpoint}?barcode={barcode}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
       
        
        json_response = response.json()
        text=f"""
        Barcode: {json_response.get('barcode')}
        Date: {json_response.get('date')}
        Name: {json_response.get('name')}
        EventName: {json_response.get('eventName')}
        EventReason: {json_response.get('eventReason')} 
        """
        formatted_response = json.dumps(json_response, indent=4, ensure_ascii=False)

        html_response = "<pre>" + text + "</pre>"
        
        return html_response
    
    except RequestException as e:
        frappe.throw(_("Error fetching tracking information: {0}").format(str(e)))
