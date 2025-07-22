# -*- coding: utf-8 -*-
{
    'name': 'Contratos',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        
    """,
    'depends': [
        'hr',
        'hr_work_entry_contract',
        'hr_attendance',
        'hr_contract',
    ],
    'data': [
        'data/low_reason.xml',
        'security/ir.model.access.csv',
        'views/hr_contract.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
