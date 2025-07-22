# -*- coding: utf-8 -*-
{
    'name': "Actualizar RUC y DNI",
    'summary': """ Actualiza RUC desde el portal SUNAT """,
    'description': """
        Este módulo devuelve información desde el portal SUNAT y además se puede configurar para obtener
        los representantes legales así como los locales anexos.
    """,
    'version': '1.0',
    'author': "SystemOuts",
    'category': 'Localization/Peruvian',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'base_vat',
        'l10n_latam_base',
        'l10n_pe',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'data/ir_cron.xml',
    ],
    'images': ['static/description/banner.gif'],
}