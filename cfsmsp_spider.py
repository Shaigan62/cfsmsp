import re
import argparse
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

class CfsmspSpider:

    start_url = 'https://cfsmsp.impots.gouv.fr/secavis/'
    api_url = 'https://cfsmsp.impots.gouv.fr/secavis/faces/commun/index.jsf'

    def __init__(self, tax_no, reference_no):
        self.view_state = ''
        self.tax_no = tax_no
        self.reference_no = reference_no
        self.key_map = {
            'Nom': 'last_name',
            'Nom de naissance': 'birth_name',
            'Prénom(s)': 'first_name',
            'Date de naissance': 'date_of_birth',
            'Adresse déclarée': 'address',
            "Date de mise en recouvrement de l'avis d'impôt": 'date_of_collection_of_tax_notice',
            "Date d'établissement": 'date_of_establishment',
            'Nombre de part(s)': 'number_of_parts',
            'Situation de famille': 'family_status',
            'Nombre de personne(s) à charge': 'number_of_dependants',
            'Revenu brut global': 'total_gross_income',
            'Revenu imposable': 'taxable_income',
            'Impôt sur le revenu net avant corrections': 'net_income_tax_before_adjustments',
            "Montant de l'impôt": 'amount_of_the_tax',
            'Revenu fiscal de référence': 'reference_tax_income'
        }

        self.multiple_entry = ['last_name', 'birth_name', 'first_name', 'date_of_birth']

    def start_request(self):
        self.view_state = self.get_viewstate()
        try:
            return self.parse_info()
        except Exception:
            return {'tax_number': self.tax_no, 'reference_number': self.reference_no, 'error': 'record not found'}

    
    def record_request(self):
        payload = f"j_id_7%3Aspi={self.tax_no}&j_id_7%3Anum_facture={self.reference_no}&j_id_7%3Aj_id_l=Valider&j_id_7_SUBMIT=1&javax.faces.ViewState={self.view_state}"
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = requests.request("POST", self.api_url, headers=headers, data=payload)

        return response

    def parse_info(self):
        response = self.record_request()
        soup = BeautifulSoup(response.text, 'html.parser')
        attr = {'tax_number': self.tax_no, 'reference_number': self.reference_no}
        for row in soup.select('table tbody tr')[1:]:
            key = self.get_key(row.select_one('td').text)
            value = self.get_value(row.select('td')[1:], key)

            if not key:
                attr[last_key] = self.clean(f'{attr[last_key]} {value}')
                continue

            attr[key] = value
            last_key = key


        return self.post_process(attr)

    def post_process(self, record):
        address = record['address']
        record['country'] = 'France'
        record['zipcode'] = next(iter(re.findall('\d{5}', address)), '')
        record['city'] = next(iter(re.findall(f'{record["zipcode"]}\s(.*?)$', address)), '') if record['zipcode'] else ''

        return record

    def get_key(self, raw_key):
        raw_key = self.clean(raw_key)
        key = self.key_map.get(raw_key, '')

        if key:
            return key

        key = next(iter([value for key, value in self.key_map.items() if key in raw_key]), '')

        return key


    def get_value(self, elements, key):
        if key not in self.multiple_entry:
            return self.clean(''.join([x.text for x in elements]))

        values = {}
        for ind, col in enumerate(elements, start=1):
            values[f'Declarant_{ind}'] = self.clean(col.text)

        return values

    def get_viewstate(self):
        response = requests.get(self.start_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        raw_viewstate = soup.select_one('[name="javax.faces.ViewState"]').get('value')
        return quote(raw_viewstate)
    
    def clean(self, raw_text):
        return str(raw_text).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-tax_no", help="Enter Tax Number")
    parser.add_argument("-refer_no", help="Enter Reference Number")
    args = parser.parse_args()
    cfsmsp_crawler = CfsmspSpider(args.tax_no, args.refer_no)
    cfsmsp_crawler.start_request()


if __name__ == '__main__':
    main()
