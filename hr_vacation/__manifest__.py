# -*- coding: utf-8 -*-
{
    'name': 'Vacaciones',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Record Vacacional y Calculo Vacacional
    """,
    'depends': [
        'hr_contract',
        'hr_afectations',
        'hr_employees',
        'hr_grati',
        'additional_fields',
        'report_xlsx'
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/xls_reports.xml',
        'views/hr_leave_menu.xml',
        'views/hr_vacation.xml',
        'views/hr_vacation_for_reports.xml',
        'views/hr_vacation_calculate.xml',
        'views/hr_vacation_purchased.xml',
        'views/hr_leave.xml',
        'data/vacation_type.xml',
        'data/vacation_sub_type.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
