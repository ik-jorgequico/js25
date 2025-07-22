# -*- coding: utf-8 -*-
{
    'name': 'Campos Adicionales',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        1. Se agrego Company a AccountAnalyticPlan
    """,
    'depends': [
        'base',
        'analytic',
    ],
    'data': [
        'data/ir_rule.xml',
        'views/account_analytic_plan_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
