import requests

class UkrposhtaApi:
    def __init__(self, bearer, token=False, throw_errors=False):
        self.bearer = bearer
        self.token = token
        self.throw_errors = throw_errors
        self.format = 'array'
        self.url = 'https://www.ukrposhta.ua/'
        self.api_version = '/0.0.1/'
        self.response_time = 30  # seconds

    def set_bearer(self, bearer):
        self.bearer = bearer
        return self

    def get_bearer(self):
        return self.bearer

    def set_token(self, token):
        self.token = token
        return self

    def get_token(self):
        return self.token

    def set_format(self, _format):
        self.format = _format
        return self

    def get_format(self):
        return self.format

    def set_response_time(self, response_time):
        if isinstance(response_time, (int, float)):
            self.response_time = response_time
        return self

    def get_response_time(self):
        return self.response_time

    def prepare(self, data):
        if self.format == 'array':
            return data.json() if isinstance(data, requests.Response) else data
        return data

    def request(self, model, method='GET', params=None, add=''):
        url = f"{self.url}ecom{self.api_version}{model}{add}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer}'
        }
        response = requests.request(method, url, json=params, headers=headers, timeout=self.response_time)

        if response.status_code != 200 and self.throw_errors:
            response.raise_for_status()

        return self.prepare(response)

    def request_token(self, model, method='GET', params=None, add='', file=False):
        url = f"{self.url}ecom{self.api_version}{model}{add}?token={self.token}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer}'
        }
        response = requests.request(method, url, json=params, headers=headers, timeout=self.response_time)

        if response.status_code != 200 and self.throw_errors:
            response.raise_for_status()

        return response.content if file else self.prepare(response)

    def request_token_put(self, model, params=None, add=''):
        return self.request_token(model, method='PUT', params=params, add=add)
    
    def model_address_get(self, _id):
        return self.request('addresses', 'GET', None, f'/{_id}')

    # Function to create address
    def model_address_post(self, data):
        return self.request('addresses', 'POST', data)

    # Function to create a new client
    def model_clients_post(self, data):
        return self.request_token('clients', 'POST', data)

    # Function to change data for an existing client
    def model_clients_put(self, _id, data):
        return self.request_token('clients', 'PUT', data, f'/{_id}')

    # Function to get created clients by external-id
    def model_clients_get(self, _id):
        return self.request_token('clients', 'GET', None, f'/external-id/{_id}')

    # Function to create a shipment
    def model_shipments_post(self, data):
        return self.request_token('shipments', 'POST', data)

    # Function to get a file for printing
    def model_print(self, _id):
        return self.request_token('shipments', 'GET', None, f'/{_id}/label', True)

    # Function to request for using smartbox
    def model_smart_box_post(self, smartbox_code, client_uuid):
        return self.request_token('smart-boxes', 'POST', None, f'/{smartbox_code}/use-with-sender/{client_uuid}')

    # Function to initialize smartbox shipment
    def model_smart_box_get(self, smartbox_code):
        return self.request_token('smart-boxes', 'GET', None, f'/{smartbox_code}/shipments/next')

    # Function to create a smartbox shipment
    def model_smart_box_put(self, smartbox_shipment_uuid, data):
        return self.request_token_put('shipments', data, f'/{smartbox_shipment_uuid}')

    # Function to get the last status of a barcode
    def model_statuses(self, barcode):
        return self.request_tracking('statuses/last', None, f'?barcode={barcode}')

    # Function to request tracking, similar to the request_token method but specific for tracking
    def request_tracking(self, model, params=None, add=''):
        return self.request_token(model, 'GET', params, add)