# -*- coding: utf-8 -*-
from typing import List
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import re


RUC_URI = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}

class SunatChar:
    def __init__(self, label, value="") -> None:
        self.label = label
        self._value = value
        
    def __get__(self, instance, owner):
        return self._value
    
    def __set__(self, instance, new_value):
        self._value = new_value

    def __str__(self):
        return self._value


class SunatList:
    def __init__(self, label, values=[]):
        self.label = label
        self._values = values

    def __get__(self, instance, owner):
        return self._values
    
    def __set__(self, instance, new_values):
        self._values = new_values


class SunatLegalRepresentative:
    document_type = None
    num_doc = None
    name = None
    position = None
    date_from = None


class SunatRuc(object):
    company_name = SunatChar("Número de RUC:")
    taxpaper_type = SunatChar("Tipo Contribuyente:")
    trade_name = SunatChar("Nombre Comercial:")
    registration_date = SunatChar("Fecha de Inscripción:")
    start_date_activities = SunatChar("Fecha de Inicio de Actividades:")
    taxpaper_state = SunatChar("Estado del Contribuyente:")
    taxpaper_condition = SunatChar("Condición del Contribuyente:")
    tax_domicile = SunatChar("Domicilio Fiscal:")
    receipt_issuance_system = SunatChar("Sistema Emisión de Comprobante:")
    foreign_trade_activity = SunatChar("Actividad Comercio Exterior:")
    accounting_system = SunatChar("Sistema Contabilidad:")
    economic_activities = SunatChar("Actividad(es) Económica(s):")
    payment_receipts = SunatChar("Comprobantes de Pago c/aut. de impresión (F. 806 u 816):")
    electronic_issuance_system = SunatChar("Sistema de Emisión Electrónica:")
    electronic_issuer_since = SunatChar("Emisor electrónico desde:")
    electronic_receipts = SunatChar("Comprobantes Electrónicos:")
    ple_affiliate_since = SunatChar("Afiliado al PLE desde:")
    patters = SunatList("Padrones:")
    legal_representatives: List[SunatLegalRepresentative] = []
    annexed_premises = []
    
    def __init__(self, num_ruc: str):
        self.num_ruc = num_ruc
        self.session = requests.Session()
        
        response = self.session.get(RUC_URI, headers=HEADERS)
        
        if not response.ok:
            raise "Error al obtener datos del RUC"
        
        self.get_data_ruc()
        self.get_data_legal_reps()
    
    # STATIC METHODS
    @staticmethod
    def _get_date(date_str: str):
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # PRIVATE METHODS
    def _get_rnd_num(self):
        params = {
            'accion': 'consPorTipdoc',
            'nrodoc': '12345678',
            'search2': '12345678',
            'contexto': 'ti-it',
            'btnTipo': 2,
            'tipdoc': 1,
            'modo': 1,
        }

        response = self.session.post(RUC_URI, headers=HEADERS, params=params)
        
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
            input_num_rnd = soup.find('input', {'name': 'numRnd'})
            if input_num_rnd:
                return input_num_rnd.attrs['value']
    
    def _request_ruc(self):
        rnd_num = self._get_rnd_num()
        params = {
            'accion': 'consPorRuc',
            'nroRuc': self.num_ruc,
            'tipdoc': 1,
            'contexto': 'ti-it',
            'modo': 1,
            'numRnd': rnd_num,
        }
        response = self.session.post(RUC_URI, headers=HEADERS, params=params)
        return response.text if response.ok else ""
    
    def _request_legal_reps(self):
        params = {
            'accion': 'getRepLeg',
            'nroRuc': self.num_ruc,
            'desRuc': '',
        }

        response = self.session.post(RUC_URI, headers=HEADERS, params=params)
        return response.text if response.ok else ""
    
    # MAIN METHODS
    def get_data_ruc(self):
        html = self._request_ruc()
        soup = BeautifulSoup(html, 'html.parser')
        panel = soup.find('div', {'class': 'panel'})
        items = panel.select('.list-group-item')
        
        for item in items:
            row = item.find('div', {'class': 'row'})
            cols = row.find_all('div')
            
            label = None
            value = None
            
            for i_col, col in enumerate(cols):
                tag = col.find()
                if tag:
                    if i_col % 2 == 0:
                        label = tag.text.strip()
                    elif tag.name == 'table':
                        value = [" ".join(td.text.split()) for td in tag.find_all('td')]
                    else:
                        value = " ".join(tag.text.split())
                    
            if label and value:
                for attr_name, attr_value in vars(SunatRuc).items():
                    if isinstance(attr_value, SunatChar) and attr_value.label == label:
                        if attr_name == "company_name":
                            match = re.search(r"^.*?-(.*)", value)
                            if match:
                                name = match.group(1).strip()
                                self.__setattr__(attr_name, name)
                            self.__setattr__(attr_name, name.strip())
                        elif attr_name == "taxpaper_condition" and value == '-':
                            self.__setattr__(attr_name, "NO HABIDO")
                        else:
                            self.__setattr__(attr_name, value)
                    
                    elif isinstance(attr_value, SunatList) and attr_value.label == label:
                        self.__setattr__(attr_name, value)
    
    def get_data_legal_reps(self):
        html = self._request_legal_reps()
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'class': 'table'})
        if table:
            headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
            legals = []
            for row in table.find('tbody').find_all('tr'):
                vals = [td.get_text(strip=True) for td in row.find_all('td')]
                row_dict = dict(zip(headers, vals))
                
                legal_rep = SunatLegalRepresentative()
                legal_rep.document_type = row_dict["Documento"]
                legal_rep.num_doc = row_dict["Nro. Documento"]
                legal_rep.name = row_dict["Nombre"]
                legal_rep.position = row_dict["Cargo"]
                legal_rep.date_from = self._get_date(row_dict["Fecha Desde"])
                
                legals.append(legal_rep)
            
            self.legal_representatives = legals


if __name__ == "__main__":
    sunat_ruc = SunatRuc("20498100245")
    # sunat_ruc = SunatRuc("20538995364")
    
    print(sunat_ruc.legal_representatives)