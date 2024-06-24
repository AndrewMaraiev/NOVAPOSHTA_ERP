# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt
# import frappe
# import requests
# import json
# from frappe import _
# from frappe.model.document import Document
# from requests.exceptions import RequestException
# from decimal import Decimal
# from frappe.utils.password import get_decrypted_password

# class Ukrposhtatracking(Document):
#     pass
# @frappe.whitelist()
# def waybill_tracking(barcode):
#    try:
#        api_key = get_decrypted_password("Ukrposhta", "Ukrposhta", "production_bearer_status_tracking", raise_exception=True)
        
#        endpoint = "statuses"
#        url = f"https://www.ukrposhta.ua/status-tracking/0.0.1/{endpoint}?barcode={barcode}"
        
#        headers = {
#            "Content-Type": "application/json",
#            "Authorization": f"Bearer {api_key}",
#            "Accept": "application/json"
#        }

#        response = requests.get(url, headers=headers)
#        response.raise_for_status()
        
#        return response.json()
    
#    except RequestException as e:
#     frappe.throw(_("Error fetching tracking information: {0}").format(str(e)))
