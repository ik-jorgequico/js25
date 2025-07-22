# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Peru - Conexión SIRE API',
    'version': '1.0',
    'description': """Módulo para descargar propuesta SIRE""",
    'category': 'Accounting/Accounting',
    'author': 'SystemOuts',
    "license": "AGPL-3",
    'sequence': '-1',
    'depends': [
        'account_sire',
        'account_sire_import',
        'account_validate_cpe',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/data_purchase_views.xml',
        'views/data_sales_views.xml',
        'views/res_company_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
