# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Compatibilidad de Campos Adicionales con Enterprise',
    'version': '1.0',
    'description': """Compatibilidad del módulo account_purchases con la versión Enterprise de Odoo""",
    'category': 'Accounting/Accounting',
    'author': 'SystemOuts',
    'sequence': '-1',
    'depends': [
        'web_enterprise',
        'account_purchases',
        'account_accountant'
    ],
    'data': [
        'views/menu_enterprise.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
    'application': False,
}
