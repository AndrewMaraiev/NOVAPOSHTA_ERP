
        
def find_contact_by_full_name(
            contact_list: list[dict],
            last_name: str,
            middle_name: str,
            first_name: str,
            email: str,
            phone: str
        ) -> dict | None:
            for contact in contact_list:
                ln = contact.get('LastName', '') if contact.get('LastName', '') else '' 
                fn = contact.get('FirstName', '') if contact.get('FirstName', '') else ''
                mn = contact.get('MiddleName', '') if contact.get('MiddleName', '') else ''
                em = contact.get('Email', '') if contact.get('Email', '') else ''
                ph = contact.get('Phones', '') if contact.get('Phones', '') else ''
                
                if not ph.startswith('+'):
                    ph = '+' + ph
                
                full_name = ln + fn + mn + em + ph
                target_name = last_name + first_name + middle_name + email + phone
                
                if full_name != target_name:
                    continue
                return contact