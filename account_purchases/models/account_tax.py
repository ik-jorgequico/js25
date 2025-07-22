# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"
    _description = "Impuestos para Perú, modificación para registro de compras y ventas"
    
    type_purchase_ple = fields.Selection([
        ('AG-VG','A. Gravadas - Ventas G. y/o Exportacion'),
        ('AG-VGNG','A. Gravadas - Ventas G. y No gravadas'),
        ('AG-NO','A. Gravadas - Ni Ventas G. Ni Exportacion'),
        ('OTROS', 'Otros Tributos o Cargos'),
    ], "Tipo Compra", store=True)
    
    type_sale_ple = fields.Selection([
        ('EXP','Exportacion'),
        ('VG','Ventas Gravadas'),
        ('EXO','Venta Exonerada'),
        ('INA','Ventas Inafecta'),
    ], "Tipo Venta", store=True)