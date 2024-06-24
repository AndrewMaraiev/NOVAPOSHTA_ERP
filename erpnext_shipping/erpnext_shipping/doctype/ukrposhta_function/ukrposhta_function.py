import logging
import requests
from frappe.model.document import Document

class UkrposhtaAPIController(Document):
    api_base_url = "https://dev.ukrposhta.ua/ecom/0.0.1/"

    def __init__(self, *args, **kwargs):
        super(UkrposhtaAPIController, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.configure_logger()
        self.access_token = '1206cee6-887a-3c8a-adb5-2ecd970597ce'  # Be cautious with sensitive information
  
    def configure_logger(self):
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)  # Adjust the log level as needed

    def create_shipment(self):
        self.logger.debug("Attempting to create a shipment...")
        url = f"{self.api_base_url}/shipments"
        data = {"sender_uuid": "your_sender_uuid"}
        response = requests.post(url, json=data, headers=self.get_headers())
        if response.status_code == 200:
            self.logger.info("Shipment created successfully.")
        else:
            self.logger.error(f"Failed to create shipment: {response.text}")

    def get_headers(self):
        self.logger.debug("Fetching headers for the request.")
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def update_shipment(self):
        self.logger.debug("Attempting to update a shipment...")
        # Update logic here

    def delete_shipment(self):
        self.logger.debug("Attempting to delete a shipment...")
        # Delete logic here

    def get_shipment(self):
        self.logger.debug("Attempting to retrieve shipment details...")
        # Retrieve logic here

# Example on how to use this class
def run_ukrposhta_operations():
    controller = UkrposhtaAPIController()
    controller.create_shipment()
    controller.update_shipment()
    controller.get_shipment()
    controller.delete_shipment()

# Assuming the above function would be called within the scope where it is appropriate
