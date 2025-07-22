# -*- coding: utf-8 -*-
{
    'name': 'Asignación LBS',
    'version': '1.0',
    'author': 'systemaoust',
    'website': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Se las reglas correspondientes se agregaran directamente al Monto LBS.
    """,
    'depends': [
        'hr_payslips',
        'hr_payroll',
    ],
    'data': [
        'views/hr_salary_rule_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
