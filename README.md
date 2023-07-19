## ERPNext Shipping

A Shipping Integration for ERPNext with various platforms. Platforms integrated in this app are:
- [Nova Poshta](https://novaposhta.ua/)
- [LetMeShip](https://www.letmeship.com/en/)
- [SendCloud](https://www.sendcloud.com/home-new/)

## Features
- Creation of shipment to a carrier service (e.g. FedEx, UPS) via LetMeShip, Nova Poshta, and SendCloud. 
- Compare shipping rates. 
- Printing the shipping label is also made available within the Shipment doctype.
- Templates for the parcel dimensions.
- Shipment tracking.


.1 Nova Poshta API
To use the delivery services of Nova Poshta, you first need to obtain an API key:

Register on the Nova Poshta website and obtain an API key.
In the ERPNext system, go to the integration settings.
Find the section for Nova Poshta API.
Insert the obtained API key into the "API Key" field.
Check the "Enabled" field and save the settings.
Now, after successful integration with Nova Poshta, you will be able to utilize their delivery services for comparing rates, generating labels, and tracking shipment statuses in the ERPNext system.

## Setup
For the compare shipping rates feature to work as expected, you need to generate an API key from your service provider. Service providers have their own specific doctypes similar to those from the `Integrations`. They can be enabled or disabled depending on your needs.

![LetMeShip 2020-08-05 09-54-28](https://user-images.githubusercontent.com/17470909/89377411-500c4f80-d724-11ea-8fe5-b11fec2a5c27.png)



### Fetch Shipping Rates
![core2](https://user-images.githubusercontent.com/17470909/89377460-70d4a500-d724-11ea-8550-a2813b936651.gif)

You can see the list of shipping rates by clicking the `Fetch Shipping Rates` button. Once you picked a rate, it will create the shipment for you. 

### Shipping Label
![71bcfc9d-9d66-4a58-8238-1eeab4e9a24f 2020-08-05 09-48-32](https://user-images.githubusercontent.com/17470909/89377478-78944980-d724-11ea-8120-a5374c6e4c5e.png)

The service provider will also provide the shipping label and to generate the label, click on the `Print Shipping Label` on top of the doctype.

-----------------------
#### License

MIT
