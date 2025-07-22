from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

import base64

class Company(models.Model):
    _inherit = 'res.company'
    
    portal_user = fields.Boolean(string = 'Creación de usuario portal', store=True)