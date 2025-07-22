# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class AccountPurchases(models.Model):
    _inherit = "account.purchases"
    _description = "Account Purchases"
    _res_model = ""
    
    child_ids = False
    
    period_name = fields.Char("Periodo", compute='_compute_period_name',store=True)
    limit_errors = fields.Integer("Limite de errores 0.01", default=2)
    
    sire_replace_filename = fields.Char('Nombre archivo para reemplazar sire')
    sire_replace_binary = fields.Binary('Reemplazar Sire')
    
    # - COMPUTES
    @api.depends("month", "year")
    def _compute_period_name(self):
        for rec in self:
            rec.period_name = rec.year + rec.month
    
    # - STATIC METHODS
    @staticmethod
    def _match_domain(record, domain):
        """ Comprueba si un registro cumple con un dominio en memoria.
        """
        for condition in domain:
            field, operator, value = condition
            record_value = getattr(record, field, None)
            
            if operator == '=' and record_value != value:
                return False
            elif operator == 'in' and record_value not in value:
                return False
            elif operator == 'not in' and record_value in value:
                return False
            elif operator == '!=' and record_value == value:
                return False
        
        return True
    
    # - PRIVATE METHODS
    def _validate_inheritances_sire(self):
        if self.env.context.get('sire_context'):
            if not self._res_model:
                raise ValidationError(f'Debe heredar "_res_model" en {self._name}.')
            if self.child_ids == False:
                raise ValidationError(f'Debe crear el campo "child_ids" en {self._name}.')
    
    def _validate_data_sire(self):
        self._validate_inheritances_sire()
        domain = self.sire_domain()
        sire_count = self.env[self._res_model].search_count(domain)
        
        if not sire_count:
            raise UserError("Aún no se ha cargado el SIRE.\nPresione el botón 'Importar SIRE' en la página 'SIRE'.")
        
        # TODO: Comparar la cuenta de registro con el más actualizado. Consultar el último SIRE disponible en SUNAT.
        # Si es diferente, mostrar una alerta para indicar que debe importar nuevamente el SIRE.
        
        return sire_count
    
    # - GENERATORS
    def validate_sire_domain(self, line):
        l_total_cpe = self.get_list_nums(line.total_amount)
        l_inafecto = self.get_list_nums(line.inafecto)
        
        return [
            ('car_sunat','=',line.car_odoo),
            ('invoice_date','=',line.invoice_date.strftime('%d/%m/%Y')),
            ('currency','=',line.currency_line or ''),
            ('exchange','=',"%.3f" % (line.tc_sunat or 0.0)),
            ('inafecto','in',l_inafecto),
            ('total_cpe','in',l_total_cpe),
        ]
    
    def sire_domain(self):
        return [
            ('company_ruc','=',self.company_id.vat),
            ('periodo','=',self.period_name),
        ]
    
    # - MAIN METHODS
    def get_list_nums(self, num: float) -> list:
        numbers = set()
        
        def add_variants(n):
            numbers.add(f"{n:.2f}")  # TODO: Podría colocarse un campo en Advanced para manejarlo en la interfaz
            if n.is_integer():
                numbers.add(f"{int(n)}")  # Añadir versión entera si es .00
            if f"{n:.2f}".endswith("0"):
                numbers.add(f"{n:.1f}")  # Añadir versión con un decimal si es .X0
        
        # Añadir variantes del número original
        add_variants(num)
        
        # Añadir variantes para las sumas y restas
        for i in range(1, self.limit_errors + 1):
            add_variants(num + i * 0.01)
            add_variants(num - i * 0.01)
        
        return tuple(numbers)
    
    def get_filename_sire(self, book_code: str) -> str:
        year = self.year
        month = self.month
        company_vat = self.company_id.vat or '99999999999'
        type_book_code = book_code
        ind_o = self.indicator_o
        ind_i = self.indicator_c
        ind_m = self.indicator_m
        ind_g = "2"  # codigo que significa que se hizo para el Sire, 1 es para el Ple

        filename = f'LE{company_vat}{year}{month}{type_book_code}{ind_o}{ind_i}{ind_m}{ind_g}'
        return filename
    
    # - BUTTONS
    def button_sire(self):
        self.ensure_one()
        self._validate_inheritances_sire()
        
        return {
            'name': 'Sire',
            'res_model': self._res_model,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [
                ('company_ruc','=',self.company_id.vat),
                ('periodo','=',self.period_name),
            ],
        }
    
    def compute_sheet(self):
        rec = super(AccountPurchases, self).compute_sheet()
        
        if self.env.context.get('sire_context'):
            self._validate_inheritances_sire()
            domain = self.sire_domain()
            sire_data = self.env[self._res_model].search(domain)
            sire_data.sire_check = 'pending'
        
        return rec
    
    def validate_sire(self):
        self._validate_data_sire()
        
        sire_domain = self.sire_domain()
        sire_records = self.env[self._res_model].search(sire_domain)
        
        for line in self.child_ids:
            domain = self.validate_sire_domain(line)
            sire_line = next((rec for rec in sire_records if self._match_domain(rec, domain)), None)
            
            if sire_line:
                line.sire_check = sire_line.sire_check = 'checked'
            else:
                line.sire_check = 'not_found'
    
    def action_sire_replace(self):
        pass
    

class AccountPurchasesLine(models.Model):
    _inherit = "account.purchases.line"
    _description = "Account Purchases Line for SIRE"
    
    car_odoo = fields.Char("CAR Odoo", compute='_compute_car_odoo')
    sire_check = fields.Selection([
        ('pending', 'Pendiente'),
        ('not_found', 'No Encontrado'),
        ('checked', 'Validado'),
    ], "Estado SIRE", default='pending', store=True)
    
    def _compute_car_odoo(self):
        for rec in self:
            rec.car_odoo = ""