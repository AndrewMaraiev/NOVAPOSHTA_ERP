## ERPNext Shipping

A Shipping Integration for ERPNext with various platforms. Platforms integrated in this app are:
- [Nova Poshta](https://novaposhta.ua/)
- [LetMeShip](https://www.letmeship.com/en/)
- [SendCloud](https://www.sendcloud.com/home-new/)

## Features

- **Shipment Creation**: Easily create shipments to carrier services like Nova Poshta, LetMeShip, and SendCloud.

- **Fetch shipping rates**: Compare shipping rates from different carriers and service providers to make informed shipping decisions.

- **Label Printing**: Generate shipping labels directly from the ERPNext system, ensuring accurate and professional label generation.

- **Parcel Templates**: Define parcel dimensions templates to simplify and streamline the shipment creation process.

- **Shipment Tracking**: Keep track of the status of your shipments in real-time using the integrated tracking functionality.


## Setup
To install the ERPNext shipping module with Nova Poshta integration, follow these steps:

- Download the ERPNext shipping module from GitHub:
Open your terminal and navigate to the bench directory:

cd /path/to/bench/directory

- Download the module using the bench get-app command:

bench get-app https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP.git

- Install the ERPNext shipping module on your site:
Navigate to the bench directory if you're not already there:

cd /path/to/bench/directory

- Install the module on your site using the following command, replacing [site_name] with the name of your site:

bench --site [site_name] install-app erpnext_shipping

- Start the server:
After installing the module, restart the server so that the changes take effect. Use the following command to start the server:

bench start

This will start the ERPNext development server.


Verify the functionality of the new module:
- Open a web browser and navigate to the address where your ERPNext site is running, typically at http://localhost:8000. Ensure that the new shipping module is displayed and working correctly.
Configure the shipping module:
Some modules require additional configuration steps to work properly. Refer to the documentation provided for the module and follow any configuration instructions specified there.
- Review the documentation:
Typically, every module and framework comes with documentation that provides information about how to use the new module, its features, and settings. Make sure you have reviewed the documentation to utilize the new module effectively.


## How to use

![Nova Poshta Logo](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/np_logo.png)
.1 Nova Poshta API
To use the delivery services of Nova Poshta, you first need to obtain an API key:

Register on the Nova Poshta website and obtain an API key.
![Nova Poshta site](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/novaposhta.png)
![Nova Poshta site](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/np%20api.png)

In the ERPNext system, go to the integration settings.
Find the section for Nova Poshta API.
Insert the obtained API key into the "API Key" field.
Check the "Enabled" field and save the settings.
 ![Nova Poshta site](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/erp%20np%20api.png)
Now, after successful integration with Nova Poshta, you will be able to utilize their delivery services for comparing rates, generating labels, and tracking shipment statuses in the ERPNext system.


## Usage

- **Compare Shipping Rates**:
  Click the "Fetch Shipping Rates" button to view a list of shipping rates. Once you select a rate, the system will create the shipment for you.
  ![Fetch shipping rates](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/fetch%20shipping%20rates.png)

- **Shipping Label Generation**:
  Access the shipping label by clicking the "Print Shipping Label" button at the top of the doctype. The label is provided by the selected service provider.
  ![Print label](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/print%20shipping%20label.png)
  ![Print label](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/label%20'zebra'.png)

- **Tracking status**:
  Click the "Update Tracking" button to view ` tracking status of shipment.

  ![Tracking status](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/status.png)
  ![Tracking status](https://github.com/AndrewMaraiev/NOVAPOSHTA_ERP/blob/main/images/status%20done.png)
  
## License

This project is licensed under the MIT License.

## How to Contribute

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository and create a new branch for your feature or bug fix.
2. Make your changes and test thoroughly.
3. Create a pull request to merge your changes into the main repository.

We appreciate your efforts in improving NOVAPOSHTA_ERP!

## Credits

This integration is developed and maintained by [iKrok](https://github.com/ikrokdev). We thank the contributors([Vladykart](https://github.com/Vladykart) and [NazikXY](https://github.com/NazikXY)) and the community for their valuable input.

For support or inquiries, please contact support@example.com.

