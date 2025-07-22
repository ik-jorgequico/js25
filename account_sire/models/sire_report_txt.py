import base64


class SireReport(object):

    def __init__(self, data):
        self.data = data

    # UNA FUNCION PARA CADA TXT NECESARIO DENTRO DEL MISMO MODELO ESTE ES PARA EL REEMPLAZO DE LAS COMPRAS DEL SIRE
    def get_replace_data(self):
        raw = ''
        template = '{company_ruc}|{company_name}|{period}||{invoice_date}|{date_due}|{type_cpe}|{serie_cpe}|' \
        '{dua_year}|{num_cpe}||{type_doc}|{num_doc}|{razon_social}|{base_ag_vg}|' \
        '{igv_ag_vg}|{base_ag_vgng}|{igv_ag_vgng}|{base_ag_no}|{igv_ag_no}|{inafecto}|{isc}|' \
        '{bolsas_tax}|{other_tax}|{total_amount}|{currency}|{tc_sunat}|{date_reversed}|{tipcomp_reversed}|' \
        '{serie_reversed}|{dua_reversed}|{num_reversed}||||||||||||\r\n'

        for value in self.data:
            raw += template.format(
                company_ruc=value['COMPANY RUC'],
                company_name=value['COMPANY NAME'],
                period=value['PERIODO PLE'][:6],
                invoice_date=value['FECHA EMISION'],
                date_due=value['FECHA VENCIMIENTO'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                dua_year=value['AÑO DUA'],
                num_cpe=value['NUMERO CPE'],
                type_doc=value['TIPO DOC'],
                num_doc=value['NUMERO DOC'],
                razon_social=value['RAZON SOCIAL'],
                base_ag_vg=value['BASE AG-VG'],
                igv_ag_vg=value['IGV AG-VG'],
                base_ag_vgng=value['BASE AG-VGNG'],
                igv_ag_vgng=value['IGV AG-VGNG'],
                base_ag_no=value['BASE AG-NO'],
                igv_ag_no=value['IGV AG-NO'],
                inafecto=value['INAFECTO'],
                isc='',
                bolsas_tax='',
                other_tax=value['OTROS CARGOS'],
                total_amount=value['TOTAL'],
                currency=value['MONEDA'],
                tc_sunat=value['TIPO DE CAMBIO'],
                date_reversed=value['FECHA REV'],
                tipcomp_reversed=value['TIPO REV'],
                serie_reversed=value['SERIE REV'],
                dua_reversed='',
                num_reversed=value['NUMERO REV'],
                date_det=value['FECHA CONSTANCIA'],
                num_det=value['CONSTANCIA'],
                state_ple=value['ESTADO PLE']
            )
        raw = raw.rstrip("\r\n")

        return raw.encode('utf8')

    def get_replace_rvie(self):
        raw = ''
        template = '{company_ruc}|{company_name}|{period}||{invoice_date}|{date_due}|{type_cpe}|{serie_cpe}|' \
        '{num_cpe}||{type_doc}|{num_doc}|{razon_social}|{expo}|{base_ag_vg}|{base_desc_vg}|' \
        '{igv_ag_vg}|{igv_desc_vg}|{exo}|{ina}|{isc}|{base_ivap}|{ivap}|' \
        '{bolsas_tax}|{other_tax}|{total_amount}|{currency}|{tc_sunat}|{date_reversed}|{tipcomp_reversed}|' \
        '{serie_reversed}|{num_reversed}|\r\n'

        for value in self.data:
            raw += template.format(
                company_ruc=value['COMPANY RUC'],
                company_name=value['COMPANY NAME'],
                period=value['PERIODO PLE'][:6],
                invoice_date=value['FECHA EMISION'],
                date_due=value['FECHA VENCIMIENTO'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                num_cpe=value['NUMERO CPE'],
                type_doc=value['TIPO DOC'],
                num_doc=value['NUMERO DOC'],
                razon_social=value['RAZON SOCIAL'],
                expo=value['BASE EXP'],
                base_ag_vg=value['BASE AG-VG'],
                base_desc_vg=value['BASE DESC'],
                igv_ag_vg=value['IGV AG-VG'],
                igv_desc_vg=value['IGV DESC'],
                exo=value['EXONERADO'],
                ina=value['INAFECTO'],
                isc='0',
                base_ivap='0',
                ivap='0',
                bolsas_tax='0',
                other_tax='0',
                total_amount=value['TOTAL'],
                currency=value['MONEDA'],
                tc_sunat=value['TIPO DE CAMBIO'],
                date_reversed=value['FECHA REV'],
                tipcomp_reversed=value['TIPO REV'],
                serie_reversed=value['SERIE REV'],
                num_reversed=value['NUMERO REV'],
            )
        raw = raw.rstrip("\r\n")

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())