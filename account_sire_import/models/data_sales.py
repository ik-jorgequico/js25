# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class DataSales(models.Model):
    _inherit = "data.sales"
    _description = "Data Sales for Import SIRE"
    
    # - PRIVATE METHODS
    def _get_tax_relation(self, line):
        return [
            # (tax_type, amount, tax_code),
            ('EXP', line.expo, 0),
            ('VG', line.base_dg, 1),
            ('EXO', line.exonerado, 0),
            ('INA', line.inafecto, 0),
        ]
    
    def _check_customer(self, line):
        doc_types = {
            '1': ('DNI', 'person'),
            '7': ('Pasaporte', 'person'),
            '4': ('Cédula Extranjera', 'person'),
            '6': ('RUC', 'company')
        }
        
        if line.est_comp == '1':
            if line.type_doc == '1' and line.vendor_doc == '-' and line.vendor_name == 'Sin Nombre':
                return self.get_partner('99999999', 'DNI', 'Cliente Generico', 'person')
            elif line.type_doc in ['-', '0']:
                return self.get_partner(['99999999', '00000000'], 'DNI', 'Cliente Generico', 'person')
            elif line.type_doc in doc_types:
                doc_name, company_type = doc_types[line.type_doc]
                return self.get_partner(line.vendor_doc, doc_name, line.vendor_name, company_type)
            else:
                raise UserError(f'{line.type_doc} no se encontró tipo de documento en la lista (dni, pasaporte, ruc, ce) en facturas activas. Por favor, revise la configuración.')			
        
        elif line.est_comp == '2':
            if line.serie_cpe[0] in ['F', 'E'] and line.serie_cpe[:2] != 'EB':
                return self.get_partner(['99999999999', '00000000000'], 'RUC', 'Factura Anulada', 'company')
            elif line.serie_cpe[0] == "B" or line.serie_cpe[:2] == "EB":
                return self.get_partner(['99999999', '00000000'], 'DNI', 'Boleta Anulada', 'person')
            else:
                raise ValidationError(f'No se encontró la serie {line.serie_cpe} en facturas anuladas. Por favor, revise la configuración.')
        
        else:
            raise ValidationError(f'El estado del comprobante {line.car_sunat} no es soportado.')
    
    def _prepare_invoice_lines_miss(self, journal_id):
        tax_id = self.env['account.tax'].search([
            ('type_sale_ple', '=', 'VG'),
            ('price_include', '=', False),
            ('tax_group_id.name', '=', 'IGV'),
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        
        if not tax_id:
            raise UserError('No se encontró Impuesto IGV para la columna de ventas gravadas. Por favor, revise la configuración de impuestos.')
        
        invoice_lines = [(0, 0, {
            'name': 'Registrado con informacion del Sire',  # Etiqueta
            'account_id': journal_id.default_account_id.id,  # Cuenta
            'quantity': 1,  # Cantidad
            'price_unit': 0.00,  # Precio
            'tax_ids': [(6, 0, [tax_id.id])],  # Impuestos
        })]
        
        return invoice_lines
    
    def _prepare_out_invoice(self, sire_data, type_ids, currency_ids, journal_ids):
        self._clear_errors()
        
        vals = []
        missing_journals = []
        invalid_currencies = []
        void_currencies = []
        for line in sire_data:
            partner_id = self._check_customer(line)
            type_id_id = type_ids.get(str(line.type_cpe).zfill(2))
            journal_id = journal_ids.get((line.serie_cpe, type_id_id))
            
            if not journal_id:
                missing_journals.append((line.serie_cpe, line.type_cpe))
                continue
            
            if not line.currency:
                void_currencies.append((line.car_sunat, line.currency))
                continue
            
            currency_id_id = currency_ids.get(line.currency)
            if not currency_id_id:
                invalid_currencies.append((line.car_sunat, line.currency)) 
                continue
            
            if line.est_comp == "1":
                tax_rel = self._get_tax_relation(line)
                invoice_line_ids = self.prepare_invoice_lines('sale', line, tax_rel, journal_id)
            elif line.est_comp == "2":
                invoice_line_ids = self._prepare_invoice_lines_miss(journal_id)
            
            if not invoice_line_ids:
                # TODO: Guardar los que no tienen lines para mostrarlo en una tabla.
                continue
            
            payment_reference = f"{line.serie_cpe}-{str(line.num_cpe).zfill(8)}"
            invoice_date = datetime.strptime(line.invoice_date, '%d/%m/%Y')
            
            vals.append({
                'move_type': "out_invoice",
                'partner_id': partner_id.id,
                'l10n_latam_document_type_id': type_id_id,
                'payment_reference': payment_reference,
                'ref': payment_reference,
                'invoice_date': invoice_date,
                'date': invoice_date,
                'journal_id': journal_id.id,
                'glosa_sunat': 'Registrado con información del Sire',
                'currency_id': currency_id_id,
                'invoice_line_ids': invoice_line_ids,
            })
        
        if missing_journals:
            pairs = "\n".join(f"({serie_cpe}, {type_cpe})" for serie_cpe, type_cpe in set(missing_journals))
            raise ValidationError(f'No se encontraron los diarios (serie, tipo):\n{pairs}')
        
        if void_currencies:
            pairs = "\n".join(f"({car}, {val})" for car, val in set(void_currencies))
            print(f'Monedas vacías (car_sunat, currency):\n{pairs}', flush=True)
        
        if invalid_currencies:
            pairs = "\n".join(f"({car}, {val})" for car, val in set(invalid_currencies))
            raise ValidationError(f'Monedas inválidas (car_sunat, currency):\n{pairs}')
        
        self._validate_lines()
        
        return vals
    
    # - INHERITED METHODS
    def get_cpe_codes_banned(self):
        records =  super().get_cpe_codes_banned()
        records.extend(['00'])
        return records
    
    def get_sire_data_prepared(self, data):
        type_ids = self.get_type_ids(data)
        currency_ids = self.get_currency_ids(data)
        journal_ids = self.get_journal_ids(data)
        return self._prepare_out_invoice(data, type_ids, currency_ids, journal_ids)
    