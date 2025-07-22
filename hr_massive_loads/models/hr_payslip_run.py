# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime
import pandas as pd
from io import BytesIO
import base64


MONTH_SELECTION = [
    ('01', 'Enero'),
    ('02', 'Febrero'),
    ('03', 'Marzo'),
    ('04', 'Abril'),
    ('05', 'Mayo'),
    ('06', 'Junio'),
    ('07', 'Julio'),
    ('08', 'Agosto'),
    ('09', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
]

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Batches'
    
    attachment_ids = fields.Many2many('ir.attachment', string='Subir archivo')
    
    @api.constrains('attachment_ids')
    def _check_single_attachment(self):
        for rec in self:
            if len(rec.attachment_ids) > 1:
                raise ValidationError('Solo se permite subir un archivo.')
            for attachment in rec.attachment_ids:
                if not any(attachment.name.endswith(ext) for ext in ['.xls', '.xlsx']):
                    raise ValidationError('Solo está permitida la carga de archivos Excel (.xls, .xlsx).')
            
    def upload_data(self):
        self.ensure_one()
        
        if not self.attachment_ids:
            raise ValidationError('Debe subir un archivo para cargar las entradas.')
        
        attachment = self.attachment_ids[0]
        file_content = base64.b64decode(attachment.datas)
        excel_data = pd.read_excel(BytesIO(file_content),dtype=str)
        
        data = {}
        for _, row in excel_data.iterrows():
            row_dict = row.to_dict()
            
            dni = str(row_dict.get('dni'))
            amount = float(row_dict.get('monto'))
            
            if amount:
                entry = {
                    'input': row_dict['input'],
                    'amount': amount,
                }
                if dni in data.keys():
                    data[dni].append(entry)
                else:
                    data[dni] = [entry]
        
        hrPayslip = self.env['hr.payslip']
        hrPayslipInputType = self.env['hr.payslip.input.type']
        
        for dni, lines in data.items():
            payslip = hrPayslip.search([
                ('payslip_run_id', '=', self.id),
                ('employee_id.identification_id', '=', dni),
            ], limit=1)
            
            input_type_ids = [x.input_type_id.id for x in payslip.input_line_ids]
            
            for line in lines:
                input_type_id = hrPayslipInputType.search([('name', '=', line['input'])], limit=1).id
                amount = line['amount']
                
                if input_type_id in input_type_ids:
                    input_line = payslip.input_line_ids.filtered(lambda x: x.input_type_id.id == input_type_id)
                    input_line.amount = amount
                else:
                    payslip.input_line_ids = [(0, 0, {
                        'input_type_id': input_type_id,
                        'amount': amount,
                    })]
            
            payslip.compute_sheet()