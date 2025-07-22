from odoo import http
from odoo.http import request, content_disposition

RUTA_ARCHIVOS = '/tmp/'


class DownloadTxt(http.Controller):

    @http.route('/download/txt', type='http', auth='public', website=True)
    def txt_download(self, filename, **kw):
        mimetype = 'text/plain'
        u_file = open(RUTA_ARCHIVOS + filename, 'rb').read()
        if u_file:
            return request.make_response(u_file, [
                ('Content-Type', mimetype),
                ('Content-Disposition', content_disposition(filename)),
            ])