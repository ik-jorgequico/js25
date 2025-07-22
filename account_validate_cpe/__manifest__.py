# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'Perú - Validación CPE Compras',
	'version': '1.0',
	'description': """Peru - Validación CPE Compras""",
	'category': 'Accounting/Accounting',
	'author': 'SystemOuts',
	'license': 'LGPL-3',
	'sequence': '1',
	'depends': [
		'account',
		'l10n_pe_edi_odoofact',
		'account_purchases',
	],
	'data': (
		'data/cron_run.xml',
		'views/account_move_view.xml',
		'views/res_company_view.xml',
	),
	'installable': True,
	'application': True,
	# 'auto_install': True,
}
