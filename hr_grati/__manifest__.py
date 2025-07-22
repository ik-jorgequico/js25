# -*- coding: utf-8 -*-
{
    'name': 'Gratificaciones',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Modulo para calculo de gratificaciones de peru
    """,
    'depends': [
        'hr_work_entry_contract_enterprise',
        'hr_contract',
        'hr_employees',
        'hr_payslips',
        'additional_fields'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_grati.xml',
        'views/hr_grati_line.xml',
        'views/hr_grati_subline.xml',
    ],
    'installable': True,
    'auto_install': True,
    
    'license': 'LGPL-3',
}
