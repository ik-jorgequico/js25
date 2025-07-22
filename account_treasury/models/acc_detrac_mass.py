from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import  timedelta, datetime, date
import base64
import logging
import pandas as pd
from io import BytesIO

_logger = logging.getLogger(__name__)

class AccDetracMass(models.Model):
    _name = 'acc.detrac.mass'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Detracciones masivas'
    
    name = fields.Char("Nombre",store=True,copy=False)
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company,store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Aprobado'),
        ('cancel', 'Cancelado'),
    ], "Status", default='draft', tracking=True,store=True)
    correlative = fields.Integer("Correlativo", default=1, compute="_compute_correlative", store=True)
    journal_id = fields.Many2one('account.journal', "Diario de Pago",tracking=True,store=True)
    # file_import = fields.Binary("Archivo a importar",store=True)
    payment_date = fields.Date("Fecha de Pago",tracking=True,store=True)
    line_ids = fields.One2many("acc.detrac.mass.line", "parent_id", "Detracciones Masivas")
    file_name = fields.Char(string='Nombre archivo txt',tracking=True,store=True)
    file_binary = fields.Binary(string='Archivo txt',store=True)
    lote = fields.Char('Lote',compute="_compute_correlative",tracking=True,store=True)
    total = fields.Integer('Pago total',compute='_compute_pay_total',tracking=True,store=True)
    payment_ids = fields.One2many('account.payment','det_mass_id', tracking=True,string="Ids Pagos")
    excel_to_upload_ids = fields.Many2many('ir.attachment',string='Subir archivo')
    warning = fields.Char('Errores',tracking=True,store=True)

    def action_upload_data(self):
        errors = self._upload_data()
        if errors:
            self.warning = ' | \n'.join(errors)

    @api.constrains('excel_to_upload_ids')
    def _check_single_attachment(self):
        for rec in self:
            if len(rec.excel_to_upload_ids) > 1:
                raise ValidationError('Solo se permite subir un archivo.')
            for attachment in rec.excel_to_upload_ids:
                if not any(attachment.name.endswith(ext) for ext in ['.xls', '.xlsx', '.csv']):
                    raise ValidationError('Solo está permitida la carga de archivos Excel (.xls, .xlsx).')
            
    def _upload_data(self):
        self.ensure_one()
        
        if not self.excel_to_upload_ids:
            raise ValidationError('Debe subir un archivo para cargar las entradas.')
        
        attachment = self.excel_to_upload_ids[0]
        file_content = base64.b64decode(attachment.datas)
        if any(attachment.name.endswith(ext) for ext in ['.xls', '.xlsx']):
            excel_data = pd.read_excel(BytesIO(file_content),dtype=str)
        if any(attachment.name.endswith(ext) for ext in ['.csv']):
            excel_data = pd.read_csv(BytesIO(file_content),dtype=str)

        errors = []
        contador = 0
        for _, row in excel_data.iterrows():
            row_dict = row.to_dict()

            if str(row_dict.get('Numero de Documento Adquiriente')) != self.company_id.vat:
                raise ValidationError('La empresa no coincide con el ruc del archivo excel.')
            
            numero_constancia = str(row_dict.get('Numero Constancia'))
            fecha_pago = str(row_dict.get('Fecha Pago'))
            ruc_proveedor = str(row_dict.get('RUC Proveedor'))
            nombre_proveedor = str(row_dict.get('Nombre Proveedor'))
            tipo_cpe = str(row_dict.get('Tipo de Comprobante'))
            serie_cpe = str(row_dict.get('Serie de Comprobante'))
            numero_cpe = str(row_dict.get('Numero de Comprobante'))

            if numero_constancia:
                move = self.env['account.move'].search([
                    ('move_type', '=', 'in_invoice'),
                    ('state', '=', 'posted'),
                    ('partner_id.vat', '=', ruc_proveedor),
                    ('l10n_latam_document_type_id.code', '=', tipo_cpe.zfill(2)),
                    ('seriecomp_sunat', '=', serie_cpe),
                    ('numcomp_sunat', '=', numero_cpe.zfill(8)),
                    ])
                if move:
                    date_pago = datetime.strptime(fecha_pago, '%d/%m/%Y')
                    move.write({
                        'num_det': numero_constancia,
                        'date_det': date_pago,
                        })
                else:
                    contador += 1
                    vals = f"error {contador}: {ruc_proveedor},{nombre_proveedor[:20]},{tipo_cpe},{serie_cpe},{numero_cpe}"
                    errors.append(vals)
        return errors

    def _create_payments(self):
        for rec in self:
            aml = self.env['account.move.line']
            payment = self.env['account.payment'].create({
                'ref': f"Pago detraccion Lote: {rec.lote}",
                'amount': rec.total,
                'currency_id': rec.company_id.currency_id.id,
                'journal_id': rec.journal_id.id,
                'date': rec.payment_date,
                'det_mass_id': rec.id,
                'payment_method_id': rec.journal_id.outbound_payment_method_line_ids.mapped('payment_method_id').ids[0],
                'payment_type':'outbound',
            })
            payment.action_post()
            move = payment.move_id
            move.button_draft()
            ids_to_reconcile = []
            detraction_to_reconcile_ids = rec.line_ids.mapped('detraction_id').ids
            ids_to_reconcile.extend(detraction_to_reconcile_ids)
            account_det = self.env['account.journal'].search([('company_id','=',rec.company_id.id),('is_detraction','=',True)],limit=1).account_det.id
            move.line_ids.filtered_domain([('debit','>',0)]).with_context(check_move_validity=False).unlink()
            debit_move_id = aml.with_context(check_move_validity=False).create({
                        'name': f"Pago detraccion Lote: {rec.lote}",
                        'account_id': account_det,
                        'currency_id': self.company_id.currency_id.id,
                        'amount_currency': rec.total,
                        'credit': 0.0,
                        'move_id': move.id,
                        'debit': rec.total,
                        'ref': f"Pago detraccion Lote: {rec.lote}",
                    })
            move.action_post()
            ids_to_reconcile.append(debit_move_id.id)
            aml.browse(ids_to_reconcile).reconcile()
            
    def _fill_spaces(self,character:str,large:int,position:str='l',data:str = None):
        """
        character, el caracter que servira para rellenar puede ser vacio '' o alguna letra o numero pero en formato string '0'
        large, el largo del total de la cadena que se formara, tiene que ser un numero entero
        position, define la posicion donde ira la data, si se rellenara en la izquierda o derecha left(l) o rigth(r)
        data, la cadena inicial siempre en string por defecto es vacio ya que puede ser que sea solo relleno
        """
        line = ''
        if data == None:
            contador = 0
            for i in range(0,large):
                contador += 1
                line += character
        elif len(data) > large:
            line = data[:large]
        elif len(data) == large:
            line = data
        elif len(data) < large:
            if position == 'r':
                for i in range(0,large - len(data)):
                    line += character
                line += data
            elif position == 'l':
                line = data
                for i in range(0,large - len(data)):
                    line += character

        return str(line)

    def _get_data(self):
        for rec in self:
            data = []
            for line in rec.line_ids:
                val = {
                    'TIPO_DOC': line.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or '',
                    'NUM_DOC': line.partner_id.vat or '',
                    'CODIGO': line.code_service or '',
                    'CUENTA': line.account_bank.acc_number or '',
                    'IMPORTE': int(line.amount) or '',
                    'TIPO_OP': line.type_operation or '',
                    'PERIODO': line.period or '',
                    'TIPO_COMP': line.type_comp or '',
                    'SERIE_COMP': line.serie_comp or '',
                    'NUM_COMP': line.num_comp or '',
                    }
                data.append(val)
        return data

    def get_data_file(self):
        raw = '' 
        data = self._get_data()
        template = '{tipo_doc}{num_doc}{fill_1}{fill_2}{codigo}{cuenta}{importe}{tipo_op}{periodo}{tipo_comp}{serie_comp}{num_comp}\r\n'
        
        #agregamos el encabezado que es diferente
        raw += f"*{self.company_id.vat}{self._fill_spaces(' ',35,'l',self.company_id.name)}{self.lote}{self._fill_spaces('0',13,'r',str(self.total))}00\r\n"
        
        for value in data:
            raw += template.format(
                tipo_doc = self._fill_spaces('',1,'l',value['TIPO_DOC']),
                num_doc = self._fill_spaces('',11,'l',value['NUM_DOC']),
                fill_1 = self._fill_spaces(' ',35,'l',None),
                fill_2 = self._fill_spaces('0',9,'l',None),
                codigo = self._fill_spaces('',3,'l',value['CODIGO']),
                cuenta = self._fill_spaces('0',11,'r',value['CUENTA']),
                importe = self._fill_spaces('0',13,'r',str(value['IMPORTE'])),
                tipo_op = self._fill_spaces('0',4,'r',value['TIPO_OP']),
                periodo = self._fill_spaces('',6,'l',value['PERIODO']),
                tipo_comp = self._fill_spaces('0',2,'r',value['TIPO_COMP']),
                serie_comp = self._fill_spaces('',4,'l',value['SERIE_COMP']),
                num_comp = self._fill_spaces('0',8,'r',value['NUM_COMP']),
            )
        raw = raw.rstrip("\r\n")
        return raw.encode('utf8')

    def action_generate_txt(self):
        filename = f"D{self.company_id.vat}{self.lote}.txt"
        values = {
            'file_name': filename,
            'file_binary': base64.encodebytes(self.get_data_file()),
                }
        self.write(values)

    @api.depends('line_ids.amount')
    def _compute_pay_total(self):
        total_pay_amount = 0
        for line in self.line_ids:
            total_pay_amount += line.amount 
        self.total = int(total_pay_amount)

    # Compute para ir aumentando cada vez que se confirme la accion
    @api.depends('journal_id','payment_date','state')
    def _compute_correlative(self):
        for rec in self:
            corre_antiguo = self.search_count([]) if self.search_count([]) >0 else 1
            rec.correlative += corre_antiguo - 1
    
    # Para el nombre
    @api.onchange("payment_date", "correlative","total")
    def _compute_name(self):
        if self.payment_date and self.correlative:
            self.lote = f"{self.payment_date.strftime('%y%m')}{str(self.correlative).zfill(2)}"
            self.name = f"Detracción Lote - {self.lote}"
    
    def aprobar(self):
        self._create_payments()
        self.write({'state': 'done'})

    def action_cancel(self):
        self.action_delete
        self.write({'state': 'cancel'})
    
    def action_draft(self):
        self.write({'state': 'draft'})
    
    def action_delete(self):
        for rec in self:
            rec.payment_ids.unlink()

    def list_payments(self):
        self.ensure_one()
        domain = [('id', 'in', self.payment_ids.ids)]
        return {
            'name': 'Pagos',
            'domain': domain,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': ""
        }

