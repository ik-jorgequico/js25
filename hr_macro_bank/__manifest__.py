# -*- coding: utf-8 -*-
{
    'name': 'Generar Macro para Beneficio Social, Nómina',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Modulo para generar reporte macro para Beneficio Social y nómina
    """,
    'depends': [
        'hr_cts',
        'hr_grati',
        'hr_utilities',
        'hr_lbs',
        'ent_ohrms_loan',
        'hr_payroll',
        'hr_vacation',
    ],
    'data': [
        'views/hr_cts.xml',
        'views/hr_grati.xml',
        'views/hr_utilities.xml',
        'views/hr_loan.xml',
        'views/hr_payslip.xml',
        'views/hr_vaca.xml',
        'views/hr_vaca_line.xml',
        'views/hr_lbs_line.xml',
    ],
    'installable': True,
    'auto_install': True,
    
    'license': 'LGPL-3',
}
