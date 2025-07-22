# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Perú - Reportes Contables',
    'version': '0.1',
    'description': """Perú Reportes adicionales para estados financieros""",
    'category': 'Accounting/Accounting',
    'author': 'SystemOuts',
    'sequence': '-1',
    'depends': [
        'account',
        'account_purchases',
        'report_xlsx_plus',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/data_mov_year_view.xml',
        'views/account_move_line.xml',
        'views/res_company_views.xml',
        'views/res_uit_views.xml',
        'views/menu_views.xml',
        'data/actions_report.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': True,
}
