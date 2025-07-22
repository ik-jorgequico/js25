# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Excel Report Plus",
    'version': '0.2',
    'description': """Añade la compatibilidad para generar reportes en el formato Excel (.xlsx)""",
    'author': 'SystemOuts',
    'sequence': '-1',
    'depends': [
        'base',
        'web',
    ],
    "external_dependencies": {"python": ["openpyxl"]},
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
