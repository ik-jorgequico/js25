#######################################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
#######################################################################################

{
    "name": "Guias electronicas Peru - PSE/OSE Nubefact",
    "version": "1.1",
    "author": "OPeru",
    "category": "Stock",
    "summary": "Electronic Picking Peru - PSE/OSE Nubefact",
    "website": "http://www.operu.pe/facturacion-electronica",
    "depends": [
        "base",
        "stock",
        "l10n_pe_edi_odoofact",
        "l10n_pe_edi_base",
    ],
    "data": [
        "data/ir_sequence_data.xml",
        # "report/epicking_report_template_old.xml",#modificar
        # "report/epicking_report.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/stock_picking_views.xml",
        "security/ir.model.access.csv", 
        "views/stock_canceled_edi_picking_views.xml",
    ],
    "installable": True,
    "external_dependencies": {
        "python": [
            "bs4",
            "json",
            "re",
            "pytz",
        ],
    },
    "images": ["static/description/banner.png"],
    "live_test_url": "http://operu.pe/manuales",
    "license": "LGPL-3",
    "price": 99.00,
    "currency": "USD",
    "sequence": 1,
    "support": "modulos@operu.pe",
}
