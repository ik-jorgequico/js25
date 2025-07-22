# -*- coding: utf-8 -*-
from odoo import models


class DataPurchase(models.Model):
    _inherit = "data.purchase"
    _description = "Data Purchase SIRE API"
    _res_model = "account.sire.purchase"
    _book_code = "080000"
    _type_proposal = "purchase"
    _fields_rel = [
        # (odoo_field, sunat_header)
        ("company_ruc", "RUC"),
        ("company_name", "Apellidos y Nombres o Razón social"),
        ("periodo", "Periodo"),
        ("car_sunat", "CAR SUNAT"),
        ("invoice_date", "Fecha de emisión"),
        ("invoice_date_due", "Fecha Vcto/Pago"),
        ("type_cpe", "Tipo CP/Doc."),
        ("serie_cpe", "Serie del CDP"),
        ("year_dua", "Año"),
        ("num_cpe", "Nro CP o Doc. Nro Inicial (Rango)"),
        ("num_final", "Nro Final (Rango)"),
        ("type_doc", "Tipo Doc Identidad"),
        ("vendor_doc", "Nro Doc Identidad"),
        ("vendor_name", "Apellidos Nombres/ Razón  Social"),
        ("base_dg", "BI Gravado DG"),
        ("igv_dg", "IGV / IPM DG"),
        ("base_dgng", "BI Gravado DGNG"),
        ("igv_dgng", "IGV / IPM DGNG"),
        ("base_dng", "BI Gravado DNG"),
        ("igv_dng", "IGV / IPM DNG"),
        ("inafecto", "Valor Adq. NG"),
        ("isc", "ISC"),
        ("icbper", "ICBPER"),
        ("otros", "Otros Trib/ Cargos"),
        ("total_cpe", "Total CP"),
        ("currency", "Moneda"),
        ("exchange", "Tipo de Cambio"),
        ("invoice_date_nc", "Fecha Emisión Doc Modificado"),
        ("type_cpe_nc", "Tipo CP Modificado"),
        ("serie_cpe_nc", "Serie CP Modificado"),
        ("year_dua_nc", "COD. DAM O DSI"),
        ("num_cpe_nc", "Nro CP Modificado"),
        ("bs_ss", "Clasif de Bss y Sss"),
        ("id_project", "ID Proyecto Operadores"),
        ("porcpart", "PorcPart"),
        ("imb", "IMB"),
        ("car_orig", "CAR Orig/ Ind E o I"),
        ("det", "Detracción"),
        ("type_note", "Tipo de Nota"),
        ("est_comp", "Est. Comp."),
        ("incal", "Incal"),
    ]
    