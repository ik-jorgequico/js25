from io import BytesIO
import xlsxwriter


class GratiExcelReport(object):
    def __init__(self, data, obj):
        self.data = data
        self.obj = obj

    def get_content(self):
        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })

        sheet = wb.add_worksheet('TRABAJADOR') # crear la hoja trabajador

        row = 10

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
            'fg_color': '#C5D9F1',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,
        })

        f1 = wb.add_format({
            'size': 10,
            'bold': 1,

        })
        f2 = wb.add_format({
            'size': 10, 
        })

        style_content_table_format = wb.add_format({
            'size': 8,
            'border': 1,

        })
        
        style_content_table_format_2 = wb.add_format({
            'size': 8,
            'border': 1,
            'num_format':"#,##0.00;-#,##0.00",
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,


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
        sheet.write(1,2,self.obj.name,f1)

        sheet.write(3,0,"RAZON SOCIAL:",f1)
        sheet.write(3,1,self.obj.env.company.name,f2)
        sheet.write(4,0,"RUC:",f1)
        if self.obj.env.company.vat:
            sheet.write(4,1,self.obj.env.company.vat,f2)
        sheet.write(5,0,"PERIODO",f1)
        sheet.write(5,1, self.obj.date_from.strftime("%b %Y").upper() + "-" + self.obj.date_to.strftime("%b %Y").upper(),f2)

        """
            PRINT COLUMNS
        """
        prom_columns = []

        for dictionary in self.data:
            prom_columns += [i for i in list(dictionary.keys()) if i[:5]=="Prom_"]
        prom_columns = list(set(prom_columns))
        prom_columns.sort()
        len_prom_columns = len(prom_columns) 
        sheet.autofilter(row-1,0,row-1,len_prom_columns + 29) #crear filtrado de la columna A10 - Q10

        sheet.set_column(0,len_prom_columns + 29, 20)
        sheet.set_row(row - 2,30) #set_row(fila, columna)
        sheet.set_row(row - 1,40)

        sheet.merge_range(row - 2,0,row - 2,19, 'DATOS GENERALES', column_content_table_format_top)
        sheet.write(row - 1,0,"ID",column_content_table_format)  #write(fila, columna, texto, formato)
        sheet.write(row - 1,1,"CODIGO",column_content_table_format)  
        sheet.write(row - 1,2,"TIPO DOC",column_content_table_format)  
        sheet.write(row - 1,3,"DOCUMENTO",column_content_table_format)  
        sheet.write(row - 1,4,"PRIMER APELLIDO",column_content_table_format)  
        sheet.write(row - 1,5,"SEGUNDO APELLIDO",column_content_table_format)  
        sheet.write(row - 1,6,"PRIMER NOMBRE",column_content_table_format)  
        sheet.write(row - 1,7,"SEGUNDO NOMBRE",column_content_table_format)  
        sheet.write(row - 1,8,"CENTRO DE COSTO",column_content_table_format)
        sheet.write(row - 1,9,"ZONAL",column_content_table_format)  #write(fila, columna, texto, formato)
        sheet.write(row - 1,10,"AREA/DEPARTAMENTO",column_content_table_format)
        sheet.write(row - 1,11,"CARGO",column_content_table_format)
        sheet.write(row - 1,12,"BANCO HABERES",column_content_table_format)
        sheet.write(row - 1,13,"CUENTA HABERES",column_content_table_format)
        sheet.write(row - 1,14,"FECHA DE INGRESO",column_content_table_format)
        sheet.write(row - 1,15,"FECHA DE CESE",column_content_table_format)
        sheet.write(row - 1,16,"NUMERO PERIODOS",column_content_table_format)
        sheet.write(row - 1,17,"INICIO DE PERIODO",column_content_table_format)
        sheet.write(row - 1,18,"TERM. DE PERIODO",column_content_table_format)
        sheet.write(row - 1,19,"FECHA DE PAGO",column_content_table_format)
        
        sheet.write(row - 1,20,"REGIMEN",column_content_table_format)
        
        sheet.merge_range(row - 2,21,row - 2,22+len_prom_columns, 'BASE CALCULO', column_content_table_format_top)
        sheet.write(row - 1,21,"BÁSICO",column_content_table_format)
        sheet.write(row - 1,22,"ASIG FAMILIAR",column_content_table_format)
        for ind,col_name in enumerate(prom_columns):
                sheet.write(row - 1,23+ind,col_name,column_content_table_format)
        sheet.merge_range(row - 2,23+len_prom_columns,row - 2,25+len_prom_columns, 'DIAS LABORADOS O NO LABORADOS', column_content_table_format_top)
        sheet.write(row - 1,23+len_prom_columns,"DÍAS LABORADOS",column_content_table_format)
        sheet.write(row - 1,24+len_prom_columns,"AUSENTISMOS",column_content_table_format)
        sheet.write(row - 1,25+len_prom_columns,"DÍAS LABORADOS TOTALES",column_content_table_format)
        sheet.merge_range(row - 2,26+len_prom_columns,row - 2,28+len_prom_columns, 'INGRESOS', column_content_table_format_top)
        sheet.write(row - 1,26+len_prom_columns,"GRATIFICACIÓN",column_content_table_format)
        sheet.write(row - 1,27+len_prom_columns,"BONIFICACIÓN EXTRAORDINARIA",column_content_table_format)
        sheet.write(row - 1,28+len_prom_columns,"TOTAL GRATIFICACIÓN",column_content_table_format)
        sheet.write(row - 2,29+len_prom_columns,"DESCUENTOS",column_content_table_format_top)
        sheet.write(row - 1,29+len_prom_columns,"DESCUENTO",column_content_table_format)
        sheet.write(row - 1,30+len_prom_columns,"NETO A PAGAR",column_content_table_format)
    
        """
            PRINT DATA TABLE
        """
        count = 0
        
        salary, family_asig, number_days, number_leave_days, number_total, total, health_regimen, grati_bono, desc_grati, grati_neto = 0,0,0,0,0,0,0,0,0,0
        
        sum_list = [0] * len_prom_columns
        
        for i,dict in enumerate(self.data):
            if(i == 0):
                salary = dict["suma basico"]
                family_asig = dict["suma asig fam"]
                number_days = dict["suma dias laborados"]
                number_leave_days = dict["suma ausentismos"]
                number_total = dict["suma dia lab total"]
                total = dict["suma gratificacion"]
                health_regimen = dict["suma bon extra"]
                grati_bono = dict["suma total grati"]
                desc_grati = dict["suma descuento"]
                grati_neto = dict["suma neto a pagar"]
                
            sheet.write(i + row,0,dict["ID"],style_content_table_format)
            sheet.write(i + row,1,dict["Cod."],style_content_table_format)
            sheet.write(i + row,2,dict["Tipo_doc"],style_content_table_format)
            sheet.write(i + row,3,dict["documento"],style_content_table_format)
            sheet.write(i + row,4,dict["PRIMER APELLIDO"],style_content_table_format)
            sheet.write(i + row,5,dict["SEGUNDO APELLIDO"],style_content_table_format)
            sheet.write(i + row,6,dict["PRIMER NOMBRE"],style_content_table_format)
            sheet.write(i + row,7,dict["SEGUNDO NOMBRE"],style_content_table_format)
            sheet.write(i + row,8,dict["centro de costo"],style_content_table_format)
            sheet.write(i + row,9,dict["zonal"],style_content_table_format)
            sheet.write(i + row,10,dict["area"],style_content_table_format)
            sheet.write(i + row,11,dict["cargo"],style_content_table_format)
            sheet.write(i + row,12,dict["banco"],style_content_table_format)
            sheet.write(i + row,13,dict["n cuenta"],style_content_table_format)
            sheet.write(i + row,14,dict["fecha de ingreso"],style_date_content_table_format)
            sheet.write(i + row,15,dict["FECHA CESE"],style_date_content_table_format)
            sheet.write(i + row,16,dict["number_periods"],style_content_table_format)
            sheet.write(i + row,17,dict["inicio de periodo"],style_date_content_table_format)
            sheet.write(i + row,18,dict["termino de periodo"],style_date_content_table_format)
            sheet.write(i + row,19,dict["fecha de pago"],style_date_content_table_format)
            
            sheet.write(i + row,20,dict["structure_type"],style_date_content_table_format)
            
            sheet.write(i + row,21,dict["basico"],style_money_content_table_format)
            sheet.write(i + row,22,dict["Asig Familiar"],style_money_content_table_format)

            for ind,col_name in enumerate(prom_columns):
                if col_name in dict:
                    sheet.write(i + row,23+ind,dict[col_name],style_money_content_table_format)
                    sum_list[ind] += dict[col_name]
                else :
                    sheet.write(i + row,23+ind,0,style_money_content_table_format)

            sheet.write(i + row,23+len_prom_columns,dict["Dias Laborados"],style_content_table_format)
            sheet.write(i + row,24+len_prom_columns,dict["Dias No Laborados"],style_content_table_format)
            sheet.write(i + row,25+len_prom_columns,dict["Dias Totales"],style_content_table_format)
            sheet.write(i + row,26+len_prom_columns,dict["Grati"],style_money_content_table_format)
            sheet.write(i + row,27+len_prom_columns,dict["health regimen"],style_money_content_table_format)
            sheet.write(i + row,28+len_prom_columns,dict["Grati + Bono"],style_money_content_table_format)
            sheet.write(i + row,29+len_prom_columns,dict["Descuento"],style_money_content_table_format)
            sheet.write(i + row,30+len_prom_columns,dict["Neto a Pagar"],style_money_content_table_format)
            count += 1
        
        sheet.write(count + row,0,"TOTAL",style_content_table_format_2)
        sheet.write(count + row,21,salary,style_content_table_format_2)
        sheet.write(count + row,22,family_asig,style_content_table_format_2)

        for ind,col_name in enumerate(prom_columns):
            sheet.write(count + row,23+ind,round(sum_list[ind],2),style_content_table_format_2)

        sheet.write(count + row,23+len_prom_columns,number_days ,style_content_table_format_2)
        sheet.write(count + row,24+len_prom_columns,number_leave_days,style_content_table_format_2)
        sheet.write(count + row,25+len_prom_columns,number_total,style_content_table_format_2)
        sheet.write(count + row,26+len_prom_columns,total,style_content_table_format_2)
        sheet.write(count + row,27+len_prom_columns,health_regimen,style_content_table_format_2)
        sheet.write(count + row,28+len_prom_columns,grati_bono,style_content_table_format_2)
        sheet.write(count + row,29+len_prom_columns,desc_grati,style_content_table_format_2)
        sheet.write(count + row,30+len_prom_columns,grati_neto,style_content_table_format_2)

        wb.close()
        output.seek(0)
        return output.read()
