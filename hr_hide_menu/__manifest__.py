# -*- coding: utf-8 -*-
{
    'name': 'Hide - Menus',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Se agrega grupos a algunos menus para que solo sea visualizado por el administrador.
    """,
    'depends': [
        'hr',
        'hr_payroll',
        'hr_work_entry_contract_enterprise',
    ],
    'data': [
        'views/hide_menus.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': True,
}
