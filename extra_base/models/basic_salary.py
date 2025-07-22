from odoo import api, fields, models


class BasicSalary(models.Model):
    _name = 'basic.salary'
    _description = 'Sueldo Mínimo'

    value = fields.Float(string='Valor', store = True)
    date_from = fields.Date(string="Desde", store=True,)
    date_to = fields.Date(string="Hasta",store=True)

    def _get_basic_salary_in_range(self,date_from,date_to):
        basic_salary = self.search([
                    ("date_from",'<=',date_from),("date_to",'>=',date_to),
                ],
                limit=1,
                order="date_to desc"
                )
        if not basic_salary:
            
            basic_salary = self.search([
                        '|',("date_from",'<=',date_from),("date_to",'>=',date_to),
                    ],
                    limit=1,
                    order="date_to desc"
                )
            
        return basic_salary.value

        

