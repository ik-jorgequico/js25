# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Peru - Regularizacion Contable',
    'version': '1.0',
    'description': """Regularizacion, compensacion de cuentas contables""",
    'category': 'Accounting/Accounting',
    'author': 'Systemouts',
    "license": "AGPL-3",
    'sequence': '-1',
    'depends': ['account',
                'l10n_pe_edi_odoofact',
                'l10n_latam_base',
                'account_purchases',
                ],
    'data': (
        'security/ir.model.access.csv',
        'views/account_regularization_view.xml',
        'views/ir_rules.xml',
    ),
    'installable': True,
    'application': True,
    'auto_install': True,
}
