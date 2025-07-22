from odoo import models, _
from odoo.tools import Markup

class StockCanceledEdiPicking(models.TransientModel):
    _name = 'stock.canceled.edi.picking'
    _description = 'Mark as Canceled in SUNAT'

    def action_canceled_edi_picking(self):
        self.ensure_one()
        active_id = self._context.get('active_id')
        if active_id:
            stock_picking = self.env['stock.picking'].browse(active_id)
            stock_picking.action_mark_canceled_edi_picking()

            # Formateamos el mensaje con el nombre del usuario, usando Markup para procesar HTML
            message = Markup(_("Electronic Guide marked as <b>Canceled in SUNAT</b> by <b>{}</b>").format(self.env.user.name))

            # Publicamos el mensaje con HTML utilizando message_post
            stock_picking.message_post(body=message)

        return {'type': 'ir.actions.act_window_close'}