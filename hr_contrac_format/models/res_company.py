from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

import base64

class Company(models.Model):
    _inherit = 'res.company'
    
    gerente_firma = fields.Binary(string = 'Firma de gerente', attachment=True)
    gerente_name = fields.Char(string = 'Nombre de gerente', store=True)
    #Nuevos campos
    gerente_job = fields.Char(string = 'Puesto del gerente', store=True)
    gerente_doc_type = fields.Selection([('1', 'DNI'), ('4', 'CE'),('6', 'RUC'),('7', 'PASAPORTE')],string = 'Tipo de documento del gerente', store=True)
    gerente_doc = fields.Char(string = 'N° de identificacion del gerente', store=True)
    gerente_partida_electroc = fields.Char(string = 'N° de partida electronica', store=True)

    company_abbr = fields.Char(string = 'Abreviatura de la Empresa', store=True)