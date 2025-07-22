# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountSirePurchase(models.Model):
    _name = "account.sire.purchase"
    _inherit = ["account.sire"]
    _description = "Propuesta del SIRE de Compras"
    
    base_dgng = fields.Char("BI Gravado DGNG")
    igv_dgng = fields.Char("IGV / IPM DGNG")
    base_dng = fields.Char("BI Gravado DNG")
    igv_dng = fields.Char("IGV / IPM DNG")
    year_dua_nc = fields.Char("COD. DAM O DSI")
    bs_ss = fields.Char("Clasif de Bss y Sss")
    porcpart = fields.Char("PorcPart")
    imb = fields.Char("IMB")
    car_orig = fields.Char("CAR Orig/ Ind E o I")
    det = fields.Char("Detracción")
    incal = fields.Char("Incal")
    