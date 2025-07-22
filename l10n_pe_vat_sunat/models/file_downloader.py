import os
import requests
from odoo import models
from odoo.exceptions import ValidationError
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import re
import zipfile


class FileDownloader(models.Model):
    _name = 'file.downloader'
    _description = 'Descarga y procesamiento de archivos de SUNAT'
    
    @staticmethod
    def download_file(url, save_path):
        """Descarga el archivo ZIP desde la URL y lo guarda en la ruta especificada."""
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as zip_file:
                zip_file.write(response.content)
            return True
        else:
            raise ValidationError("Error al descargar ZIP.")

    @staticmethod
    def extract_zip(zip_path, extract_to):
        """Extrae el contenido del ZIP en la ruta especificada."""
        if not zipfile.is_zipfile(zip_path):
            raise ValidationError(f"El archivo {zip_path} no es un archivo ZIP válido.")
        
        with zipfile.ZipFile(zip_path) as zip_ref:
            zip_ref.extractall(extract_to)
    
    @staticmethod
    def _get_date_from_remote(url: str):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            match = re.search(r'Actualizado al ?:? (\d{2}/\d{2}/\d{4})', soup.text)
            if match:
                try:
                    return datetime.strptime(match.group(1), '%d/%m/%Y')
                except:
                    return None
    
    @staticmethod
    def _get_date_file(file_path: str):
        if os.path.exists(file_path):
            timestamp = os.path.getctime(file_path)
            return datetime.fromtimestamp(timestamp)
    
    def goods_ready_for_update(self):
        url = "https://ww1.sunat.gob.pe/descarga/AgentRet/AgenRet0.html"
        update_date = self._get_date_from_remote(url)
        local_date = self._get_date_file('/tmp/BueCont_TXT.txt')
        if not self.env['good.contributor'].search_count([]) or not local_date or not update_date:
            return True
        return local_date < update_date
    
    def agents_ready_for_update(self):
        url = "https://ww1.sunat.gob.pe/descarga/BueCont/BueCont0.html"
        update_date = self._get_date_from_remote(url)
        local_date = self._get_date_file('/tmp/AgenRet_TXT.txt')
        if not self.env['agent.retention'].search_count([]) or not local_date or not update_date:
            return True
        return local_date < update_date
    
    # TODO: PASAR A UTILS_SYSTEM_OUTS
    @staticmethod
    def sync_model_with_df(model, df, unique_field, map_fields):
        """
        Sincroniza los registros de un modelo con los datos de un DataFrame.
        
        :param model: Nombre del modelo Odoo.
        :param df: DataFrame con los datos a sincronizar.
        :param unique_field: Campo único usado para identificar registros (por ejemplo, 'ruc').
        :param map_fields: Mapeo de campos del DataFrame a los campos del modelo.
        """
        
        def format_val(val):
            try:
                return datetime.strptime(val, "%d/%m/%Y")
            except:
                return val
        
        existing_records = model.search([])
        existing_dict = {getattr(rec, map_fields[unique_field]): rec for rec in existing_records}

        for _, row in df.iterrows():
            unique_value = str(row[unique_field])
            values = {model_field: format_val(row[df_field]) for df_field, model_field in map_fields.items()}

            if unique_value in existing_dict:
                record = existing_dict.pop(unique_value)
                if any(getattr(record, field) != value for field, value in values.items()):
                    record.write(values)
            else:
                model.create(values)
        
        for record in existing_dict.values():
            record.unlink()

    def update_agent_retention(self):
        """Actualiza el modelo de Agentes de Retención."""
        url = "https://ww1.sunat.gob.pe/descarga/AgentRet/AgenRet_TXT.zip"
        tmp_path = '/tmp'
        zip_path = os.path.join(tmp_path, 'AgentRet.zip')

        if self.download_file(url, zip_path):
            self.extract_zip(zip_path, tmp_path)
            txt_path = os.path.join(tmp_path, 'AgenRet_TXT.txt')
            
            df = pd.read_csv(txt_path, delimiter='|', encoding='latin-1')
            map_fields = {
                'Ruc': 'ruc',
                'Nombre/Razon': 'razon_social',
                'A partir del': 'a_partir_del',
                'Resolucion': 'resolucion',
            }
            self.sync_model_with_df(self.env['agent.retention'], df, unique_field='Ruc', map_fields=map_fields)

    def update_good_contributor(self):
        """Actualiza el modelo de Buenos Contribuyentes."""
        url = "https://ww1.sunat.gob.pe/descarga/BueCont/BueCont_TXT.zip"
        tmp_path = '/tmp'
        zip_path = os.path.join(tmp_path, 'GoodCont.zip')

        if self.download_file(url, zip_path):
            self.extract_zip(zip_path, tmp_path)
            txt_path = os.path.join(tmp_path, 'BueCont_TXT.txt')

            df = pd.read_csv(txt_path, delimiter='|', encoding='latin-1')
            map_fields = {
                'Ruc': 'ruc',
                'Nombre/Razon': 'razon_social',
                'A partir del': 'a_partir_del',
                'Resolucion': 'resolucion',
            }
            self.sync_model_with_df(self.env['good.contributor'], df, unique_field='Ruc', map_fields=map_fields)

    def update_files(self):
        if self.agents_ready_for_update():
            self.update_agent_retention()
        if self.goods_ready_for_update():
            self.update_good_contributor()