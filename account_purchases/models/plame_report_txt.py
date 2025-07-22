# -*- coding: utf-8 -*-
import base64


class PlameReport(object):
    
    def __init__(self, data):
        self.data = data
    
    # UNA FUNCION PARA CADA TXT NECESARIO DENTRO DEL MISMO MODELO ESTE ES PARA LAS COMPRAS NORMALES
    def get_content_data(self):
        raw = ''
        template = '{period_ple}|{cuo_sunat}|{correlativo_ple}|{invoice_date}|{date_due}|{type_cpe}|{serie_cpe}|' \
        '{dua_year}|{num_cpe}||{type_doc}|{num_doc}|{company_name}|{base_ag_vg}|' \
        '{igv_ag_vg}|{base_ag_vgng}|{igv_ag_vgng}|{base_ag_no}|{igv_ag_no}|{inafecto}|{isc}|' \
        '{bolsas_tax}|{other_tax}|{total_amount}|{currency}|{tc_sunat}|{date_reversed}|{tipcomp_reversed}|' \
        '{serie_reversed}|{dua_reversed}|{num_reversed}|{date_det}|{num_det}|||' \
        '||||||{state_ple}|\r\n'

        for value in self.data:
            raw += template.format(
                period_ple=value['PERIODO PLE'],
                cuo_sunat=value['CUO'],
                correlativo_ple=value['M0002'],
                invoice_date=value['FECHA EMISION'],
                date_due=value['FECHA VENCIMIENTO'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                dua_year=value['AÑO DUA'],
                num_cpe=value['NUMERO CPE'],
                type_doc=value['TIPO DOC'],
                num_doc=value['NUMERO DOC'],
                company_name=value['RAZON SOCIAL'],
                base_ag_vg=value['BASE AG-VG'],
                igv_ag_vg=value['IGV AG-VG'],
                base_ag_vgng=value['BASE AG-VGNG'],
                igv_ag_vgng=value['IGV AG-VGNG'],
                base_ag_no=value['BASE AG-NO'],
                igv_ag_no=value['IGV AG-NO'],
                inafecto=value['INAFECTO'],
                isc='',
                bolsas_tax='0.00',
                other_tax='',
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

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())
    
    # UNA FUNCION PARA CADA TXT NECESARIO DENTRO DEL MISMO MODELO ESTE ES PARA LAS COMPRAS NO DOMICILIADO
    def get_data_82(self):
        raw = ''
        template = '{period_ple}|{cuo_sunat}|{correlativo_ple}|{invoice_date}|{type_cpe}|{serie_cpe}|' \
        '{num_cpe}|{inafecto}|{other_tax}|{total_amount}||||||{currency}|{tc_sunat}|{country_code}|{vendor_name}||' \
        '{num_doc}||||||||||{convenio_nodom}||{type_profit_nodom}|||{state_ple}|\r\n'

        for value in self.data:
            raw += template.format(
                period_ple=value['PERIODO PLE'],
                cuo_sunat=value['CUO'],
                correlativo_ple=value['M0002'],
                invoice_date=value['FECHA EMISION'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                num_cpe=value['NUMERO CPE'],
                inafecto=value['INAFECTO'],
                other_tax='',
                total_amount=value['TOTAL'],
                currency=value['MONEDA'],
                tc_sunat=value['TIPO DE CAMBIO'],
                country_code=value['CODIGO PAIS'],
                vendor_name=value['RAZON SOCIAL'],
                num_doc=value['NUMERO DOC'],
                convenio_nodom=value['CONVENIO NODOM'],
                type_profit_nodom=value['TIPO RENTA NODOM'],
                state_ple=value['ESTADO PLE'],
            )
        raw = raw.rstrip("\r\n")

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())
    
    # UNA FUNCION PARA CADA TXT NECESARIO DENTRO DEL MISMO MODELO ESTE ES PARA VALIDAR LAS COMPRAS
    def get_data_sunat_validate(self):
        raw = ''
        template = '{num_doc}|{type_cpe}|{serie_cpe}|{num_cpe}|{invoice_date}|{total_real}\r\n'

        for value in self.data:
            raw += template.format(
                num_doc=value['NUMERO DOC'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                num_cpe=value['NUMERO CPE'],
                invoice_date=value['FECHA EMISION'],
                total_real=value['TOTAL REAL'],
            )
        raw = raw.rstrip("\r\n")

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())
    
    # UNA FUNCION PARA CADA TXT NECESARIO DENTRO DEL MISMO MODELO ESTE ES PARA LAS VENTAS NORMALES
    def get_data_141(self):
        raw = ''
        template = '{period_ple}|{cuo_sunat}|{correlativo_ple}|{invoice_date}|{date_due}|{type_cpe}|{serie_cpe}|' \
        '{num_cpe}||{type_doc}|{num_doc}|{company_name}|{exportacion}|{base_ag_vg}|{desc_vg}|' \
        '{igv_ag_vg}|{desc_igv_vg}|{exonerado}|{inafecto}|{isc}|||{ibv}||' \
        '{total_amount}|{currency}|{tc_sunat}|{date_reversed}|{tipcomp_reversed}|' \
        '{serie_reversed}|{num_reversed}||||{state_ple}|\r\n'

        for value in self.data:
            raw += template.format(
                period_ple=value['PERIODO PLE'],
                cuo_sunat=value['CUO'],
                correlativo_ple=value['M0002'],
                invoice_date=value['FECHA EMISION'],
                date_due=value['FECHA VENCIMIENTO'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                num_cpe=value['NUMERO CPE'],
                type_doc=value['TIPO DOC'],
                num_doc=value['NUMERO DOC'],
                company_name=value['RAZON SOCIAL'],
                exportacion=value['BASE EXP'],
                base_ag_vg=value['BASE AG-VG'],
                desc_vg=value['BASE DESC'],
                igv_ag_vg=value['IGV AG-VG'],
                desc_igv_vg=value['IGV DESC'],
                exonerado=value['EXONERADO'],
                inafecto=value['INAFECTO'],
                isc='',
                ibv='0.00',
                total_amount=value['TOTAL'],
                currency=value['MONEDA'],
                tc_sunat=value['TIPO DE CAMBIO'],
                date_reversed=value['FECHA REV'],
                tipcomp_reversed=value['TIPO REV'],
                serie_reversed=value['SERIE REV'],
                num_reversed=value['NUMERO REV'],
                state_ple=value['ESTADO PLE']
            )
        raw = raw.rstrip("\r\n")

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())
    
    # UNA FUNCION PARA CADA TXT NECESARIO DENTRO DEL MISMO MODELO, ESTE ES PARA EL TXT DEL DIARIO
    def get_data_ple51(self):
        raw = ''
        template =  '{period_ple}|{cuo_sunat}|{correlativo_ple}|{chart_code}|||{currency}|{type_doc}|' \
        '{num_doc}|{type_cpe}|{serie_cpe}|{num_cpe}|{date}|{due_date}|{invoice_date}|{ref}||{debit}|' \
        '{credit}||{state_ple}|\r\n'

        for value in self.data:
            raw += template.format(
                period_ple=value['PERIODO PLE'],
                cuo_sunat=value['CUO'],
                correlativo_ple=value['SECUENCIA'],
                chart_code=value['CTA CODE'],
                currency=value['MONEDA'],
                type_doc=value['TIPO DOC'],
                num_doc=value['NUMERO DOC'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                num_cpe=value['NUMERO CPE'],
                date = value['FECHA'],
                invoice_date=value['FECHA EMISION'],
                due_date = value['FECHA VENC'],
                ref=value['REF'],
                debit=value['DEBITO'],
                credit=value['CREDITO'],
                state_ple=value['ESTADO PLE']
            )
        raw = raw.rstrip("\r\n")

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())
    
    def get_data_ple53(self):
        raw = ''
        template = '{period_ple}|{chart_code}|{chart_name}|{chart_type}||||{state_ple}|\r\n'

        for value in self.data:
            raw += template.format(
                period_ple=value['PERIODO PLE'],
                chart_code=value['CTA CODE'],
                chart_name=value['CTA NAME'],
                chart_type=value['CTA TIPO'],
                state_ple=value['ESTADO PLE'],
            )
        raw = raw.rstrip("\r\n")

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())
    
     # UNA FUNCION PARA CADA TXT NECESARIO DENTRO DEL MISMO MODELO, ESTE ES PARA EL TXT DEL MAYOR
    
    def get_data_ple61(self):
        raw = ''
        template =  '{period_ple}|{cuo_sunat}|{correlativo_ple}|{chart_code}|||{currency}|{type_doc}|' \
        '{num_doc}|{type_cpe}|{serie_cpe}|{num_cpe}|{date}|{due_date}|{invoice_date}|{ref}||{debit}|' \
        '{credit}||{state_ple}|\r\n'

        for value in self.data:
            raw += template.format(
                period_ple=value['PERIODO PLE'],
                cuo_sunat=value['CUO'],
                correlativo_ple=value['SECUENCIA'],
                chart_code=value['CTA CODE'],
                currency=value['MONEDA'],
                type_doc=value['TIPO DOC'],
                num_doc=value['NUMERO DOC'],
                type_cpe=value['TIPO CPE'],
                serie_cpe=value['SERIE CPE'],
                num_cpe=value['NUMERO CPE'],
                date = value['FECHA'],
                invoice_date=value['FECHA EMISION'],
                due_date = value['FECHA VENC'],
                ref=value['REF'],
                debit=value['DEBITO'],
                credit=value['CREDITO'],
                state_ple=value['ESTADO PLE']
            )
        raw = raw.rstrip("\r\n")

        return base64.encodebytes(raw.encode('utf8') or '\n'.encode())
    
