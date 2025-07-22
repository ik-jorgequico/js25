# -*- coding: utf-8 -*-
{
    'name': 'Cuentas Bancarias',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Este módulo permite gestionar las cuentas bancarias de los empleados.
        """,
    'depends': [
        'hr',
        'account',
        'hr_employees',
    ],
    'data': [
        'data/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/hr_bank_account_views.xml',
        'views/hr_employee_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
