# -*- coding: utf-8 -*-
{
    'name': 'Tramos de 5ta Categoría',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Se agregan nuevas características a Tramos de 5ta Categoría.
    """,
    'depends': [
        'hr_employees',
        'hr_contracts',
        'hr_payslips',
        'hr_work_entry_contract_enterprise'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/tramo_5ta.xml',
        'data/5ta_sections.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}