# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountSire(models.Model):
    _name = "account.sire"
    _description = "Account Sire"
    
    sire_check = fields.Selection([
        ('pending', 'Pendiente'),
        ('checked', 'Validado'),
    ], "Estado", default='pending', store=True)
    company_ruc = fields.Char("RUC", readonly=True)
    company_name = fields.Char("Razón Social Compañía", readonly=True)
    periodo = fields.Char("Periodo", readonly=True)
    car_sunat = fields.Char("CAR Sunat", readonly=True)
    invoice_date = fields.Char("Fecha de emisión")
    invoice_date_due = fields.Char("Fecha Vcto/Pago")
    type_cpe = fields.Char("Tipo CP/Doc.", readonly=True)
    serie_cpe = fields.Char("Serie del CDP", readonly=True)
    num_cpe = fields.Char("Nro CP o Doc. Nro Inicial (Rango)", readonly=True)
    year_dua = fields.Char('Año Dua', readonly=True)
    num_final = fields.Char("Nro Final (Rango)")
    type_doc = fields.Char("Tipo Doc. Identidad", readonly=True)
    vendor_doc = fields.Char("Nro. Doc. Identidad")
    vendor_name = fields.Char("Apellidos Nombres / Razón Social")
    base_dg = fields.Char("BI Gravado DG")
    igv_dg = fields.Char("IGV / IPM DG")
    inafecto = fields.Char("Inafecto")
    isc = fields.Char("ISC")
    icbper = fields.Char("ICBPER")
    otros = fields.Char("Otros Trib. / Cargos")
    total_cpe = fields.Char("Total CP")
    currency = fields.Char("Moneda")
    exchange = fields.Char("Tipo de Cambio")
    invoice_date_nc = fields.Char("Fecha Emisión Doc Modificado")
    type_cpe_nc = fields.Char("Tipo CP Modificado")
    serie_cpe_nc = fields.Char("Serie CP Modificado")
    num_cpe_nc = fields.Char("Nro CP Modificado")
    id_project = fields.Char("ID Proyecto Operadores")
    type_note = fields.Char("Tipo de Nota")
    est_comp = fields.Char("Est. Comp")
    