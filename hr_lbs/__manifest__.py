# -*- coding: utf-8 -*-
{
    'name': 'LBS',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Modulo para calculo de gratificaciones de peru
    """,
    'depends': [
        'web',
        'extra_base',
        'hr_payroll',
        'hr_work_entry_contract_enterprise',
        'hr_contracts',
        'hr_employees',
        'hr_5ta',
        'hr_grati',
        'hr_vacation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_lbs.xml',
        'views/hr_lbs_cts.xml',
        'views/hr_lbs_grati.xml',
        'views/hr_lbs_vaca.xml',
        'views/hr_lbs_ded.xml',
        'views/hr_lbs_report.xml',
        'views/report_lbs_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
