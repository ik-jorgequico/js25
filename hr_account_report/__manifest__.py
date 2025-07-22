#-*- coding:utf-8 -*-
{
    'name': 'Asientos Contables - Reportes en Excel',
    'category': 'Human Resources/Payroll',
    'author': 'SystemOuts',
    'version': '1.0',
    'description': """Asientos Contables - Reportes en Excel""",
    'depends': [
        'hr_employees',
        'hr_payroll', 
        'hr_payroll_account',
        'hr_payslips',
        'hr_contracts',
        'hr_grati',
        'hr_lbs',
        'hr_report_excel',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_run_form.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': True,
}
