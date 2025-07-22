# -*- coding: utf-8 -*-
{
    'name': 'Agregar Configuracion a empresas nuevas',
    'version': '1.0',
    'author': 'SystemOuts',
    'category': 'Localization PE/HR',
    'description': """
        Agregar Configuracion a empresas nuevas
    """,
    'depends': [
        'base',
        'hr_payroll', 
        'hr_payslips',
        'hr_regimen_peru',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/hr_new_company_view.xml",
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
