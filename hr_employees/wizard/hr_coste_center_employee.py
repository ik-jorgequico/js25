from odoo import api, fields, models,  _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class CosteCenterEmployee(models.TransientModel):
    _name = "hr.coste.center.employee.wizard"
    _description = "Add Coste Center Employee Wizard"

    @api.model
    def _get_default_date_from(self):
        if self.env.context.get('active_id'):
            employee_id = self.env["hr.employee"].browse(self.env.context.get('active_id'))
            employee_id.write({'is_passed': False})
            
            if len(employee_id.cod_coste_center_account) > 0:
                if not all([i.date_to for i in employee_id.cod_coste_center_account]):
                    raise UserError('Debe seleccionar una Fecha de Termino a todas lon periodos de Centros de Costo ya existentes.')
                return max(d.date_to for d in employee_id.cod_coste_center_account) + relativedelta(days=1)
            else:
                return employee_id.first_contract_date

    name = fields.Char(string="Nombe",)
    date_from = fields.Date(string="Fecha de Inicio", required=True,default=_get_default_date_from )
    date_to = fields.Date(string="Fecha de Termino", )


    account_analytic_account_id = fields.Many2one('account.analytic.account', string='Centro Costo Contable', )
    percent = fields.Selection(
        selection=[
            ("0","0%"),
            ("10","10%"),
            ("20","20%"),
            ("30","30%"),
            ("40","40%"),
            ("50","50%"),
            ("60","60%"),
            ("70","70%"),
            ("80","80%"),
            ("90","90%"),
            ("100","100%"),
            ],string="Porcentaje")
    
    total = fields.Float(compute='_compute_total',)
    lines_ids = fields.One2many("hr.coste.center.employee.lines.wizard","parent_id",string="Cuentas")

    @api.depends('lines_ids')
    def _compute_total(self):
        for record in self:
            record.total = sum([i.percent for i in record.lines_ids ])

    def add_line(self):
        self.ensure_one()
        if  self.date_to and self.date_from > self.date_to:
            raise UserError('La Fecha de Inicio no puede ser mayor a la Fecha de Termino.')
        if not self.account_analytic_account_id or not self.percent:
            raise UserError('Falta registrar Centro de Costo Contable o Porcentaje.')

        val = {
            "account_analytic_account_id":self.account_analytic_account_id.id,
            "percent":float(self.percent),
            "parent_id":self.id,
            "date_from":self.date_from,
            "date_to":self.date_to
        }
        self.write({
            "lines_ids":[(0,0,val)]
        })
        self.percent = False
        self.account_analytic_account_id = False
        return {
            'view_id': False,
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target':'new',
            'type': 'ir.actions.act_window',
            'context': dict(self._context, active_ids=self.ids),
        }
    

    def compute_sheet(self):
        self.ensure_one()
        if self.total != 100:
            raise UserError('El porcentaje no llega al 100%')
        if self.env.context.get('active_id'):
            employee_id = self.env["hr.employee"].browse(self.env.context.get('active_id'))
            if not employee_id:
                raise UserError(_("No registra a ningun empleado"))
            if len(employee_id.cod_coste_center_account) > 0:
                for cod in employee_id.cod_coste_center_account:
                    if cod.date_to >= self.date_from:
                        raise UserError('La Fecha de Inicio debe ser mayor a todas las fecha de Termino de los periodos del Centro de Costo.')
            

            cod_coste_center_account_ids = [(0,0,{"date_from":i.date_from,
                                                  "date_to":i.date_to,
                                                  "percent":i.percent,
                                                  "account_analytic_account_id":i.account_analytic_account_id.id,
                                                  }) for i in self.lines_ids]
            employee_id.write({"cod_coste_center_account":cod_coste_center_account_ids,'is_passed': True})


class CosteCenterEmployeeLines(models.TransientModel):
    _name = "hr.coste.center.employee.lines.wizard"
    _description = "Lines in Coste Center Employee Wizard"

    account_analytic_account_id = fields.Many2one('account.analytic.account', string='Centro Costo Contable', )
    date_from = fields.Date(string="Fecha Inicio", )
    date_to = fields.Date(string="Fecha Fin", )
    percent = fields.Float(string="Porcentaje")
    parent_id = fields.Many2one("hr.coste.center.employee.wizard",)
        
    # @api.depends("parent_id",)
    # def _compute_name(self):
    #     for record in self:
    #         record.name =  record.account_analytic_account_id.name +\
    #                     " " +\
    #                     record.date_from.strftime("%d-%m-&Y") +\
    #                     " " +\
    #                     record.date_to.strftime("%d-%m-&Y")
    