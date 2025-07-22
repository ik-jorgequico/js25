# -*- coding: utf-8 -*-
{
    'name': 'Días Feriados',
    'version': '1.0',
    'author': 'SystemOuts',
    'description': """
        Módulo para Días Feriados
    """,
    'depends': [
        'hr_grati',
        'hr_regimen_peru',
        'hr_payslips',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_holidays_peru_views.xml',
        'data/hr_holidays_peru_input_data.xml'
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
