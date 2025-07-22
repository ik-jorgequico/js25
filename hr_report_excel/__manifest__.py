#-*- coding:utf-8 -*-
{
    'name': 'Reportes en Excel - Provisiones',
    'category': 'Human Resources/Payroll',
    'author': 'SystemOuts',
    'version': '1.0',
    'description': """Provisiones - Reportes en Excel""",
    'depends': [
        'hr_employees',
        'hr_payslips',
        'hr_contracts',
        'hr_grati',
        'hr_lbs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_prov_cts.xml',
        'views/hr_prov_cts_line.xml',
        'views/hr_prov_cts_subline.xml',
        'views/hr_prov_grati.xml',
        'views/hr_prov_grati_line.xml',
        'views/hr_prov_grati_subline.xml',
        'views/hr_prov_vaca.xml',
        'views/hr_prov_vaca_line.xml',
        'views/hr_prov_vaca_subline.xml',
        
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': True,
}
