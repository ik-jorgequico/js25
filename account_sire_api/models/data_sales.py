# -*- coding: utf-8 -*-
from odoo import models


class DataSales(models.Model):
    _inherit = "data.sales"
    _description = "Data Sales SIRE API"
    _book_code = "140000"
    _type_proposal = "sales"
    _fields_rel = [
        # (odoo_field, sunat_header)
        ("company_ruc", "Ruc"),
        ("company_name", "Razon Social"),
        ("periodo", "Periodo"),
        ("car_sunat", "CAR SUNAT"),
        ("invoice_date", "Fecha de emisión"),
        ("invoice_date_due", "Fecha Vcto/Pago"),
        ("type_cpe", "Tipo CP/Doc."),
        ("serie_cpe", "Serie del CDP"),
        ("num_cpe", "Nro CP o Doc. Nro Inicial (Rango)"),
        ("num_final", "Nro Final (Rango)"),
        ("type_doc", "Tipo Doc Identidad"),
        ("vendor_doc", "Nro Doc Identidad"),
        ("vendor_name", "Apellidos Nombres/ Razón Social"),
        ("expo", "Valor Facturado Exportación"),
        ("base_dg", "BI Gravada"),
        ("desc_base_dg", "Dscto BI"),
        ("igv_dg", "IGV / IPM"),
        ("desc_igv_dg", "Dscto IGV / IPM"),
        ("exonerado", "Mto Exonerado"),
        ("inafecto", "Mto Inafecto"),
        ("isc", "ISC"),
        ("base_ivap", "BI Grav IVAP"),
        ("ivap", "IVAP"),
        ("icbper", "ICBPER"),
        ("otros", "Otros Tributos"),
        ("total_cpe", "Total CP"),
        ("currency", "Moneda"),
        ("exchange", "Tipo Cambio"),
        ("invoice_date_nc", "Fecha Emisión Doc Modificado"),
        ("type_cpe_nc", "Tipo CP Modificado"),
        ("serie_cpe_nc", "Serie CP Modificado"),
        ("num_cpe_nc", "Nro CP Modificado"),
        ("id_project", "ID Proyecto Operadores Atribución"),
        ("type_note", "Tipo de Nota"),
        ("est_comp", "Est. Comp"),
        ("fob_embarcado", "Valor FOB Embarcado"),
        ("op_gratuita", "Valor OP Gratuitas"),
        ("operation_sales_type", "Tipo Operación"),
        ("dam_cp", "DAM / CP"),
    ]
    