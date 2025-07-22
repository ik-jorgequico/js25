# -*- coding: utf-8 -*-
{
    'name': 'Tabla de UIT',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Se agregan nuevas características al valor de UIT.
    """,
    'depends': [
        'hr_employees',
        'hr_contracts',
        'hr_payslips',
        'tramo_5ta',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/uit_table.xml',
        'data/uit_values_table.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}