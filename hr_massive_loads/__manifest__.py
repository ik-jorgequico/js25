# -*- coding: utf-8 -*-
{
    'name': 'Cargas masivas',
    'version': '1.0',
    'author': 'SystemOuts',
    'description': """
        Módulo para carga archivos de data masiva
    """,
    'depends': [
        'hr_payroll',
    ],
    'data': [
        'views/hr_payslip_run_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
