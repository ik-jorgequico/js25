# -*- coding: utf-8 -*-
{
    'name': 'CTS',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Modulo para calculo de cts de peru
    """,
    'depends': [
        'hr_employees',
        'hr_payslips',
        'hr_contracts',
        'hr_grati',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_cts.xml',
        'views/hr_cts_line.xml',
        'views/hr_cts_subline.xml',
        'views/hr_cts_report.xml',
        'views/report_cts_templates.xml',
        # 'data/payroll_structure_type.xml',
        'data/report_paper_format.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
