# -*- coding: utf-8 -*-
{
    'name': 'Extra Base',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Extra Base
    """,
    'depends': [
        'hr_payroll',
        'hr_contract',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/basic_salary.xml',
        'views/holidays.xml',
        'views/sundays.xml',
        'report/peru_rrhh_layout.xml',
        'data/holidays.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
