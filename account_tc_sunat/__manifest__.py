# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Peru - Tipo de Cambio Sunat(USD)',
    'version': '1.0',
    'description': """Tipo de cambio PEN/USD""",
    'category': 'Accounting/Accounting',
    'author': 'SystemOuts',
    'sequence': '1',
    'depends': [
                'base',
                'account',
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_currency_update.xml',
        'views/res_currency_view.xml',
    ],
    
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': True,
}
