from io import BytesIO
import xlsxwriter


class HrloanMacro(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj


    def get_content(self):
        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })

        sheet = wb.add_worksheet('Loan Macro') # crear la hoja trabajador

        row = 7

        column_content_table_format = wb.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,
        })
        

        column_content_table_format_top = wb.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#DDEBF7',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,
        })

        f1 = wb.add_format({
            'size': 10,
            'bold': 1,
            'font_color': 'black',

        })
        f2 = wb.add_format({
            'size': 10, 
            'font_color': 'black',
        })

        style_content_table_format = wb.add_format({
            'size': 8,
            'border': 1,
            'num_format':"#,##0.00;-#,##0.00",

        })

        style_content_table_format_integer = wb.add_format({
            'size': 8,
            'border': 1,
            'num_format':"#,##0;-#,##0",

        })
        
        style_content_table_format_2 = wb.add_format({
            'size': 8,
            'border': 1,
            'bold': 1,
            'num_format':"#,##0.00;-#,##0.00",

        })
        
        style_date_content_table_format = wb.add_format({
            'size': 8,
            'num_format': 'dd/mm/yyyy',
            'border': 1,
            }
        )


        style_money_content_table_format = wb.add_format({
            'num_format':"#,##0.00;-#,##0.00",
            'border': 1,
            'size': 8,
            })

        """
            CABECERA
        """


        """
            PRINT COLUMNS
        """
        sheet.autofilter('A7:J8') #crear filtrado de la columna A10 - J10
        #sheet.autofilter(0,row-1,0,23) #crear filtrado de la columna A10 - Q10

        #sheet.freeze_panes(1, 3)
        sheet.set_column(0, 18, 20)
  
        sheet.set_row(row - 2,30) #set_row(fila, columna)
        sheet.set_row(row - 1,40)

        # sheet.merge_range(row - 1,0,row,0,"CODIGO EMPLEADO",column_content_table_format)  #write(fila, columna, texto, formato)
        # sheet.merge_range(row - 1,1,row,1,"DOCUMENTO DE IDENTIDAD",column_content_table_format)
        # sheet.merge_range(row - 1,2,row,2,"NOMBRE DEL EMPLEADO",column_content_table_format)
        # sheet.merge_range(row - 1,3,row,3,"CENTRO DE COSTO",column_content_table_format)
        # sheet.merge_range(row - 1,4,row,4,"LOCALIDAD",column_content_table_format)
        # sheet.merge_range(row - 1,5,row,5,"AREA/DEPARTAMENTO",column_content_table_format)
        # sheet.merge_range(row - 1,6,row,6,"FECHA INGRESO",column_content_table_format)
        # sheet.merge_range(row - 1,7,row,7,"PUESTO",column_content_table_format)
        # sheet.merge_range(row - 1,8,row,8,"FECHA DE SOLICITUD",column_content_table_format)
        # sheet.merge_range(row - 1,9,row,9,"FECHA DE PAGO 1RA CUOTA",column_content_table_format)
        # sheet.merge_range(row - 1,10,row,10,"FECHA DE PAGO ULTIMA CUOTA",column_content_table_format)
        # sheet.merge_range(row - 1,11,row,11,"IMPORTE PRESTAMOS",column_content_table_format)
        # sheet.merge_range(row - 1,12,row,12,"NRO. DE CUOTAS",column_content_table_format)
        # sheet.merge_range(row - 1,13,row,13,"VALOR DE CUOTA",column_content_table_format)
        # sheet.merge_range(row - 1,14,row,14,"NRO. CUOTAS PAGADAS",column_content_table_format)
        # sheet.merge_range(row - 1,15,row,15,"NRO. CUOTAS PENDIENTES",column_content_table_format)
        # sheet.merge_range(row - 1,16,row,16,"IMPORTE PAGADO",column_content_table_format)
        # sheet.merge_range(row - 1,17,row,17,"IMPORTE PENDIENTE",column_content_table_format)
        # sheet.merge_range(row - 1,18,row,18,"ESTADO",column_content_table_format)


        sheet.merge_range(row - 1,0,row,0,"DOCUMENTO DE IDENTIDAD",column_content_table_format)  #write(fila, columna, texto, formato)
        sheet.merge_range(row - 1,1,row,1,"NOMBRE DEL EMPLEADO",column_content_table_format)
        sheet.merge_range(row - 1,2,row,2,"CONCEPTO",column_content_table_format)
        sheet.merge_range(row - 1,3,row,3,"FECHA DE PAGO",column_content_table_format)
        sheet.merge_range(row - 1,4,row,4,"MONTO A PAGAR",column_content_table_format)
        sheet.merge_range(row - 1,5,row,5,"FORMA DE PAGO",column_content_table_format)
        sheet.merge_range(row - 1,6,row,6,"CODIGO OFICINA",column_content_table_format)
        sheet.merge_range(row - 1,7,row,7,"CODIGO CUENTA",column_content_table_format)
        sheet.merge_range(row - 1,8,row,8,"REFERENCIA",column_content_table_format)
        sheet.merge_range(row - 1,9,row,9,"CCI",column_content_table_format)
    
        """
            PRINT DATA TABLE
        """
        meses = ("ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE")

        cont = 0
        # for i,dict in enumerate(self.data):
        #     sheet.write(i + row + 1,0,dict["Cod."],style_content_table_format)
        #     sheet.write(i + row + 1,1,dict["dni"],style_content_table_format)
        #     sheet.write(i + row + 1,2,dict["nombre"],style_content_table_format)
        #     sheet.write(i + row + 1,3,dict["centro"],style_date_content_table_format)
        #     sheet.write(i + row + 1,4,dict["localidad"],style_content_table_format)
        #     sheet.write(i + row + 1,5,dict["area"],style_content_table_format)
        #     sheet.write(i + row + 1,6,dict["first"],style_date_content_table_format)
        #     sheet.write(i + row + 1,7,dict["puesto"],style_content_table_format)
        #     sheet.write(i + row + 1,8,dict["solicitud"],style_date_content_table_format)
        #     sheet.write(i + row + 1,9,dict["cuota_1"],style_date_content_table_format)
        #     sheet.write(i + row + 1,10,dict["cuota_n"],style_date_content_table_format)
        #     sheet.write(i + row + 1,11,dict["importe"],style_content_table_format)
        #     sheet.write(i + row + 1,12,dict["n_cuotas"],style_content_table_format)
        #     sheet.write(i + row + 1,13,dict["val_cuota"],style_content_table_format)
        #     sheet.write(i + row + 1,14,dict["cuotas_pagadas"],style_content_table_format)
        #     sheet.write(i + row + 1,15,dict["cuotas_pendientes"],style_content_table_format)
        #     sheet.write(i + row + 1,16,dict["importe_pagado"],style_content_table_format)
        #     sheet.write(i + row + 1,17,dict["importe_pendiente"],style_content_table_format)
        #     sheet.write(i + row + 1,18,dict["estado"],style_content_table_format)

        for i,dict in enumerate(self.data):
            sheet.write(i + row + 1,0,dict["dni"],style_content_table_format)
            sheet.write(i + row + 1,1,dict["nombre"],style_content_table_format)
            sheet.write(i + row + 1,2,dict["concepto"],style_content_table_format)
            sheet.write(i + row + 1,3,dict["pago"],style_date_content_table_format)
            sheet.write(i + row + 1,4,dict["monto"],style_content_table_format)
            sheet.write(i + row + 1,5,dict["forma"],style_content_table_format_integer)
            sheet.write(i + row + 1,6,dict["cod_oficina"],style_content_table_format)
            sheet.write(i + row + 1,7,dict["cod_cuenta"],style_content_table_format)
            sheet.write(i + row + 1,8,dict["referencia"],style_content_table_format)
            sheet.write(i + row + 1,9,dict["cci"],style_content_table_format)
            


          
            
          

        wb.close()
        output.seek(0)
        return output.read()
