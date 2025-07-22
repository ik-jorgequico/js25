# -*- coding: utf-8 -*-
{
    'name': 'Beneficio Extra',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Se agrega beneficios no correspondientes al RG.
    """,
    'depends': [
        'hr_contract',
        'hr_payslips',
        'hr_payroll',
    ],
    'data': [
        'views/hr_contract.xml',
        'views/hr_salary_rule.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
