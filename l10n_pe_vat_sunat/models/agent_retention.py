# -*- coding: utf-8 -*-
from odoo import models, fields


class AgentRetention(models.Model):
    _name = 'agent.retention'
    _description = 'Agentes de Retención'

    ruc = fields.Char(required=True)
    razon_social = fields.Char()
    a_partir_del = fields.Date()
    resolucion = fields.Char()
