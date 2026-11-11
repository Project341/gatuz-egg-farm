from database import connect
def summary(start='0001-01-01',end='9999-12-31'):
 with connect() as c:
  q=lambda sql,args=():c.execute(sql,args).fetchone()[0]
  return {'eggs':q('SELECT COALESCE(SUM(small+medium+large+jumbo+cracked+dirty),0) FROM production WHERE collection_date BETWEEN ? AND ?',(start,end)), 'sold':q("SELECT COALESCE(SUM(quantity*CASE unit WHEN 'tray' THEN 30 ELSE 1 END),0) FROM sales WHERE sale_date BETWEEN ? AND ?",(start,end)), 'revenue':q('SELECT COALESCE(SUM(total),0) FROM sales WHERE sale_date BETWEEN ? AND ?',(start,end)), 'expenses':q('SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date BETWEEN ? AND ?',(start,end)), 'stock':q('SELECT COALESCE(SUM(quantity),0) FROM inventory'), 'chickens':q("SELECT COALESCE(SUM(quantity),0) FROM chickens WHERE status='Active'")}
def export_excel(path,start='0001-01-01',end='9999-12-31'):
 from openpyxl import Workbook
 from openpyxl.styles import Font,PatternFill
 w=Workbook(); s=w.active; s.title='Summary'; s.append(['EGG FARM GATUZ REPORT']); s.append(['Metric','Value'])
 for k,v in summary(start,end).items(): s.append([k.title(),v])
 with connect() as c:
  for table in ('extensions','chickens','production','inventory','sales','customers','expenses','suppliers','feed_items','feed_tx','mortality'):
   sh=w.create_sheet(table[:31]); cur=c.execute('SELECT * FROM '+table); sh.append([x[0] for x in cur.description]); [sh.append(list(r)) for r in cur.fetchall()]
 for sh in w:
  sh.freeze_panes='A2'
  for x in sh[1]: x.font=Font(bold=True,color='FFFFFF'); x.fill=PatternFill('solid',fgColor='174B35')
  for col in sh.columns: sh.column_dimensions[col[0].column_letter].width=min(34,max(12,max(len(str(x.value or '')) for x in col)+2))
 w.save(path)
def export_pdf(path,start='0001-01-01',end='9999-12-31'):
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer
 from reportlab.lib import colors
 from reportlab.lib.styles import getSampleStyleSheet
 s=summary(start,end); data=[['Metric','Value']]+[[k.title(),str(v)] for k,v in s.items()]
 t=Table(data,colWidths=[250,200]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#174B35')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.5,colors.grey),('PADDING',(0,0),(-1,-1),8)]))
 SimpleDocTemplate(str(path)).build([Paragraph('EGG FARM GATUZ - FARM REPORT',getSampleStyleSheet()['Title']),Spacer(1,12),t])
