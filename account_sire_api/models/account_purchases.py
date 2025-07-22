# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import requests, zipfile, io, time, pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime
import csv

class AccountPurchases(models.Model):
    _inherit = "account.purchases"
    _description = "Account Purchases for SIRE API"
    _res_model = ""
    _book_code = ""
    _type_proposal = ""
    _fields_rel = []
    _code_type_file = 0  # 0: txt | 1: csv
    
    period_sunat = fields.Char('Periodo', compute='_compute_period_sunat')
    
    token = fields.Char('Token')
    days_sire = fields.Integer('Margen Días SIRE', default=2, required=True)
    
    @api.depends('year', 'month')
    def _compute_period_sunat(self):
        for rec in self:
            rec.period_sunat = f"{rec.year}{rec.month}"
    
    def _validate_inheritances_api(self):
        if self.env.context.get('api_sire_context'):
            if not self._type_proposal:
                raise ValidationError(f'Debe heredar "_type_proposal" en {self._name}')
            if not self._book_code:
                raise ValidationError(f'Debe heredar "_book_code" en {self._name}')
            if not self._fields_rel:
                raise ValidationError(f'Debe heredar "_fields_rel" en {self._name}')
    
    def _get_token(self):
        missing_fields = []
        fields_to_check = [
            ("id_token_sunat", "company_id"),
            ("clave_token_sunat", "company_id"),
            ("vat", "company_id"),
            ("username_sunat", "company_id"),
            ("password_sunat", "company_id"),
        ]
        
        for field_name, model_name in fields_to_check:
            model_instance = getattr(self, model_name)
            field_value = getattr(model_instance, field_name)
            if not field_value:
                field = self.company_id._fields[field_name]
                missing_fields.append(f"{field.string} ({self.company_id._name})")
        
        if missing_fields:
            raise ValidationError("Falta información en los siguientes campos: %s" % ", ".join(missing_fields))
        
        url = f"https://api-seguridad.sunat.gob.pe/v1/clientessol/{self.company_id.id_token_sunat}/oauth2/token/"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded" 
        }
        data = {
            "grant_type": "password",
            "scope": "https://api-sire.sunat.gob.pe",
            "client_id": self.company_id.id_token_sunat,
            "client_secret": self.company_id.clave_token_sunat,
            "username": f"{self.company_id.vat}{self.company_id.username_sunat}",
            "password": self.company_id.password_sunat,
        }
        response = requests.post(url, data=data, headers=headers)
        
        if response.status_code != 200:
            raise ValidationError("Error al obtener token de seguridad:\n%s" % response.text)
        
        self.token = response.json()["access_token"]
    
    def _get_ticket_exists(self, force=False, attempt_record=0):
        ''' Retorna el último ticket si el día de hoy es mayor a `days_sire` del siguiente mes al periodo seleccionado.
        '''
        def register_filter(r):
            return (
                r.get("codProceso") == "10" and
                r["archivoReporte"][0]["nomArchivoContenido"].split(".")[-1] == "txt"
            )
        
        margin_date = datetime(int(self.year), int(self.month), day=self.days_sire) + relativedelta(months=1)
        if datetime.today().date() > margin_date.date() and not force:
            # Obtiene el último ticket creado hasta `days_sire` si existe.
            registers = self._request_registers(attempt_record=attempt_record)
            # Filtra los que sean de tipo `Generar archivo exportar propuesta` y `txt`.
            proposal_registers = list(filter(register_filter, registers))
            
            if len(proposal_registers):
                return proposal_registers[0]["numTicket"]
    
    def _get_ticket(self, force=False, attempt_record=0):
        ''' Retorna el número de ticket para el periodo seleccionado; si no existe crea uno nuevo.
        '''
        num_ticket_exist = self._get_ticket_exists(force=force, attempt_record=attempt_record)
        if num_ticket_exist:
            return num_ticket_exist
        
        # Crear nuevo ticket
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}" 
        }
        params = {
            "codTipoArchivo": self._code_type_file  # REQUIRED 
        }
        
        if self._type_proposal.lower() == "sales":  # VENTAS
            _p_1 = "rvie"
            _p_2 = "exportapropuesta"
            # params.update({
            #     "mtoTotalDesde": "",  # OPTIONAL
            #     "mtoTotalHasta": "",  # OPTIONAL
            #     "fecDocumentoDesde": "",  # OPTIONAL
            #     "fecDocumentoHasta": "",  # OPTIONAL
            #     "numRucAdquiriente": "",  # OPTIONAL
            #     "numCarSunat": "",  # OPTIONAL
            #     "codTipoCDP": "",  # OPTIONAL
            #     "codTipoInconsistencia": "",  # OPTIONAL
            # })
        elif self._type_proposal.lower() == "purchase":  # COMPRAS
            _p_1 = "rce"
            _p_2 = "exportacioncomprobantepropuesta"
            params.update({
                "codOrigenEnvio": 1,  # REQUIRED
                # "mtoDesde": "",  # OPTIONAL
                # "mtoHasta": "",  # OPTIONAL
                # "codTipoCDP": "",  # OPTIONAL
                # "numSerieCDP": "",  # OPTIONAL
                # "numCDP": "",  # OPTIONAL
                # "codInconsistencia": "",  # OPTIONAL
                # "codCar": "",  # OPTIONAL
                # "fecEmisionIni": "",  # OPTIONAL
                # "fecEmisionFin": "",  # OPTIONAL
                # "numDocAdquiriente": "",  # OPTIONAL
            })
        else:
            raise UserError("No existe el tipo de propuesta %s. Revise la configuración en el modelo." % self._type_proposal)
        
        url = f"https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/{_p_1}/propuesta/web/propuesta/{self.period_sunat}/{_p_2}"
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            raise ValidationError("Error al obtener ticket:\n%s" % response.text)
        
        return response.json()["numTicket"]
    
    def _request_registers(self, num_ticket="", attempt_record=0):
        ''' Si no se usa `numTicket`, retorna una lista de todos los tickets del periodo seleccionado.
        '''
        url = "https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rvierce/gestionprocesosmasivos/web/masivo/consultaestadotickets"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}" 
        }
        params = {
            "perIni": self.period_sunat,
            "perFin": self.period_sunat,  # POR AHORA SOLO UN PERIODO, NO UN RANGO
            "page": 1,
            "perPage": 20,
            "numTicket": num_ticket,
            "codOrigenEnvio": 1,
            "codLibro": self._book_code,
        }
        
        response = requests.get(url, params=params, headers=headers)
        response_json = response.json()
        
        if not response.ok:
            for e in response_json["errors"]:
                if str(e["cod"]) == "1070":
                    if attempt_record < 3:
                        attempt_record += 1
                        time.sleep(2)
                        return self._get_list_records(force=True, attempt_record=attempt_record)
                    raise ValidationError(f"1070 - Aún no se han generados tickets para el periodo {self.period_sunat}.")
                
                raise ValidationError(f"{response_json['cod']} - {e['cod']}: {str(e['msg'])}")
        
        registers = response_json["registros"]
        return list(registers)
    
    def _get_status_ticket(self, num_ticket: str):
        ''' Retorna una tupla con el código del tipo de archivo `codTipoAchivoReporte` y el nombre del archivo `nomArchivoReporte`.
        '''
        registers = self._request_registers(num_ticket)
        register = registers[0]  # Obtiene siempre el primero
        ticket_status_code = register["codEstadoProceso"]
        
        # Si aún no se ha completado la creación del archivo en SUNAT, se vuelve a consultar.
        if ticket_status_code != '06':
            time.sleep(2)
            return self._get_status_ticket(num_ticket)
        
        reports = register["archivoReporte"]
        
        if not reports:
            raise ValidationError("No hay reportes para el ticket")
        
        return reports[0]["codTipoAchivoReporte"], reports[0]["nomArchivoReporte"]
    
    def _download_file(self, type_code: str, report_name: str, num_ticket: str, attempt_record=0, attempt_download=0):
        ''' Retorna el archivo `.zip` de la propuesta en bytes. 
        '''
        url = f"https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rvierce/gestionprocesosmasivos/web/masivo/archivoreporte"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        params = {
            "nomArchivoReporte": report_name,
            "codTipoArchivoReporte": type_code,
            "codLibro": self._book_code,
            "numTicket": num_ticket,
            "perTributario": self.period_sunat,
            "codProceso": 10,
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        if not response.ok:
            # Se reintenta 3 veces la descarga.
            if attempt_download <= 3:
                attempt_download += 1
                time.sleep(2)  # Tiempo de espera de 2 segundos.
                return self._download_file(type_code, report_name, num_ticket, attempt_download=attempt_download)
            else:
                response_json = response.json()
                for e in response_json["errors"]:
                    if str(e["cod"]) == "2244" and attempt_record < 3:
                        attempt_record += 1
                        return self._get_list_records(force=True, attempt_record=attempt_record)
                raise ValidationError("Error al descargar el archivo:\n%s" % response.text)
        
        list_records = []
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        file_list = zip_file.namelist()
        
        if not file_list:
            raise ValidationError("No se encontraron archivos en el archivo ZIP")
        
        file_path = file_list[0]  # Se espera solo un archivo en el ZIP
        
        if file_path.endswith('.txt'):
            with zip_file.open(file_path) as txt_file:
                # Leer el contenido como texto
                contenido = txt_file.read().decode('utf-8')
        
                # Reemplazar las comillas curvas por comillas rectas
                contenido = contenido.replace('”', '"').replace('“', '"')
        
                # Crear un objeto similar a archivo a partir del texto corregido
                contenido_io = io.StringIO(contenido)
        
                # Leer el contenido ya corregido con pandas
                df = pd.read_csv(contenido_io, sep="|", quoting=csv.QUOTE_NONE,dtype=str,engine="python")
                #df = pd.read_csv(txt_file, sep="|", dtype=str,engine="python")
                df = df.fillna("")
                list_records = df.to_dict(orient='records')
        elif file_path.endswith('.csv'):
            raise ValidationError("Tipo de archivo (.csv) no soportado.")
        else:
            raise ValidationError("No se encontró el archivo TXT en el archivo ZIP")
        
        return list_records
    
    def _get_list_records(self, force=False, attempt_record=0):
        numTicket = self._get_ticket(force, attempt_record=attempt_record)
        type_code, report_name = self._get_status_ticket(numTicket)
        return self._download_file(type_code, report_name, numTicket, attempt_record=attempt_record)
    
    def import_sire_proposal(self):
        self._validate_inheritances_api()
        self._get_token()
        
        account_sire_object = self.env[self._res_model]
        sire_line_ids = account_sire_object.search([('company_ruc','=',self.company_id.vat),('periodo','=',self.period_sunat)])
        car_est_dict = {x.car_sunat: x.est_comp for x in sire_line_ids}
        list_records = self._get_list_records()
        
        for rec in list_records:
            car_sunat = rec.get("CAR SUNAT")
            est_comp = rec.get("Est. Comp")
            est_comp_sire = car_est_dict.get(car_sunat)
            
            if car_sunat not in car_est_dict.keys():
                account_sire_object.create({field: rec.get(header) for field, header in self._fields_rel})
            elif est_comp != est_comp_sire:
                account_sire_object.write({"est_comp": est_comp})
    