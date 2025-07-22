# -*- coding: utf-8 -*-
{
    'name': 'RRHH - Reglas',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Reglas
    """,
    'depends': [
        'base',
        'hr',
        'hr_payroll',
        'hr_employees',
        'hr_cts',
        'hr_vacation',
        'hr_lbs',
        'hr_utilities',
        'hr_grati',
        'hr_afectations',
        'hr_holidays',
        'hr_report_excel',
        'hr_reports_payroll',
        'hr_work_entry',
        'hr_regimen_peru', 
    ],
    'data': [
        'views/equal_company.xml',
        'data/ir_rule.xml',
   ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
