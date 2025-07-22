# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Peru - Cuentas Destino',
    'version': '1.0',
    'description': """destiny accounts for peru""",
    'category': 'Accounting/Accounting',
    'author': 'Systemouts',
    'sequence': '-1',
    'depends': ['account',
                'analytic',
                'l10n_latam_base',
                ],
    'data': (
        'views/account_analytic_account.xml',
        'views/account_move_views.xml',
    ),
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': True,
}