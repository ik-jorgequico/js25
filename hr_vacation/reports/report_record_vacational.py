from odoo import models

class PartnerXlsx(models.AbstractModel):
    _name = 'report.hr_vacation.detail_record_vacational'
    _description = "Model Report Detail Record Vacational"
    _inherit = 'report.report_xlsx.abstract'

    @staticmethod
    def getColumnName(n):
        result = ''
        while n > 0:
            index = (n - 1) % 26
            result += chr(index + ord('A'))
            n = (n - 1) // 26
        return result[::-1]
    
    def generate_xlsx_report(self, workbook, data, partners):
        row = 7
        dataset = data["dataset"]
        sheet = workbook.add_worksheet('Detalle Record Vacacional')
        sheet.autofilter('A'+str(row)+':S'+str(row))


        style_content_table_format = workbook.add_format({
            'size': 8,
        })
        column_content_table_format = workbook.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,

        })

        column_content_table_format_top = workbook.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#DDEBF7',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,
        })
        
        f2 = workbook.add_format({
            'size': 10, 
            'bold': 1,
            'text_h_align' : 2,
            'text_v_align' : 2,
        })
        
        f3 = workbook.add_format({
            'size': 8, 
            'bold': 1,
            'text_h_align' : 2,
            'text_v_align' : 2,
        })

        sheet.set_column('A:C', 10)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:I', 20)
        sheet.set_column('K:R', 10)
        sheet.set_row(row - 6,20)
        sheet.set_row(row - 5,20)
        sheet.set_row(row - 4,20)
        sheet.set_row(row - 2,30)
        sheet.set_row(row - 1,40)

        sheet.merge_range(row - 6,0,row - 6,18, 'RECORD VACACIONAL', f2)
        sheet.merge_range(row - 5,0,row - 5,18, data["information"]["date"], f2)
        sheet.merge_range(row - 4,0,row - 4,3, data["information"]["company"], f2)

        index = row - 1
        sheet.merge_range(index-1,0,index-1,8, 'DATOS GENERALES', column_content_table_format_top)
        sheet.write(index,0,"Codigo",column_content_table_format)
        sheet.write(index,1,"Tipo Doc",column_content_table_format)
        sheet.write(index,2,"Num Doc",column_content_table_format)
        sheet.write(index,3,"Empleado",column_content_table_format)
        sheet.write(index,4,"Fecha de Ingreso",column_content_table_format)
        sheet.write(index,5,"Puesto",column_content_table_format)
        sheet.write(index,6,"Centro Costo",column_content_table_format)
        sheet.write(index,7,"Area",column_content_table_format)
        sheet.write(index,8,"Localidad",column_content_table_format)
        sheet.write(index,9,"Periodo",column_content_table_format)
        sheet.write(index,10,"Dias Generados",column_content_table_format)
        sheet.write(index,11,"Desde",column_content_table_format)
        sheet.write(index,12,"Hasta",column_content_table_format)
        sheet.write(index,13,"Dias Gozados",column_content_table_format)
        sheet.write(index,14,"Vac Comprads",column_content_table_format)
        sheet.write(index,15,"Vac Pendiente",column_content_table_format)
        sheet.write(index,16,"Vac Vencidas",column_content_table_format)
        sheet.write(index,17,"Vac Truncas",column_content_table_format)

        for i , record in enumerate(dataset):
            index = i + row
            sheet.write(index,0,record["cod"],style_content_table_format)
            sheet.write(index,1,record["type_doc"],style_content_table_format)
            sheet.write(index,2,record["doc"],style_content_table_format)
            sheet.write(index,3,record["employee_id"],style_content_table_format)
            sheet.write(index,4,record["first_contract_date"],style_content_table_format)
            sheet.write(index,5,record["job"],style_content_table_format)
            sheet.write(index,6,record["center_coste"],style_content_table_format)
            sheet.write(index,7,record["area"],style_content_table_format)
            sheet.write(index,8,record["localidad"],style_content_table_format)
            sheet.write(index,9,record["period_char_date"],style_content_table_format)
            sheet.write(index,10,record["days_generated"],style_content_table_format)
            sheet.write(index,11,record["date_from"],style_content_table_format)
            sheet.write(index,12,record["date_to"],style_content_table_format)
            sheet.write(index,13,record["number_real_days"],style_content_table_format)
            sheet.write(index,14,record["vacation_purchased"],style_content_table_format)
            sheet.write(index,15,record["vacation_days_earrings"],style_content_table_format)
            sheet.write(index,16,record["vacation_compensable"],style_content_table_format)
            sheet.write(index,17,record["vacation_trunced"],style_content_table_format)

        tamanio = len(dataset)
        column_total_table_format = workbook.add_format({
            'size': 8,
            'fg_color': '#BFBFC0',
            'border':1,
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'num_format': '#,##0.00'

        })
        sheet.write(row + tamanio, 10 ,"=SUM({}{}:{}{})".format(self.getColumnName(10+1),
                                                            row+1,
                                                            self.getColumnName(10+1),
                                                            row + tamanio),column_total_table_format)
        sheet.write(row + tamanio,0,"TOTAL",column_total_table_format)
        for i in range(13,18):
            sheet.write(row + tamanio,i,"=SUM({}{}:{}{})".format(self.getColumnName(i+1),
                                                                row+1,
                                                                self.getColumnName(i+1),
                                                                row + tamanio),column_total_table_format)




