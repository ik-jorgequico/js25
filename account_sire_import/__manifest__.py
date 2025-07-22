# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Peru - Importar Propuesta SIRE',
    'version': '1.0',
    'description': """Módulo que agrega la función para importar facturas del SIRE""",
    'category': 'Accounting/Accounting',
    'author': 'SystemOuts',
    "license": "AGPL-3",
    'sequence': '-1',
    'depends': [
        'account_sire',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/data_sales_views.xml',
        'views/data_purchase_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
