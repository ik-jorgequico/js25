# -*- coding: utf-8 -*-
{
    'name': 'Formato de contratos',
    'version': '1.1',
    'author': 'SystemOuts',
    'website': '',
    'category': 'Localization PE/HR',
    'description': """
        
    """,
    'depends': [
        'hr_work_entry_contract',
        'hr_attendance',
        'hr_contract',
        'hr_contracts', 
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_job.xml',
        'views/res_company.xml',

        'data/data_ayr/template_ayr_coordinador.xml',
        'data/data_ayr/template_ayr_supervisor_ventas.xml',
        'data/data_ayr/template_ayr_vendor_mass.xml',
        'data/data_ayr/template_ayr_asesor_ventas.xml',
        'data/data_ayr/template_ayr_part_time.xml',
        
        'views/contract_ayr/hr_contract_ayr_coordinador.xml',
        'views/contract_ayr/hr_contract_ayr_supervisor_ventas.xml',
        'views/contract_ayr/hr_contract_ayr_vendor_mass.xml' ,
        'views/contract_ayr/hr_contract_ayr_asesor_ventas.xml',
        'views/contract_ayr/hr_contract_ayr_part_time.xml',
        
        'views/hr_contract_adm_teletrabajo_report.xml',
        'views/hr_contract_operative_operative_report.xml',
        'views/hr_contract_operative_seller_report.xml',
        'views/hr_contract_renovation_report.xml',
        
        'views/hr_contract.xml',
        'views/hr_contract_adm_hybrid_report.xml',
        
        'data/template_hybrid.xml',
        'data/template_operative.xml',
        'data/template_seller.xml',
        'data/template_teletrabajo.xml',
        'data/template_renovation.xml',
        'data/template_firma.xml',
        'data/template_style_contrato.xml',
        'data/paper_format_contract.xml',

        
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
