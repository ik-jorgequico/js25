# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountSireSales(models.Model):
    _name = "account.sire.sales"
    _inherit = ["account.sire"]
    _description = "Propuesta del SIRE de Ventas"
    
    expo = fields.Char("Valor Facturado Exportación")
    desc_base_dg = fields.Char("Dscto BI")
    desc_igv_dg = fields.Char("Dscto IGV / IPM")
    exonerado = fields.Char("Exonerado")
    base_ivap = fields.Char("BI Grav IVAP")
    ivap = fields.Char("IVAP")
    fob_embarcado = fields.Char("Valor FOB embarcado")
    op_gratuita = fields.Char("Valor OP Gratuitas")
    operation_sales_type = fields.Char("Tipo Operación")	
    dam_cp = fields.Char("DAM / CP")
    