class AccDetracMassLine(models.Model):
    _name = 'acc.detrac.mass.line'
    _description = 'Informacion detraccion line'
    
    parent_id = fields.Many2one("acc.detrac.mass", "Detracción Masiva", ondelete='cascade', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('verify', 'Enviado'),
        ('approve', 'Aprobado'),
        ('refuse', 'Rechazado'),
        ('cancel', 'Cancelado'), 
    ], "State", related="parent_id.state",store=True,copy=False)
    detraction_id = fields.Many2one('account.move.line', 'Detracción',store=True)
    partner_id = fields.Many2one('res.partner', 'Proveedor', store=True)
    code_service = fields.Char("Codigo Bien o Serv.",store=True, copy=False)
    type_operation = fields.Char("Tipo Op", store=True)
    account_bank = fields.Many2one('res.partner.bank','Cuenta Det', store=True)
    amount = fields.Float("Importe", store=True)
    type_comp = fields.Char("Tipo CPE", store=True)
    serie_comp = fields.Char("Serie CPE", store=True)
    num_comp = fields.Char("Número CPE", store=True)
    period = fields.Char("Periodo",store=True)
    
    @api.onchange('detraction_id')
    def onchange_detraction_id(self):
        if self.detraction_id:
            self.partner_id = self.detraction_id.partner_id
            self.amount = self.detraction_id.credit
        
            original_move = self.detraction_id.move_id.am_det_parent
            if original_move:
                self.type_comp = original_move.l10n_latam_document_type_id.code
                self.serie_comp = original_move.seriecomp_sunat
                self.num_comp = original_move.numcomp_sunat
                self.code_service = original_move.detraction_type_id.code
                self.type_operation = '01'
                self.period = str(original_move.invoice_date.year).zfill(4) + str(original_move.invoice_date.month).zfill(2)
            
            acc_number = self.env['res.partner.bank'].search([
                ('partner_id','=',self.detraction_id.partner_id.id),
                ('is_det_bank','=',True)], limit=1)
            if acc_number:
                self.account_bank = acc_number