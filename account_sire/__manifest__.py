# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Peru - Validar Propuesta SIRE',
    'version': '1.0',
    'description': """Módulo que agrega la función para validar la propuesta del SIRE contra los registros de cada compañia""",
    'category': 'Accounting/Accounting',
    'author': 'SystemOuts',
    "license": "AGPL-3",
    'sequence': '-1',
    'depends': [
        'account_purchases',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/data_purchase_views.xml',
        'views/data_sales_views.xml',
        'views/account_sire_views.xml',
        'views/sire_purchase_views.xml',
        'views/sire_sales_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
