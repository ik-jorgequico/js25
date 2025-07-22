# -*- coding: utf-8 -*-
{
    'name': 'Afectaciones',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Se agrega afectaciones en ausencias para el cálculo de beficions sociales.
    """,
    'depends': [
        'hr_contract',
        'hr_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_leave_import.xml',
        'views/hr_leave_type.xml',
        'views/hr_leave_subtype.xml',
        'views/hr_leave.xml',
        'views/hr_leave_menu.xml',
        
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': True,
}
