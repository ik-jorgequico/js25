# -*- coding: utf-8 -*-
{
    'name': 'Impuesto 5ta Categoria',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Modulo para calculo del impuesto de 5ta categoria de peru
    """,
    'depends': [
        'hr_grati',
        'hr_contract',
        'hr_employees',
        'tramo_5ta', 
        'uit_table',
        'hr_payslips',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_5ta.xml',
        'views/hr_5ta_line.xml',
        'views/hr_5ta_subline.xml',
        'views/hr_5ta_reports.xml',
        'views/report_5ta_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    
    'license': 'LGPL-3',
}
