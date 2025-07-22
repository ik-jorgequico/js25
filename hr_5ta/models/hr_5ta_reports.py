from io import BytesIO
import xlsxwriter


class Excel5taReport(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj


    def get_content(self):
        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })

        sheet = wb.add_worksheet('5TA CATEGORIA') # crear la hoja trabajador

        row = 17

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
        
        style_content_table_format_2 = wb.add_format({
            'size': 8,
            'border': 1,
            'bold': 1,
            'num_format':"#,##0.00;-#,##0.00",

        })
        
        style_date_content_table_format = wb.add_format({
            'size': 8,
            'num_format': 'dd/mm/yy',
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
        sheet.autofilter('A17:Q18') #crear filtrado de la columna A10 - Q10
        #sheet.autofilter(0,row-1,0,23) #crear filtrado de la columna A10 - Q10

        #sheet.freeze_panes(1, 3)
        sheet.set_column(0, 16, 20)
  
        sheet.set_row(row - 2,30) #set_row(fila, columna)
        sheet.set_row(row - 1,40)

        sheet.write(9,1,"Renta anual",column_content_table_format)
        sheet.write(9,2,"Tasa",column_content_table_format)
        sheet.write(9,3,"Exceso",column_content_table_format)
        sheet.write(9,4,"Hasta",column_content_table_format)

        sheet.merge_range(row - 1,0,row,0,"NRO.",column_content_table_format)  #write(fila, columna, texto, formato)
        sheet.merge_range(row - 1,1,row,1,"COD.",column_content_table_format)
        sheet.merge_range(row - 1,2,row,2,"DNI",column_content_table_format)
        sheet.merge_range(row - 1,3,row,3,"TRABAJADOR",column_content_table_format)
        sheet.merge_range(row - 1,4,row,4,"CENTRO DE COSTO",column_content_table_format)
        sheet.merge_range(row - 1,5,row,5,"LOCALIDAD",column_content_table_format)
        sheet.merge_range(row - 1,6,row,6,"AREA/DEPARTAMENTO",column_content_table_format)
        sheet.merge_range(row - 1,7,row,7,"FEC. INGRESO",column_content_table_format)
        sheet.merge_range(row - 1,8,row,8,"REMUNER. ACUMULADA",column_content_table_format)
        sheet.merge_range(row - 1,9,row,9,"REMUNER. AFECTA MES",column_content_table_format)
        sheet.merge_range(row - 1,10,row,10,"MONTO PROYEC. MENSUAL",column_content_table_format)
        sheet.merge_range(row - 1,11,row,11,"PROYECTA GRATIFIC. F.P. Y BONO EXTRAOR.",column_content_table_format)
        sheet.merge_range(row - 1,12,row,12,"RENTA BRUTA ANUAL",column_content_table_format)
        sheet.merge_range(row - 1,13,row,13,"RENTA NETA ANUAL",column_content_table_format)
        sheet.merge_range(row - 1,14,row,14,"RESULT. IR",column_content_table_format)
        sheet.merge_range(row - 1,15,row,15,"SALDO",column_content_table_format)
        sheet.merge_range(row - 1,16,row,16,"RETENCION MES",column_content_table_format)
    
        """
            PRINT DATA TABLE
        """
        meses = ("ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE")

        cont = 0
        for i,dict in enumerate(self.data):

            for j,tramo in enumerate(dict['tramo']):
                sheet.write(10+j,1,"IR("+str(j+1)+")",style_content_table_format)
                sheet.write(10+j,2,str(tramo[2])+"%",style_content_table_format)
                sheet.write(10+j,3,tramo[0]*dict["uit"],style_content_table_format)
                sheet.write(10+j,4,tramo[1]*dict["uit"] if (tramo[1] < 10000) else "",style_content_table_format)


            sheet.write(0,0,dict["cliente"].upper(),f1)
            sheet.write(2,0,"INGRESOS Y DESCUENTOS POR RETENCION DE 5TA. CATEGORIA",f1)
            sheet.write(3,0,meses[int(dict['fecha de 5ta'].month) - 1] + " - " + str(dict["fecha de 5ta"].year),f1)
            sheet.write(4,0,"Cliente:",f2)
            sheet.write(4,1,dict["cliente"].upper(),f2)

            sheet.write(6,1,"1UIT",column_content_table_format)
            sheet.write(6,2,dict["uit"],style_content_table_format)

            sheet.write(7,1,"7UIT",column_content_table_format)
            sheet.write(7,2,dict["uit"]*7,style_content_table_format)

            sheet.write(i + row + 1,0,i+1,style_content_table_format)
            sheet.write(i + row + 1,1,dict["Cod."],style_content_table_format)
            sheet.write(i + row + 1,2,dict["dni"],style_content_table_format)
            sheet.write(i + row + 1,3,dict["apellidos y nombres"],style_content_table_format)
            
            
            sheet.write(i + row + 1,4,dict["CENTRO DE COSTO"],style_content_table_format)
            sheet.write(i + row + 1,5,dict["LOCALIDAD"],style_content_table_format)
            sheet.write(i + row + 1,6,dict["AREA/DEPARTAMENTO"],style_content_table_format)
            
            
            sheet.write(i + row + 1,7,dict["fecha de ingreso"],style_date_content_table_format)
            sheet.write(i + row + 1,8,dict["total ingreso"],style_content_table_format)
            sheet.write(i + row + 1,9,dict["remuneracion afecta"],style_content_table_format)
            sheet.write(i + row + 1,10,dict["proyeccion mensual"],style_content_table_format)
            sheet.write(i + row + 1,11,dict["proyeccion gratificacion"],style_content_table_format)
            sheet.write(i + row + 1,12,dict["renta bruta anual"],style_content_table_format)
            sheet.write(i + row + 1,13,dict["renta neta anual"],style_money_content_table_format)
            sheet.write(i + row + 1,14,dict["resultado ir"],style_money_content_table_format)

            sheet.write(i + row + 1,15,dict["saldo"],style_content_table_format)
            sheet.write(i + row + 1,16,dict["retencion mes"],style_money_content_table_format)  
            
            cont += 1   
            
        sheet.write(cont + row + 1,8,dict["sum acum"],style_content_table_format_2)
        sheet.write(cont + row + 1,9,dict["sum afec"],style_content_table_format_2)
        sheet.write(cont + row + 1,10,dict["sum monto proy"],style_content_table_format_2)
        sheet.write(cont + row + 1,11,dict["sum grati proy"],style_content_table_format_2)
        sheet.write(cont + row + 1,12,dict["sum bruta"],style_content_table_format_2)
        sheet.write(cont + row + 1,13,dict["sum neta"],style_content_table_format_2)
        sheet.write(cont + row + 1,14,dict["sum result"],style_content_table_format_2)

        sheet.write(cont + row + 1,15,dict["sum saldo"],style_content_table_format_2)
        sheet.write(cont + row + 1,16,dict["sun reten"],style_content_table_format_2)
          

        wb.close()
        output.seek(0)
        return output.read()
