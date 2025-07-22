# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import UserError
from fuzzywuzzy import process
from .sunat_ruc import SunatRuc, SunatLegalRepresentative
from typing import List
import requests


STATE_SELECTION = [
    (x, x) for x in [
        'ACTIVO',
        'BAJA DE OFICIO',
        'BAJA DEFINITIVA',
        'BAJA PROVISIONAL',
        'SUSPENSION TEMPORAL',
        'INHABILITADO-VENT.UN',
        'BAJA MULT.INSCR. Y O',
        'PENDIENTE DE INI. DE',
        'OTROS OBLIGADOS',
        'NUM. INTERNO IDENTIF',
        'ANUL.PROVI.-ACTO ILI',
        'ANULACION - ACTO ILI',
        'BAJA PROV. POR OFICIO',
        'ANULACION - ERROR SU',
    ]
]

CONDITION_SECTION = [
    (x, x) for x in [
        'HABIDO',
        'NO HABIDO',
        'NO HALLADO',
        'NO HALLADO SE MUDO D',
        'NO HALLADO NO EXISTE',
        'NO HALLADO FALLECIO',
        'NO HALLADO OTROS MOT',
        'NO HALLADO NRO.PUERT',
        'NO HALLADO CERRADO',
        'NO HALLADO DESTINATA',
        'NO HALLADO RECHAZADO',
        'NO APLICABLE',
        'POR VERIFICAR',
        'PENDIENTE',
    ]
]

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Add fields for information of RUC Sunat'
    
    state = fields.Selection(STATE_SELECTION, "Partner State", default="ACTIVO")
    condition = fields.Selection(CONDITION_SECTION, 'Condition')
    is_agent_retentions = fields.Boolean('¿Es agente de retención?', readonly=True, store=True)
    is_good_contributor = fields.Boolean('¿Es buen contribuyente?', readonly=True, store=True)
    
    contact_identification_type = fields.Char("Tipo de Identificación")
    contact_vat = fields.Char("NIF/Identificación fiscal")
    contact_from_date = fields.Date("Fecha desde")
    padron_1 = fields.Char(readonly=True, store=True)
    padron_2 = fields.Char(readonly=True, store=True)
    padron_3 = fields.Char(readonly=True, store=True)
    
    # PRIVATE METHODS
    def _get_state_id_from_domicile(self, domicile: str, country_id_id: int):
        state_ids = self.env['res.country.state'].search([('country_id','=',country_id_id)])
        state_names = [state.name for state in state_ids]
        words = domicile.split()
        for i in range(1, len(words) + 1):
            match = process.extractOne(" ".join(words[-i:]), state_names)
            if match and match[1] > 80:
                return state_ids.filtered(lambda s: s.name == match[0])
    
    def _fill_address_data(self, full_domicile: str):
        if full_domicile.strip() == "-":
            return
        parts = full_domicile.split("-")
        domicile = str(parts[0]).strip()
        city = str(parts[1]).strip()
        district = str(parts[2]).strip()
        
        country_id = self.env['res.country'].search([('code','=','PE')])
        state_id = self._get_state_id_from_domicile(domicile, country_id.id)
        city_id = self.env['res.city'].search([('name','ilike',city),('country_id','=',country_id.id)], limit=1)
        district_id = self.env['l10n_pe.res.city.district'].search([('name','ilike',district),('city_id','=',city_id.id)], limit=1)
        
        self.street = domicile.upper().replace(state_id.name.upper() if state_id else "", "").strip()
        self.city_id = city_id
        self.state_id = state_id
        self.country_id = country_id
        self.l10n_pe_district = district_id
        self.zip = district_id.code
        
    def _clear_patters(self):
        self.padron_1 = self.padron_2 = self.padron_3 = False
    
    def _fill_patters(self, patters):
        if len(patters) >= 1:
            self.padron_1 = patters[0]
        if len(patters) >= 2:
            self.padron_2 = patters[1]
        if len(patters) >= 3:
            self.padron_3 = patters[2]
    
    def _fill_legal_representatives(self, legal_representatives: List[SunatLegalRepresentative]):
        """
        Sincroniza los representantes legales de la compañía con la lista proporcionada. 
        Elimina representantes que ya no están en legal_representatives y agrega los nuevos.
        """
        if self.is_company and legal_representatives:
            current_representatives = {child.name: child for child in self.child_ids}
            new_representatives = {rep.name.strip(): rep for rep in legal_representatives}
            
            to_remove = [
                child.id for name, child in current_representatives.items()
                if name not in new_representatives
            ]
            if to_remove:
                self.child_ids = [(3, rep_id) for rep_id in to_remove]
            
            to_add = []
            for name, rep in new_representatives.items():
                if name not in current_representatives:
                    to_add.append({
                        'parent_id': self.id,
                        'name': name,
                        'function': rep.position,
                        'type': 'contact',
                        'contact_identification_type': rep.document_type,
                        'contact_vat': rep.num_doc,
                        'display_name': f'{self.name}, {name}',
                        'is_company': False,
                        'commercial_partner_id': self.id,
                        'commercial_company_name': self.name,
                        'contact_from_date': rep.date_from,
                    })
            
            if to_add:
                self.child_ids = [(0, 0, val) for val in to_add]

    # INHERIT METHODS
    def _onchange_city_id(self):
        ''' Método heredado de `base_address_city` para colocar el zip correcto.
        '''
        res = super(ResPartner, self)._onchange_city_id()
        self.zip = self.l10n_pe_district.code
        return res
    
    # VALIDATIONS
    def validate_dni(self, num_dni):
        if len(num_dni) != 8:
            raise UserError(_('The DNI entered is incorrect'))
    
    def validate_ruc(self, num_ruc):
        if not num_ruc.isdigit():
            raise UserError(f"El número de RUC '{num_ruc}' debería tener solo caracteres numéricos.")
        
        ruc_len = len(num_ruc)
        if not ruc_len == 11:
            raise UserError(f"El número de RUC '{num_ruc}' tiene {ruc_len} {'caracter' if ruc_len == 1 else 'caracteres'} y debería tener 11 caracteres.")
    
    # ONCHANGES
    @api.onchange('company_type')
    def _onchange_company_type(self):
        if not self.vat:
            self.l10n_latam_identification_type_id = self.env['l10n_latam.identification.type'].search([
                ('name', '=', 'DNI' if self.company_type == 'person' else 'RUC'),
            ], limit=1)
    
    @api.onchange('vat', 'l10n_latam_identification_type_id')
    def onchange_doc_number(self):
        vat_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
        
        if self.vat and vat_type:
            if vat_type == '1':
                self.consult_dni(self.vat)
            elif vat_type == "6":
                self.consult_ruc(self.vat)
    
    # MAIN METHODS
    @api.model
    def consult_dni(self, num_dni):
        self.validate_dni(num_dni)
        
        result = requests.get(f'https://api.apis.net.pe/v1/dni?numero={num_dni}')
        
        if result.status_code == 404:
            raise UserError(_('DNI not found.'))
        
        json = result.json()
        names = str(json['nombres'])
        pat_surname = str(json['apellidoPaterno'])
        mat_surname = str(json['apellidoMaterno'])
        
        self.name = f"{names} {pat_surname} {mat_surname}"
    
    @api.model
    def consult_ruc(self, num_ruc):
        self._clear_patters()
        self.validate_ruc(num_ruc)

        sunat_ruc = SunatRuc(num_ruc)
        self.name = sunat_ruc.company_name
        
        if 'BAJA DE OFICIO' in sunat_ruc.taxpaper_state:
            tax_state = 'BAJA DE OFICIO'
        else: 
            tax_state = sunat_ruc.taxpaper_state

        self.state = tax_state
        self.condition = sunat_ruc.taxpaper_condition
        self._fill_address_data(sunat_ruc.tax_domicile)
        self._fill_patters(sunat_ruc.patters)
        self._fill_legal_representatives(sunat_ruc.legal_representatives)
        self.is_agent_retentions = self.env['agent.retention'].search_count([('ruc','=',num_ruc)]) > 0
        self.is_good_contributor = self.env['good.contributor'].search_count([('ruc','=',num_ruc)]) > 0
    
    # METHODS
    def update_document(self):
        self.onchange_doc_number()
    
