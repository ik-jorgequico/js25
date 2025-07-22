# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import models, fields, _
import requests, json
import time


class AccountMoveValidationCpeApi(models.Model):
    _inherit = "account.move"
    _description = "Validacion CPE de Compras con API Sunat"
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,store=True)
    
    send_json_validate = fields.Text("Envio Validación SUNAT", store=True)
    result_json_validate = fields.Text("Resultado Validación SUNAT", store=True)

    account_validate_state_cp = fields.Selection([
        ("0", "NO EXISTE"),
        ("1", "ACEPTADO"),
        ("2", "ANULADO"),
        ("3", "AUTORIZADO"),
        ("4", "NO AUTORIZADO"),
    ], "Estado del Comprobante", store=True)
    
    account_validate_state_ruc = fields.Selection([
        ("00", "ACTIVO"),
        ("01", "BAJA PROVISIONAL"),
        ("02", "BAJA PROV. POR OFICIO"),
        ("03", "SUSPENSION TEMPORAL"),
        ("10", "BAJA DEFINITIVA"),
        ("11", "BAJA DE OFICIO"),
        ("22", "INHABILITADO-VENT.UNICA"),
    ], "Estado del Contribuyente", store=True)
    
    account_validate_state_cond_domi_ruc = fields.Selection([
        ("00", "HABIDO"),
        ("09", "PENDIENTE"),
        ("11", "POR VERIFICAR"),
        ("12", "NO HABIDO"),
        ("20", "NO HALLADO"),
    ], "Condición de Domicilio del Contribuyente", store=True)
    
    account_validate_observations = fields.Text("Observaciones", store=True)
    
    def action_validate_invoices(self):
        invoices = self.search([
            ('journal_id.have_purchase', '=', True),
            ('journal_id.type', '=', 'purchase'),
            ('move_type', '=', 'in_invoice'),
        ])
        for rec in invoices:
            rec.run(is_cron=True)
            time.sleep(5)
    
    def get_token(self, is_cron=False):
        client_secret = self.company_id.clave_token_sunat
        client_id = self.company_id.id_token_sunat
        
        try:
            grant_type = "client_credentials"
            scope = "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes"
            headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"}
            data = {
                "grant_type": grant_type,
                "scope": scope,
                "client_id": client_id,
                "client_secret": client_secret
            }
            url = f"https://api-seguridad.sunat.gob.pe/v1/clientesextranet/{client_id}/oauth2/token/"
            auth_response = requests.post(url, data=data, headers=headers)
            auth_response_json = auth_response.json()
            auth_token = auth_response_json["access_token"]
            token_type=auth_response_json["token_type"]
            expires_in=auth_response_json["expires_in"]
            auth_token_header_value = "Bearer %s" % auth_token
            auth_token_header = {"Authorization": auth_token_header_value}
            return auth_token_header
        
        except Exception as e:
            if not is_cron:
                raise ValidationError(_('La compañía no tiene ID Y CLAVE, o validación errada.'))

    def connect(self, ruc, rc, output, cont=0, is_cron=False):
        auth_token_header=self.get_token(is_cron)
        url = "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/"+ruc+"/validarcomprobante"
        headers = {'Authorization': auth_token_header}
        r = requests.post(url, json=rc, headers=auth_token_header)
        r = json.loads(r.text)
        if r['message']=='Unauthorized' and cont<10:
            r = self.connect(ruc,rc,output,cont, is_cron)
            cont += 1
        return r
    
    def get_data(self, is_cron=False):
        """
        Propiedad 		| Tipo 	  | Longitud   | Descripción 						| Obligatorio
        numRuc 			| String  | 11 		   | Número de RUC emisor comprobante 	| Si
        codComp 		| String  | an2		   | Código de tipo de comprobante 		| Si
        numeroSerie 	| String  | an4   	   | Número de serie del comprobante	| Si
        numero 			| Integer | an…8 	   | Número del comprobante				| Si
        fechaEmision 	| date    | dd/mm/yyyy | Fecha de emisión del comprobante 	| Si
        monto 			| decimal | n(8,2) 	   | Monto total del comprobante 		| *Solo para electrónico

        Codigo 			| Descripcion
        01				| FACTURA
        03				| BOLETA DE VENTA 
        04				| LIQUIDACIÓN DE COMPRA
        07				| NOTA DE CREDITO 
        08				| NOTA DE DEBITO
        R1				| RECIBO POR HONORARIOS
        R7				| NOTA DE CREDITO DE RECIBOS
        """
        def transform_code(code):
            if code == "01":
                return "01"
            elif code == "03":
                return "03"
            elif code == "07":
                return "07"
            elif code == "08":
                return "08"
            elif code == "02":
                return "R1"
            
        try:
            company_id_vat = self.partner_id.vat
            tipdoc_sunat_code = transform_code(self.l10n_latam_document_type_id.code)
            numcomp_sunat = self.numcomp_sunat 
            seriecomp_sunat = self.seriecomp_sunat
            date = self.invoice_date
            amount = self.amount_total
                
            if company_id_vat or tipdoc_sunat_code or numcomp_sunat or seriecomp_sunat or date or amount:
                return {
                    "numRuc" : company_id_vat,
                    "codComp" : tipdoc_sunat_code,
                    "numero" : str(int(numcomp_sunat)),
                    "numeroSerie" : seriecomp_sunat,
                    "fechaEmision" : date.strftime("%d/%m/%Y"),
                    "monto" : '%.2f' % amount
                }
        
        except Exception as e:
            if not is_cron:
                raise ValidationError(_(f'ERROR GET DATA {e}'))

    def run(self, is_cron=False):
        def filter_records(x):
            first_year_date = x.date.replace(day=1, month=1)
            return (
                x.move_type == 'in_invoice' and
                x.date >= first_year_date and
                x.account_validate_state_cp != "1"
            )

        for record in self.filtered(filter_records):
            try:
                output=[]
                ruc = str(record.company_id.vat)
                data_json = record.get_data(is_cron)
                r = record.connect(ruc, data_json,output,is_cron)
                send_json_validate = str(data_json)
                account_validate_state_cp = ""
                account_validate_state_ruc = ""
                account_validate_state_cond_domi_ruc = ""
                account_validate_observations = ""
                
                if r.get("data"):
                    account_validate_state_cp = r.get("data").get("estadoCp")
                    account_validate_state_ruc = r.get("data").get("estadoRuc")
                    account_validate_state_cond_domi_ruc = r.get("data").get("condDomiRuc")
                    account_validate_observations = '\n'.join(r.get("data").get("observaciones"))
                
                record.write({
                    'send_json_validate': send_json_validate,
                    'account_validate_state_cp': account_validate_state_cp,
                    'account_validate_state_ruc': account_validate_state_ruc,
                    'account_validate_state_cond_domi_ruc': account_validate_state_cond_domi_ruc,
                    'account_validate_observations': account_validate_observations,
                    "result_json_validate":str(r)
                })
                
            except Exception as e:
                if not is_cron:
                    raise ValidationError(_(f'ERROR RUN {e}'))                    
