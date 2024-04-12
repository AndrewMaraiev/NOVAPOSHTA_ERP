# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password
from erpnext_shipping.erpnext_shipping.utils import show_error_alert
from .ukrposhta_client import UkrposhtaApi  
from frappe import _ 



class Ukrposhta(Document):
    def validate(self):
        if not self.enabled:
            return

        # Assuming there's a method to validate Ukrposhta credentials
        if not self.validate_credentials():
            frappe.throw("Invalid Ukrposhta API credentials.")

    def validate_credentials(self):
        """Check if provided Ukrposhta credentials are valid."""
        client = self.get_client()
        # Assuming there's a simple endpoint that can validate the token without making any changes
        return client.validate_credentials()

    def get_client(self):
        """Initialize and return a Ukrposhta API client."""
        api_key = get_decrypted_password('Ukrposhta', self.name, 'api_key', raise_exception=False)
        return UkrposhtaApi(api_key)

    def create_address(self, data):
        """Create a new address in Ukrposhta."""
        client = self.get_client()
        response = client.model_address_post(data)
        return response

    def create_client(self, data):
        """Create a new client in Ukrposhta."""
        client = self.get_client()
        response = client.model_clients_post(data)
        return response

    def create_shipment(self, data):
        """Create a new shipment in Ukrposhta."""
        client = self.get_client()
        response = client.model_shipments_post(data)
        return response

    def get_label(self, shipment_id):
        """Retrieve shipping label for a given shipment ID from Ukrposhta."""
        client = self.get_client()
        response = client.model_print(shipment_id)
        if response:
            # Assuming the response content is the direct label or a URL to the label
            return response
        else:
            frappe.throw("Failed to retrieve label.")

    def track_shipment(self, barcode):
        """Track a shipment using its barcode."""
        client = self.get_client()
        response = client.model_statuses(barcode)
        if response:
            # Assuming the response contains tracking information
            return response
        else:
            frappe.throw("Failed to track shipment.")

class UkrposhtaUtils():
	def __init__(self):
		self.api_key = get_decrypted_password('Ukrposhta', 'Ukrposhta', 'api_key', raise_exception=False)
		self.enabled = frappe.db.get_single_value('Ukrposhta', 'enabled')

		if not self.enabled:
			link = frappe.utils.get_link_to_form('Ukrposhta', 'Ukrposhta', frappe.bold('Ukrposhta Settings'))
			frappe.throw(_('Please enable Ukrposhta Integration in {0}'.format(link)), title=_('Mandatory'))

	