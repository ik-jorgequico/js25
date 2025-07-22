# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Peru - Campos Adicionales',
    'version': '1.0',
    'description': """Campos adicionales para el registro de compras y ventas - Perú""",
    'category': 'Accounting/Accounting',
    'author': 'SystemOuts',
    'sequence': '-1',
    'depends': [
        'account',
        'l10n_pe_edi_catalog',
        'l10n_pe_edi_odoofact',
        'l10n_latam_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_items.xml',      
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
        'views/account_tax_views.xml',
        'views/res_country_view.xml',
        'views/account_purchases_views.xml',
        'views/data_purchase_view.xml',
        'views/data_purchase_nodom_view.xml',
        'views/data_sales_view.xml',
        'views/data_ple51_view.xml',
        'views/data_ple53_view.xml',
        'views/data_ple61_view.xml',
        'views/ir_rules.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    # 'auto_install': True,
}
