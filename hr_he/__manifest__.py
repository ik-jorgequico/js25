# -*- coding: utf-8 -*-
{
    'name': 'Horas Extra',
    'version': '1.0',
    'author': 'SystemOuts',
    'description': """
        Módulo para cálculo de Horas Extra
    """,
    'depends': [
        'hr_grati',
        'hr_regimen_peru'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_he_views.xml',
        'data/hr_he_input_data.xml'
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
