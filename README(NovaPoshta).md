# NOVAPOSHTA_ERP - Nova Poshta Shipping Integration for ERPNext

NOVAPOSHTA_ERP is a comprehensive shipping integration for ERPNext that enables seamless logistics and shipping operations using the Nova Poshta shipping service. This integration provides features such as shipment creation, rate comparison, label generation, shipment tracking, and warehouse management. The integration supports multiple platforms, including Nova Poshta, LetMeShip, and SendCloud.

![Nova Poshta Logo](https://user-images.githubusercontent.com/17470909/89377411-500c4f80-d724-11ea-8fe5-b11fec2a5c27.png)

## Features

- **Shipment Creation**: Easily create shipments to carrier services like FedEx, UPS, and more via Nova Poshta, LetMeShip, and SendCloud.

- **Rate Comparison**: Compare shipping rates from different carriers and service providers to make informed shipping decisions.

- **Label Printing**: Generate shipping labels directly from the ERPNext system, ensuring accurate and professional label generation.

- **Parcel Templates**: Define parcel dimensions templates to simplify and streamline the shipment creation process.

- **Shipment Tracking**: Keep track of the status of your shipments in real-time using the integrated tracking functionality.

## Setup

1. **Nova Poshta API Integration**:
   To utilize Nova Poshta's delivery services, you need to set up the API integration:

   - Register on the Nova Poshta website and obtain an API key.
   - In ERPNext, go to the integration settings.
   - Locate the Nova Poshta API section.
   - Enter the obtained API key in the "API Key" field.
   - Enable the integration by checking the "Enabled" field and save the settings.

   Once integrated, you can use Nova Poshta's services for rate comparison, label generation, and shipment tracking within ERPNext.

2. **Service Provider API Keys**:
   For the rate comparison feature to work, generate API keys from your chosen service providers. Enable or disable specific doctypes similar to the "Integrations" section based on your needs.

## Usage

- **Compare Shipping Rates**:
  Click the "Fetch Shipping Rates" button to view a list of shipping rates. Once you select a rate, the system will create the shipment for you.

- **Shipping Label Generation**:
  Access the shipping label by clicking the "Print Shipping Label" button at the top of the doctype. The label is provided by the selected service provider.

## License

This project is licensed under the MIT License.

## How to Contribute

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository and create a new branch for your feature or bug fix.
2. Make your changes and test thoroughly.
3. Create a pull request to merge your changes into the main repository.

We appreciate your efforts in improving NOVAPOSHTA_ERP!

## Credits

This integration is developed and maintained by [Your Company Name]. We thank the contributors and the community for their valuable input.

For support or inquiries, please contact support@example.com.