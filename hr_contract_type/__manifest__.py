# -*- coding: utf-8 -*-
{
    'name': 'Tipos de contratos',
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
        # 'security/ir.model.access.csv',
        'data/contract_type.xml',
        'views/hr_contract_type.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
    
    'license': 'LGPL-3',
}
