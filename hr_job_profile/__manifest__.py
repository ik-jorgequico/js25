# -*- coding: utf-8 -*-
{
    'name': 'Perfil del puesto de trabajo',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': "",
    'depends': [
        'hr',
        'hr_employees',
        'hr_contract',
        'hr_contrac_format',
        'hr_contracts',
        'hr_work_entry_contract',
        'hr_attendance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_job.xml',
        'views/hr_job_profile_pdf_report.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
