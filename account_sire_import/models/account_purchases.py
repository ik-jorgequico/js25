# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class AccountPurchases(models.Model):
    _inherit = "account.purchases"
    _description = "Account Purchases for Sire Import"
    
    missing_taxes = []
    invalid_journals = []
    invalid_igvs = []
    
    lote_limit = fields.Integer('Lote', default=1000)
    
    # - STATIC METHODS
    @staticmethod
    def get_igv_rate(line):
        ratio = float(line.igv_dg) / float(line.base_dg)
        if 0.17 < ratio < 0.19:
            return 18.0
        elif 0.09 < ratio < 0.11:
            return 10.0
        # TODO: Falta obtener el %IGV para valores menores a 0.01
    
    @staticmethod
    def try_float(value):
        try:
            return float(value)
        except ValueError:
            return 0.0
    
    @staticmethod
    def find_account_move_by_ref(account_moves, ref):
        """
        Busca un asiento contable que tenga una referencia de pago coincidente con la proporcionada.
        """
        for move in account_moves:
            if move.payment_reference == ref or move.ref == ref:
                return move
        return None
    
    # - PRIVATE METHODS
    def _get_ref_list(self):
        if self._name == 'data.purchase':
            move_type = 'in_invoice'
            ref_field = 'ref'
        else:
            move_type = 'out_invoice'
            ref_field = 'payment_reference'
        
        ref_list = self.env["account.move"].search([
            ('company_id', '=', self.company_id.id),
            ('move_type', '=', move_type)
        ]).mapped(ref_field)
        
        return ref_list
    
    def _filter_moves(self, sire_data):
        """
        Filtra los lines del SIRE que no están en `account_move`
        de tipo `account_type` a través de su referencia.
        """
        ref_list = self._get_ref_list()
        
        def _filter(line):
            ref = f'{line.serie_cpe}-{str(line.num_cpe).zfill(8)}'
            return ref not in ref_list
        
        return sire_data.filtered(_filter)
    
    def _validate_lines(self):
        if self.missing_taxes:
            pairs = "\n - ".join(f"{tax_type} - {igv_amount}%{' (Precio incluído)' if price_include else ''}" for tax_type, igv_amount, price_include in set(self.missing_taxes))
            raise ValidationError(f"No se encontraron los siguientes impuestos de tipo {'compra' if self._name == 'data.purchase' else 'venta'}:\n - {pairs}")
        
        if self.invalid_journals:
            names = "\n - ".join(journal_name for journal_name in set(self.invalid_journals))
            raise ValidationError(f"Los siguientes diarios no tienen cuenta predeterminada:\n - {names}")
        
        if self.invalid_igvs:
            cars = "\n".join(car_sunat for car_sunat in set(self.invalid_igvs))
            print("Error al calcular los montos IGV: ", cars, flush=True)
            # TODO: mostrar en logger o agregar a una tabla de observaciones para no detener el proceso.
            # raise ValidationError(f'Error al calcular los montos IGV, revise (car_sunat): \n{cars}')
    
    def _clear_errors(self):
        self.missing_taxes.clear()
        self.invalid_journals.clear()
        self.invalid_igvs.clear()
    
    # - GENERATORS
    def get_cpe_codes_banned(self):
        """ Tipos de documentos que no se toman en cuenta en la extracción de la data de SIRE
        """
        return ['07', '91']
    
    # - INHERIT METHODS
    def get_sire_data(self, type_cpe_list=None, banned_method=False):
        """
        Busca los datos del SIRE del modelo seleccionado `_res_model`.\n
        Se puede filtrar por `type_cpe` si se pasa la lista `type_cpe_list`.\n
        Si `banned_method` es `True`, se eliminan los lines de la lista; si es `False` se obtienen solo los de la lista.
        """
        domain = [
            ('company_ruc','=',self.company_id.vat),
            ('periodo','=',self.period_name),
        ]
        
        if type_cpe_list:
            domain.append(('type_cpe', 'not in' if banned_method else 'in', type_cpe_list))
        
        self._validate_inheritances_sire()
        
        sire_data = self.env[self._res_model].search(domain)
        sire_data_filtered = self._filter_moves(sire_data)
        
        return sire_data_filtered
    
    # - MAIN METHODS
    def get_identification_type(self, name):
        identification_type_id = self.env['l10n_latam.identification.type'].search([('name', '=', name)], limit=1)
        if not identification_type_id:
            raise ValidationError("No se encontró el tipo de identificación %s" % name)
        return identification_type_id
    
    def get_partner(self, vats, identification_type_name, name, company_type):
        identification_type_id = self.get_identification_type(identification_type_name)
        
        if name in ("-"):
            name = "CLIENTES VARIOS"
            vats = "00000000" if company_type == "person" else "00000000000"
        
        res_partner = self.env['res.partner']
        partner_id = res_partner.search([
            ('vat', 'in' if type(vats) is list else "=", vats),
            ('l10n_latam_identification_type_id', '=', identification_type_id.id),
        ], limit=1)
        
        if not partner_id:
            partner_id = res_partner.create({
                'name': name,
                'company_type': company_type,
                'l10n_latam_identification_type_id': identification_type_id.id,
                'vat': vats[1] if type(vats) is list else vats,
            })
        
        return partner_id
    
    def get_type_ids(self, data):
        sire_type_cpe_list = list(set(x.zfill(2) for x in data.mapped("type_cpe")))
        document_types = self.env['l10n_latam.document.type'].search([('code','in',sire_type_cpe_list)])
        
        type_ids = {}
        for doc in document_types:
            key = doc.code
            if key not in type_ids.keys():
                type_ids.update({key: doc.id})
        
        missing_codes = set(sire_type_cpe_list) - set(type_ids.keys())
        if missing_codes:
            raise UserError('No se encontraron los tipos de documento: %s' % ', '.join(missing_codes))
        
        return type_ids
    
    def get_journal_ids(self, data):
        serie_cpe_list = list(set(x for x in data.mapped("serie_cpe")))
        type_cpe_list = list(set(x for x in data.mapped("type_cpe")))
        journals = self.env['account.journal'].search([
            ('company_id','=',self.company_id.id),
            ('type','=','sale'),
            ('code','in',serie_cpe_list),
            ('l10n_latam_document_type_id.code','in',type_cpe_list),
        ])
        
        journal_ids = ({(journal.code, journal.l10n_latam_document_type_id.id): journal for journal in journals})
        
        return journal_ids
    
    def get_currency_ids(self, data):
        void_currencies = tuple(set(x.car_sunat for x in data if x.currency == ""))
        
        if void_currencies:
            # TODO: Agregar esto a una tabla de observaciones
            print("Los siguientes registros de SIRE no tienen moneda (CAR Sunat):\n%s" % '\n'.join(void_currencies), flush=True)
        
        sire_currency_ids = tuple(set(x for x in data.mapped("currency") if x))
        currencies = self.env['res.currency'].search([('name', 'in', sire_currency_ids)])
        currency_ids = {curr.name: curr.id for curr in currencies}
        
        missing_currencies = set(sire_currency_ids) - set(currency_ids.keys())
        if missing_currencies:
            raise ValidationError("No se encontraron las monedas: %s" % ', '.join(missing_currencies))
        
        inactive_currencies = [curr.name for curr in currencies if not curr.active]
        if inactive_currencies:
            raise ValidationError("Las siguientes monedas no están activas: %s" % ', '.join(inactive_currencies))
        
        return currency_ids
    
    def prepare_invoice_lines(self, account_type: str, line, tax_rel, journal_id):
        def is_price_include(line):
            return bool(
                self.try_float(line.base_dg) and self.try_float(line.igv_dg) and 
                self.try_float(line.expo) == 0 and self.try_float(line.desc_base_dg) == 0 and 
                self.try_float(line.exonerado) == 0 and self.try_float(line.inafecto) == 0 and 
                self.try_float(line.isc) == 0 and self.try_float(line.base_ivap) == 0 and 
                self.try_float(line.ivap) == 0 and self.try_float(line.otros) == 0
            )
        
        invoice_line_ids = []
        for tax_type, amount, tax_code in tax_rel:
            igv_amount = 0
            price_include = False
            price_unit = self.try_float(amount)
            
            if price_unit == 0:
                continue
            
            tax_domain = [
                (f'type_{account_type}_ple', '=', tax_type),
                ('tax_group_id.name', '=', tax_type),
                ('type_tax_use', '=', 'sale'),
                ('company_id', '=', self.company_id.id),
            ]
            
            if tax_code in [1, 2]:
                if tax_code == 1:
                    igv_amount = self.get_igv_rate(line)
                
                    if igv_amount is None:
                        self.invalid_igvs.append((line.car_sunat))
                        continue
                
                if tax_type == 'VG':
                    price_include = is_price_include(line)
                
                    if price_include:
                        price_unit = round(self.try_float(line.total_cpe), 2)
                
                tax_domain = [
                    ('amount', '=', igv_amount),
                    ('tax_group_id.name', '=', 'IGV' if tax_code == 1 else tax_type),
                    ('type_tax_use', '=', account_type),
                    ('company_id', '=', self.company_id.id),
                ]
                
                if tax_code == 1:
                    tax_domain.append(('price_include', '=', price_include))
                    tax_domain.append((f'type_{account_type}_ple', '=', tax_type))
            
            tax = self.env['account.tax'].search(tax_domain, limit=1)
            if not tax:
                self.missing_taxes.append((tax_type, igv_amount, price_include))
                continue
            
            if line.currency != self.company_id.currency_id.name:
                price_unit = round(price_unit / self.try_float(line.exchange), 2)
            
            account_id = journal_id.default_account_id
            
            if not account_id:
                self.invalid_journals.append(journal_id.name)
                continue
            
            invoice_line_ids.append((0, 0, {
                'name': 'Registrado con información del Sire',
                'account_id': account_id.id,
                'quantity': 1.0,
                'price_unit': price_unit,
                'tax_ids': [(6, 0, [tax.id])],
            }))
        
        return invoice_line_ids
    
    def create_credit_note(self, sire_line_id, invoice_id):
        """ Lógica para procesar la nota de crédito con el asiento contable proporcionado.
        """
        wizard_id = self.env['account.move.reversal'].create({
            'reason': 'Refacturación',
            'move_ids': [invoice_id.id],
            'move_type': invoice_id.move_type,
            #'refund_method': 'refund',
            'journal_id': invoice_id.journal_id.id,
            'date': datetime.strptime(sire_line_id.invoice_date, "%d/%m/%Y"),
            #'date_mode': 'custom',
        })
        
        action = wizard_id.reverse_moves()
        
        nc_id = self.env['account.move'].browse(action.get("res_id"))
        
        serie_cpe = sire_line_id.serie_cpe
        num_cpe = str(sire_line_id.num_cpe).zfill(8)
        
        nc_id.seriecomp_sunat = serie_cpe
        nc_id.numcomp_sunat = num_cpe
        
        if self._name == 'data.sales':
            ref = f'{serie_cpe}-{num_cpe}'
            nc_id.name = ref
            nc_id.payment_reference = ref
        
        if self._name == 'data.purchase':
            nc_id.l10n_pe_edi_reversal_serie = sire_line_id.serie_cpe_nc
            nc_id.l10n_pe_edi_reversal_number = sire_line_id.num_cpe_nc
            nc_id.l10n_pe_edi_reversal_date = datetime.strptime(sire_line_id.invoice_date_nc, '%d/%m/%Y')
        
        #sire_line_id.move_id = invoice_id.id
        
        return nc_id
    
    def add_credit_notes_sire(self):
        account_move_ids = self.env['account.move'].search([
            ('company_id','=',self.company_id.id),
            ('state','=','posted'),
        ])
        
        nc_sire_line_ids = self.get_sire_data(['07'])
        for sire_line_id in nc_sire_line_ids:
            invoice_ref = f"{sire_line_id.serie_cpe_nc}-{str(sire_line_id.num_cpe_nc).zfill(8)}"
            invoice_id = self.find_account_move_by_ref(account_move_ids, invoice_ref)
            if invoice_id:
                self.create_credit_note(sire_line_id, invoice_id)
    
    def process_from_batch(self, data_prepared: list):
        """ Divide la data por lotes definido por `lote_limit` y lo procesa.
        """
        for start in range(0, len(data_prepared), self.lote_limit):
            batch = data_prepared[start:start + self.lote_limit]
            accounts = self.env['account.move'].create(batch)
            
            if self._name == 'data.purchase':
                accounts._get_doc_cpe()
            
            # Commit cada vez que se alcanza el límite establecido en Advanced Page
            self.env.cr.commit()
    
    def get_sire_data_prepared(self, data) -> list:
        return []
    
    def import_from_sire(self):
        list_banned = self.get_cpe_codes_banned()
        sire_data = self.get_sire_data(list_banned, banned_method=True)
        data_prepared = self.get_sire_data_prepared(sire_data)
        self.process_from_batch(data_prepared)
    
