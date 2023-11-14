from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    custom_fields = {
        "Shipment": [
            # ... other custom fields ...

            dict(
                fieldname="section_break_bpdvz",
                fieldtype="Section Break",
                label="NovaPoshta specific",
                insert_after="update_tracking",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),

            dict(
                fieldname="pickup_city",
                label="Pickup city",
                fieldtype="Link",
                options="NovaPoshta cities",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="section_break_bpdvz",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),
            
            dict(
                fieldname="pickup_warehouse",
                label="Pickup Warehouse",
                fieldtype="Link",
                options="NovaPoshta Warehouse",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="pickup_city",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),
            
            dict(
                fieldname="sender_full_name",
                label="Sender full name",
                fieldtype="Data",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="pickup_warehouse",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),
            
            dict(
                fieldname="sender_phone",
                label="Sender phone",
                fieldtype="Data",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="sender_full_name",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),
            
            dict(
                fieldname="column_break_et3lj",
                fieldtype="Column Break",
                insert_after="sender_phone",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),

            dict(
                fieldname="delivery_to_city",
                label="Delivery to City",
                fieldtype="Link",
                options="NovaPoshta cities",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="column_break_et3lj",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),
            
            dict(
                fieldname="delivery_to_warehouse",
                label="Delivery to Warehouse",
                fieldtype="Link",
                options="NovaPoshta Warehouse",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="delivery_to_city",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),    
            
            dict(
                fieldname="recipient_full_name",
                label="Recipient full name",
                fieldtype="Data",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="delivery_to_warehouse",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),
            
            dict(
                fieldname="recipient_phone",
                label="Recipient phone",
                fieldtype="Data",
                depends_on="eval: doc.service_provider == 'NovaPoshta'",
                insert_after="recipient_full_name",
                mandatory_depends_on="eval: doc.service_provider == 'NovaPoshta'",
            ),
            
        ],
    }

    create_custom_fields(custom_fields)