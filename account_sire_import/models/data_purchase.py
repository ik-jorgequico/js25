# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError
from datetime import datetime


class DataPurchase(models.Model):
    _inherit = 'data.purchase'
    _description = 'Data Purchase for Import SIRE'
    
    def _default_journal_id(self):
        journal_id = self.env['account.journal'].search([
            ('company_id', '=', self.env.company.id),
            ('type', '=', 'purchase'),
        ], limit=1)
        
        if not journal_id:
            raise ValidationError("No se encontró un Diario de tipo 'purchase' para la compañía %s" % self.company_id.name)
        
        return journal_id.id
    
    journal_id = fields.Many2one('account.journal', 'Diario de Compras', default=_default_journal_id)
    
    # - PRIVATE METHODS
    def _get_tax_relation(self, line):
        return [
            # (tax_type, amount, tax_code),
            ('AG-VG', line.base_dg, 1),
            ('AG-VGNG', line.base_dgng, 1),
            ('AG-NO', line.base_dng, 1),
            ('INA', line.inafecto, 2),
            ('OTROS', line.otros, 2),
        ]
    
    def _prepare_in_invoice(self, sire_data, type_ids, currency_ids):
        self._clear_errors()
        
        vals = []
        print("Preparando registros desde SIRE...", flush=True)
        for line in sire_data:
            partner_id = self.get_partner(line.vendor_doc, 'RUC', line.vendor_name, 'company')
            type_id_id = type_ids.get(str(line.type_cpe).zfill(2))
            currency_id_id = currency_ids.get(line.currency)
            
            tax_rel = self._get_tax_relation(line)
            invoice_line_ids = self.prepare_invoice_lines('purchase', line, tax_rel, self.journal_id)
            
            if not invoice_line_ids or not currency_id_id:
                # TODO: Guardar los lines con errores para mostrarlo en una tabla.
                continue
            
            val = {
                "move_type": "in_invoice",
                "partner_id": partner_id.id,
                "l10n_latam_document_type_id": type_id_id,
                "seriecomp_sunat": line.serie_cpe,
                "numcomp_sunat": line.num_cpe,
                "invoice_date": datetime.strptime(line.invoice_date, "%d/%m/%Y"),
                "date": self.first_and_last_day(month=line.periodo[4:], year=line.periodo[:4])[1],
                "journal_id": self.journal_id.id,
                "currency_id": currency_id_id,
                "glosa_sunat": "Registrado con información del Sire",
                "invoice_line_ids": invoice_line_ids,
            }
            
            if str(line.type_cpe).zfill(2) == '08':  # Debit note
                s_cpe = line.serie_cpe_nc or line.serie_cpe
                num_cpe = line.num_cpe_nc or line.num_cpe
                date = datetime.strptime(line.invoice_date_nc or line.invoice_date, "%d/%m/%Y") 
                ref_origin = f"{s_cpe}-{str(num_cpe).zfill(8)}"
                val.update({
                    "l10n_pe_edi_reversal_serie": s_cpe,
                    "l10n_pe_edi_reversal_number": num_cpe,
                    "l10n_pe_edi_reversal_date": date,
                    "reversal_type": str(line.type_cpe_nc).zfill(2),
                    "glosa_sunat": f"DEBITO {ref_origin}",
                })
            
            vals.append(val)
        
        self._validate_lines()
        
        return vals
    
    # - INHERITED METHODS
    def get_cpe_codes_banned(self):
        records =  super().get_cpe_codes_banned()
        # 30 - son documentos emitidos por emisores de tarjeta de crédito
        records.extend(['30', '50', '53', '54'])
        return records
    
    def get_sire_data_prepared(self, data):
        type_ids = self.get_type_ids(data)
        currency_ids = self.get_currency_ids(data)
        return self._prepare_in_invoice(data, type_ids, currency_ids)
    
