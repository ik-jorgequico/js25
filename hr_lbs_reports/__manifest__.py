# -*- coding: utf-8 -*-
{
    'name': 'Reportes LBS',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Modulo para reportes de LBS
    """,
    'depends': [
        'hr_lbs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_lbs.xml',
        'views/hr_lbs_report.xml',
        'views/report_lbs_work_templates.xml',
        'views/report_lbs_cts_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
