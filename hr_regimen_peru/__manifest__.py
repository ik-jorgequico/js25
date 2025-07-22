# -*- coding: utf-8 -*-
{
    'name': 'Peru -- Regimen Laboral',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Regimenes laborales en el Peru 
    """,
    'depends': [
        'base',
        'hr',
        'hr_contract',
        'hr_payslips',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_regimen_peru_view.xml',
        # 'data/ir_rule.xml',
        'data/regimen_peru_data.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    # 'auto_install': False,
}
