# -*- coding: utf-8 -*-
{
    'name': 'Utilidades',
    'version': '1.0',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        Se agrega utilidades de nómina.
    """,
    'depends': [
        'base',
        'hr_employees',
        'hr_afectations',
        'hr_payroll',
        'hr_contracts',
        'hr_grati',
        'l10n_pe_vat_sunat',

    ],
    'data': [
        'views/hr_utilities_incomes_report.xml',
        # 'data/template_of_utility_email.xml',
        'views/hr_utilities_report.xml',
        'views/hr_utilities_template.xml',
        'views/hr_utilities_incomes.xml',
        'views/hr_utilities.xml',
        'security/ir.model.access.csv',
        'wizard/bulk_send_payslips_view.xml',
        # 'views/hr_utilities_batches_mail.xml',
        # 'views/hr_utilities_mail.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': True,
}
