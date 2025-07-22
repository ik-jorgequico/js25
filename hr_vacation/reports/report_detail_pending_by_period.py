from odoo import models

class PartnerXlsx(models.AbstractModel):
    _name = 'report.hr_vacation.detail_pending_by_period'
    _description = "Model Report Detail Pending Days"
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
        sheet = workbook.add_worksheet('Detalle General por Periodos')
        style_content_table_format = workbook.add_format({
            'size': 8,
        })
        column_content_table_format = workbook.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#DDEBF7',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,
        })
        column_content_table_format_top = workbook.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#BFBFC0',
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
        sheet.set_column('J:R', 13)

        sheet.set_row(row - 6,20)
        sheet.set_row(row - 5,20)
        sheet.set_row(row - 4,20)
        sheet.set_row(row - 2,30)
        sheet.set_row(row - 1,40)
        
        periods_columns = []
        for dictionary in dataset:
            periods_columns += [i for i in list(dictionary.keys()) if i[:8]=="_Period_"]
        periods_columns = list(set(periods_columns))
        periods_columns.sort()
        
        len_periods_columns = len(periods_columns) 
        sheet.merge_range(row - 6,0,row - 6,15, 'Detalle de Vacaciones Pendientes por Periodo', f2)
        sheet.merge_range(row - 5,0,row - 5,15, data["information"]["date"], f2)
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

        for ind,col_name in enumerate(periods_columns):
            sheet.write(index,9+ind,col_name[8:],column_content_table_format)

        sheet.write(index,9+len_periods_columns,"Total",column_content_table_format)

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

            for ind,col_name in enumerate(periods_columns):
                if col_name in record:
                    sheet.write(i + row,9+ind,record[col_name],style_content_table_format)
                else :
                    sheet.write(i + row,9+ind,0,style_content_table_format)

            sheet.write(index,9+len_periods_columns,record["total_days_pending"],style_content_table_format)
        
        sheet.autofilter('A'+str(row)+':'+self.getColumnName(10+len_periods_columns)+str(row))




