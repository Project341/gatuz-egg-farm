import customtkinter as ctk
from tkinter import ttk,messagebox,filedialog,Canvas
from datetime import date,datetime
from database import *
from security import *
from reports import summary,export_excel,export_pdf
ctk.set_appearance_mode('dark'); ctk.set_default_color_theme('green')
GREEN='#174B35'; DARK='#061F17'; BG='#061F17'; PANEL='#0B2D20'; PANEL2='#103725'; GOLD='#E1C45A'; MINT='#83C9A5'; MUTED='#8CA99A'; BORDER='#194A35'
class App(ctk.CTk):
 def __init__(self):
  super().__init__(); self.title('EGG FARM GATUZ | Poultry Farm Management System'); self.geometry('1440x920'); self.minsize(1100,720); self.user=None; self.login()
 def clear(self):
  for w in self.winfo_children():w.destroy()
 def login(self):
  self.clear(); self.configure(fg_color=BG); f=ctk.CTkFrame(self,width=420,height=460); f.place(relx=.5,rely=.5,anchor='center')
  ctk.CTkLabel(f,text='🥚 EGG FARM GATUZ',font=('Arial',28,'bold'),text_color=GREEN).pack(pady=(48,8)); ctk.CTkLabel(f,text='POULTRY FARM MANAGEMENT SYSTEM',text_color='gray').pack(pady=(0,28))
  self.un=ctk.CTkEntry(f,width=300,height=42,placeholder_text='Username'); self.un.pack(pady=8); self.pw=ctk.CTkEntry(f,width=300,height=42,placeholder_text='Password',show='•'); self.pw.pack(pady=8); self.pw.bind('<Return>',lambda e:self.do_login())
  ctk.CTkButton(f,text='LOGIN',width=300,height=42,fg_color=GREEN,command=self.do_login).pack(pady=20); ctk.CTkLabel(f,text='First login: admin / admin123\nChange this password after login.',text_color='gray').pack()
 def do_login(self):
  with connect() as c:r=c.execute('SELECT * FROM users WHERE username=? AND active=1',(self.un.get().strip(),)).fetchone()
  if r and verify_password(self.pw.get(),r['password_hash'],r['salt']):self.user=dict(r); audit(r['id'],'LOGIN'); self.shell()
  else:messagebox.showerror('Login failed','Invalid username or password.')
 def shell(self):
  self.clear(); self.configure(fg_color=BG)
  side=ctk.CTkFrame(self,width=225,corner_radius=0,fg_color='#041B13',border_width=0); side.pack(side='left',fill='y'); side.pack_propagate(False)
  brand=ctk.CTkFrame(side,fg_color='transparent'); brand.pack(fill='x',padx=16,pady=(22,18))
  ctk.CTkLabel(brand,text='♧  GATUZ',font=('Arial',22,'bold'),text_color=GOLD).pack(anchor='w')
  ctk.CTkLabel(brand,text='EGG FARM MANAGEMENT',font=('Arial',9,'bold'),text_color=MUTED).pack(anchor='w',padx=35,pady=(0,0))
  ctk.CTkLabel(side,text=f"{self.user['username']}  •  {self.user['role']}",text_color='#C3D6CA',font=('Arial',10)).pack(anchor='w',padx=18,pady=(0,18))
  nav=[('▦','Dashboard'),('▣','Extensions'),('♧','Chickens'),('◉','Egg Production'),('◌','Egg Inventory'),('₱','Sales'),('♙','Customers'),('▤','Expenses'),('▥','Feed Items'),('♧','Suppliers'),('▧','Reports'),('⚙','Users'),('▣','Backup / Restore')]
  for ico,n in nav:
   if n=='Users' and self.user['role']!='ADMIN':continue
   active=(n=='Dashboard')
   b=ctk.CTkButton(side,text=f'  {ico}    {n}',anchor='w',height=38,corner_radius=9,fg_color=('#183D2B' if active else 'transparent'),hover_color='#194B34',text_color=(GOLD if active else '#A9C2B3'),font=('Arial',12,'bold' if active else 'normal'),command=lambda x=n:self.open(x))
   b.pack(fill='x',padx=9,pady=2)
  ctk.CTkButton(side,text='Change Password',height=34,fg_color='#173B2A',hover_color='#24543B',command=self.change_password).pack(side='bottom',fill='x',padx=10,pady=(4,6))
  ctk.CTkButton(side,text='↪  Logout',height=34,fg_color='#713D35',hover_color='#8B4A40',command=self.logout).pack(side='bottom',fill='x',padx=10,pady=(4,4))
  self.body=ctk.CTkFrame(self,fg_color=BG,corner_radius=0); self.body.pack(side='left',fill='both',expand=True,padx=(22,24),pady=(16,16)); self.dashboard()
 def heading(self,title,sub=''):
  ctk.CTkLabel(self.body,text=title,font=('Arial',27,'bold'),text_color='#E9D27C').pack(anchor='w',pady=(3,2))
  if sub:ctk.CTkLabel(self.body,text=sub,text_color='gray').pack(anchor='w',pady=(0,14))
 def open(self,n):
  if n=='Dashboard':return self.dashboard()
  if n=='Egg Production':return self.production()
  if n=='Egg Inventory':return self.inventory()
  if n=='Sales':return self.sales()
  if n=='Reports':return self.report_page()
  if n=='Backup / Restore':return self.backup_page()
  if n=='Users':return self.users()
  mapping={'Extensions':('extensions',['code','name','location','breed','established','status','notes']), 'Chickens':('chickens',['chicken_code','breed','quantity','age_months','acquired_date','laying_hens','extension_id','status','notes']), 'Customers':('customers',['name','contact','address','notes']), 'Expenses':('expenses',['expense_date','category','description','amount','extension_id']), 'Suppliers':('suppliers',['name','contact','address','products','notes']), 'Feed Items':('feed_items',['name','feed_type','unit','stock','low_stock','cost_per_unit'])}
  if n in mapping:return self.crud(n,*mapping[n])
 def dashboard(self):
  for w in self.body.winfo_children():w.destroy()
  # Dashboard content is scrollable so it remains usable on smaller monitors.
  root=ctk.CTkScrollableFrame(self.body,fg_color=BG,corner_radius=0,scrollbar_button_color='#315B43',scrollbar_button_hover_color=GOLD)
  root.pack(fill='both',expand=True)
  today=date.today().isoformat(); month_key=date.today().strftime('%Y-%m'); s=summary(today,today)
  with connect() as c:
   month=c.execute("SELECT COALESCE(SUM(small+medium+large+jumbo+cracked+dirty),0) FROM production WHERE substr(collection_date,1,7)=?",(month_key,)).fetchone()[0]
   extensions=c.execute("SELECT id,code,name,location,breed,status FROM extensions ORDER BY id LIMIT 3").fetchall()
   inv=c.execute("SELECT category,quantity FROM inventory WHERE category IN ('Small','Medium','Large','Jumbo','Cracked Eggs') ORDER BY CASE category WHEN 'Small' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Large' THEN 3 WHEN 'Jumbo' THEN 4 WHEN 'Cracked Eggs' THEN 5 END").fetchall()
   low=c.execute('SELECT name,stock,unit FROM feed_items WHERE stock<=low_stock ORDER BY stock').fetchall()
   recent=c.execute('SELECT action,details,created_at FROM audit_log ORDER BY id DESC LIMIT 4').fetchall()
   daily=c.execute("SELECT collection_date,COALESCE(SUM(small+medium+large+jumbo+cracked+dirty),0) total FROM production WHERE collection_date>=date('now','-6 days') GROUP BY collection_date ORDER BY collection_date").fetchall()
   monthly_sales=c.execute("SELECT substr(sale_date,1,7) m,COALESCE(SUM(total),0) total FROM sales WHERE sale_date>=date('now','-4 months') GROUP BY substr(sale_date,1,7) ORDER BY m").fetchall()
  header=ctk.CTkFrame(root,fg_color='transparent');header.pack(fill='x',pady=(2,18))
  left=ctk.CTkFrame(header,fg_color='transparent');left.pack(side='left',fill='x',expand=True)
  ctk.CTkLabel(left,text='GATUZ EGG FARM',font=('Arial',25,'bold'),text_color='#F0D77B').pack(anchor='w')
  ctk.CTkLabel(left,text='Smart Farming. Better Tomorrow.',font=('Arial',11),text_color=MUTED).pack(anchor='w',pady=(2,0))
  right=ctk.CTkFrame(header,fg_color=PANEL,corner_radius=18,border_width=1,border_color=BORDER);right.pack(side='right',anchor='ne',padx=4,pady=5)
  ctk.CTkLabel(right,text=f"{datetime.now():%a, %B %d, %Y}   •   {self.user['username']} — {self.user['role']}",font=('Arial',10),text_color='#D5E5DA').pack(padx=14,pady=10)
  ctk.CTkLabel(root,text='Farm Management',font=('Arial',18,'bold'),text_color='#E9D27C').pack(anchor='w')
  ctk.CTkLabel(root,text='Choose a farm extension to see its operations at a glance.',font=('Arial',10),text_color=MUTED).pack(anchor='w',pady=(1,9))
  farms=ctk.CTkFrame(root,fg_color='transparent');farms.pack(fill='x',pady=(0,18))
  for i in range(4):farms.grid_columnconfigure(i,weight=1,uniform='farm')
  if extensions:
   for i,e in enumerate(extensions):
    card=ctk.CTkFrame(farms,fg_color=PANEL,corner_radius=13,border_width=1,border_color=(GOLD if i==0 else BORDER));card.grid(row=0,column=i,sticky='nsew',padx=(0 if i==0 else 7,7),pady=2)
    ctk.CTkLabel(card,text='♧',font=('Arial',22,'bold'),text_color=GOLD).pack(anchor='w',padx=13,pady=(10,0))
    ctk.CTkLabel(card,text=e['name'],font=('Arial',12,'bold'),text_color='#E2EEE6').pack(anchor='w',padx=13,pady=(2,0))
    ctk.CTkLabel(card,text=e['location'] or 'Farm extension',font=('Arial',9),text_color=MUTED).pack(anchor='w',padx=13,pady=(0,7))
    ctk.CTkLabel(card,text=(e['breed'] or 'Poultry')+'  •  '+(e['status'] or 'Active'),font=('Arial',9),text_color=GOLD).pack(anchor='w',padx=13,pady=(0,11))
  else:
   card=ctk.CTkFrame(farms,fg_color=PANEL,corner_radius=13,border_width=1,border_color=BORDER);card.grid(row=0,column=0,sticky='ew',padx=(0,7));ctk.CTkLabel(card,text='No farm extension yet',text_color='#E2EEE6',font=('Arial',12,'bold')).pack(padx=18,pady=18)
  add=ctk.CTkButton(farms,text='+  Add New Farm',height=105,fg_color='#102B20',hover_color='#1B4932',border_width=1,border_color=GOLD,text_color=GOLD,corner_radius=13,command=lambda:self.open('Extensions'));add.grid(row=0,column=3,sticky='nsew',padx=(7,0),pady=2)
  ctk.CTkLabel(root,text='Farm Overview',font=('Arial',18,'bold'),text_color='#E9D27C').pack(anchor='w',pady=(0,2))
  ctk.CTkLabel(root,text='All active farm operations • Live database summary',font=('Arial',10),text_color=MUTED).pack(anchor='w',pady=(0,8))
  cards=[('Total Chickens',f"{s['chickens']:,}",'♧'),('Eggs Collected Today',f"{s['eggs']:,}",'◉'),('Eggs This Month',f'{month:,}','▦'),('Egg Inventory',f"{s['stock']:,}",'◌'),('Eggs Sold Today',f"{s['sold']:,}",'▤'),('Sales Today',f"₱{s['revenue']:,.2f}",'₱'),('Expenses Today',f"₱{s['expenses']:,.2f}",'↘'),('Net Profit Today',f"₱{s['revenue']-s['expenses']:,.2f}",'↗')]
  metrics=ctk.CTkFrame(root,fg_color='transparent');metrics.pack(fill='x')
  for i,(label,value,ico) in enumerate(cards):
   metrics.grid_columnconfigure(i%4,weight=1,uniform='metric')
   card=ctk.CTkFrame(metrics,fg_color=PANEL,corner_radius=13,border_width=1,border_color=BORDER);card.grid(row=i//4,column=i%4,sticky='nsew',padx=(0 if i%4==0 else 6,6),pady=5)
   top=ctk.CTkFrame(card,fg_color='transparent');top.pack(fill='x',padx=12,pady=(10,0));ctk.CTkLabel(top,text=label,font=('Arial',9),text_color=MUTED).pack(side='left');ctk.CTkLabel(top,text=ico,font=('Arial',15,'bold'),text_color=GOLD).pack(side='right')
   ctk.CTkLabel(card,text=value,font=('Arial',21,'bold'),text_color='#E3F0E8').pack(anchor='w',padx=12,pady=(5,0));ctk.CTkLabel(card,text='↗  Current farm total',font=('Arial',8),text_color=MINT).pack(anchor='w',padx=12,pady=(0,10))
  # Two-column dashboard panels
  panels=ctk.CTkFrame(root,fg_color='transparent');panels.pack(fill='x',pady=(6,0));panels.grid_columnconfigure(0,weight=2);panels.grid_columnconfigure(1,weight=1)
  def panel(parent,title,row,col,span=1):
   box=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=13,border_width=1,border_color=BORDER);box.grid(row=row,column=col,columnspan=span,sticky='nsew',padx=(0,7) if col==0 else (7,0),pady=5);ctk.CTkLabel(box,text=title,font=('Arial',13,'bold'),text_color='#E9D27C').pack(anchor='w',padx=14,pady=(12,8));return box
  prod=panel(panels,'Egg Production — Last 7 Days',0,0);summarybox=panel(panels,'Egg Production Summary',0,1)
  chart=Canvas(prod,height=165,bg=PANEL,highlightthickness=0);chart.pack(fill='x',padx=12,pady=(0,8))
  vals=[int(x['total']) for x in daily]; labels=[x['collection_date'][5:] for x in daily]
  if not vals: vals=[0,0,0,0,0,0,0];labels=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
  w=560;h=165;chart.configure(height=h);mx=max(vals+[1]);chart.update_idletasks();w=max(chart.winfo_width(),420)
  for j in range(4):
   y=18+j*36;chart.create_line(28,y,w-12,y,fill='#1A4935');chart.create_text(8,y,text=str(round(mx*(3-j)/3)),fill=MUTED,anchor='w',font=('Arial',7))
  pts=[]
  for i,v in enumerate(vals):
   x=38+i*(max(w-70,100)/max(len(vals)-1,1));y=126-(v/mx)*105;pts.extend([x,y]);chart.create_oval(x-3,y-3,x+3,y+3,fill=GOLD,outline=GOLD);chart.create_text(x,145,text=labels[i] if i<len(labels) else '',fill=MUTED,font=('Arial',8))
  if len(pts)>=4:chart.create_line(*pts,fill=GOLD,width=2,smooth=True)
  for label,value in [("Today's Production",f"{s['eggs']:,} eggs"),('Average per Day',f"{(sum(vals)/len(vals)) if vals else 0:,.1f} eggs"),('Monthly Production',f'{month:,} eggs')]:
   line=ctk.CTkFrame(summarybox,fg_color='transparent');line.pack(fill='x',padx=14,pady=8);ctk.CTkLabel(line,text=label,font=('Arial',9),text_color=MUTED).pack(side='left');ctk.CTkLabel(line,text=value,font=('Arial',12,'bold'),text_color='#E3F0E8').pack(side='right');ctk.CTkFrame(summarybox,height=1,fg_color=BORDER).pack(fill='x',padx=14)
  invbox=panel(panels,'Egg Inventory by Category',1,0);topbox=panel(panels,'Low Stock Notifications',1,1)
  invwrap=ctk.CTkFrame(invbox,fg_color='transparent');invwrap.pack(fill='x',padx=10,pady=(0,12))
  if inv:
   for i,r in enumerate(inv):
    cell=ctk.CTkFrame(invwrap,fg_color=PANEL2,corner_radius=9);cell.grid(row=0,column=i,sticky='ew',padx=3);invwrap.grid_columnconfigure(i,weight=1);ctk.CTkLabel(cell,text=f"{r['quantity']:,}",font=('Arial',16,'bold'),text_color=GOLD).pack(pady=(10,0));ctk.CTkLabel(cell,text=r['category'],font=('Arial',8),text_color=MUTED).pack(pady=(0,10))
  if low:
   for r in low[:4]:ctk.CTkLabel(topbox,text=f"⚠  {r['name']}  —  {r['stock']:g} {r['unit']}",font=('Arial',9),text_color='#E8C76B').pack(anchor='w',padx=14,pady=5)
  else:ctk.CTkLabel(topbox,text='✓  Feed stock levels look good.',font=('Arial',9),text_color=MINT).pack(anchor='w',padx=14,pady=10)
  salesbox=panel(panels,'Sales & Receipts',2,0);activity=panel(panels,'Recent Activities',2,1)
  saleschart=Canvas(salesbox,height=145,bg=PANEL,highlightthickness=0);saleschart.pack(fill='x',padx=12,pady=(0,10));months=[r['m'][-2:] for r in monthly_sales];amounts=[float(r['total']) for r in monthly_sales]
  if not amounts:months=['—'];amounts=[0]
  peak=max(amounts+[1]);sw=560;saleschart.update_idletasks();sw=max(saleschart.winfo_width(),420)
  for i,(m,a) in enumerate(zip(months,amounts)):
   x=42+i*(max(sw-90,100)/max(len(amounts)-1,1));barh=(a/peak)*90;saleschart.create_rectangle(x-7,112-barh,x+7,112,fill=GOLD,outline='');saleschart.create_text(x,127,text=m,fill=MUTED,font=('Arial',8))
  if recent:
   for r in recent[:4]:
    ctk.CTkLabel(activity,text='•  '+(r['action'] or 'Activity')+'  '+(r['details'] or ''),font=('Arial',9),text_color='#D5E5DA',wraplength=260,justify='left').pack(anchor='w',padx=14,pady=(4,0));ctk.CTkLabel(activity,text=(r['created_at'] or '')[:16],font=('Arial',8),text_color=MUTED).pack(anchor='w',padx=27,pady=(0,5))
  else:ctk.CTkLabel(activity,text='No recent activity yet.',font=('Arial',9),text_color=MUTED).pack(anchor='w',padx=14,pady=12)
  if low:
   warn=ctk.CTkFrame(root,fg_color='#3A3017',corner_radius=10);warn.pack(fill='x',pady=(10,4));ctk.CTkLabel(warn,text='⚠  LOW STOCK: '+', '.join(x['name'] for x in low),font=('Arial',10,'bold'),text_color='#F0D77B').pack(anchor='w',padx=14,pady=10)
  ctk.CTkLabel(root,text='GATUZ EGG FARM  •  Your farm records are saved locally on this computer.',font=('Arial',9),text_color='#6F9180').pack(pady=(18,10))
 def table(self,parent,cols,rows):
  fr=ctk.CTkFrame(parent,fg_color='white');fr.pack(fill='both',expand=True,pady=10);tv=ttk.Treeview(fr,columns=cols,show='headings',height=15)
  for x in cols:tv.heading(x,text=x.replace('_',' ').title());tv.column(x,width=125)
  sb=ttk.Scrollbar(fr,orient='vertical',command=tv.yview);tv.configure(yscrollcommand=sb.set);tv.pack(side='left',fill='both',expand=True);sb.pack(side='right',fill='y')
  for r in rows:tv.insert('','end',values=tuple(r))
  return tv
 def crud(self,label,table,cols):
  for w in self.body.winfo_children():w.destroy()
  self.heading(label); search=ctk.CTkEntry(self.body,placeholder_text='Search...');search.pack(anchor='w');area=ctk.CTkFrame(self.body,fg_color='transparent');area.pack(fill='both',expand=True);sel={'id':None}
  def refresh():
   for w in area.winfo_children():w.destroy()
   with connect() as c:
    if search.get():
     wh=' OR '.join(f'CAST({x} AS TEXT) LIKE ?' for x in cols); rows=c.execute(f'SELECT * FROM {table} WHERE {wh} ORDER BY id DESC',tuple(['%'+search.get()+'%']*len(cols))).fetchall()
    else:rows=c.execute(f'SELECT * FROM {table} ORDER BY id DESC').fetchall()
   tv=self.table(area,['id']+cols,rows);tv.bind('<<TreeviewSelect>>',lambda e:sel.update(id=tv.item(tv.selection()[0])['values'][0]) if tv.selection() else None)
  def form(edit=False):
   win=ctk.CTkToplevel(self);win.title(('Edit ' if edit else 'Add ')+label);win.geometry('460x650');win.grab_set();old=None
   if edit and sel['id']:
    with connect() as c:old=c.execute(f'SELECT * FROM {table} WHERE id=?',(sel['id'],)).fetchone()
   es=[]
   for col in cols:
    ctk.CTkLabel(win,text=col.replace('_',' ').title()).pack(anchor='w',padx=20,pady=(6,0));e=ctk.CTkEntry(win,width=410);e.pack(padx=20,pady=3)
    if old and old[col] is not None:e.insert(0,str(old[col]))
    es.append(e)
   def save():
    try:
     vals=[e.get().strip() or None for e in es]
     for i,col in enumerate(cols):
      if col in ('quantity','age_months','laying_hens','extension_id') and vals[i] is not None:vals[i]=int(vals[i])
      if col in ('amount','stock','low_stock','cost_per_unit') and vals[i] is not None:vals[i]=float(vals[i])
     with connect() as c:
      if edit:c.execute('UPDATE '+table+' SET '+','.join(x+'=?' for x in cols)+' WHERE id=?',(*vals,sel['id']))
      else:c.execute('INSERT INTO '+table+'('+','.join(cols)+') VALUES('+','.join('?' for _ in cols)+')',vals)
     audit(self.user['id'],'SAVE',label);win.destroy();refresh()
    except Exception as e:messagebox.showerror('Save error',str(e),parent=win)
   ctk.CTkButton(win,text='Save Record',command=save,fg_color=GREEN).pack(pady=15)
  bar=ctk.CTkFrame(self.body,fg_color='transparent');bar.pack(anchor='w',pady=5);ctk.CTkButton(bar,text='Add New',command=lambda:form()).pack(side='left',padx=3);ctk.CTkButton(bar,text='Edit Selected',command=lambda:form(True)).pack(side='left',padx=3)
  def delete():
   if self.user['role']!='ADMIN':messagebox.showwarning('Permission','Admin only.');return
   if sel['id'] and messagebox.askyesno('Confirm','Delete selected record?'):
    try:
     with connect() as c:c.execute(f'DELETE FROM {table} WHERE id=?',(sel['id'],))
     refresh()
    except Exception as e:messagebox.showerror('Delete blocked',str(e))
  ctk.CTkButton(bar,text='Delete',fg_color='#91443B',command=delete).pack(side='left',padx=3);ctk.CTkButton(bar,text='Refresh',command=refresh).pack(side='left',padx=3);search.bind('<KeyRelease>',lambda e:refresh());refresh()
 def production(self):
  for w in self.body.winfo_children():w.destroy()
  self.heading('Egg Production','Record one morning and one afternoon collection per extension per day.');
  with connect() as c:ext=c.execute("SELECT id,name FROM extensions WHERE status='Active'").fetchall()
  if not ext:ctk.CTkLabel(self.body,text='Add an extension first.').pack();return
  f=ctk.CTkFrame(self.body);f.pack(fill='x',pady=10);opts=[f"{r['id']} - {r['name']}" for r in ext];ex=ctk.CTkOptionMenu(f,values=opts);ex.grid(row=0,column=0,padx=6,pady=8);dt=ctk.CTkEntry(f,width=120);dt.insert(0,date.today().isoformat());dt.grid(row=0,column=1,padx=6);shift=ctk.CTkOptionMenu(f,values=['Morning','Afternoon']);shift.grid(row=0,column=2,padx=6);es=[]
  for i,cat in enumerate(['Small','Medium','Large','Jumbo','Cracked Eggs']):ctk.CTkLabel(f,text=cat).grid(row=1,column=i*2,padx=5);e=ctk.CTkEntry(f,width=80);e.insert(0,'0');e.grid(row=1,column=i*2+1,padx=5);es.append(e)
  area=ctk.CTkFrame(self.body,fg_color='transparent');area.pack(fill='both',expand=True)
  def refresh():
   for w in area.winfo_children():w.destroy()
   with connect() as c:rows=c.execute('SELECT p.id,e.name,p.collection_date,p.shift,p.small,p.medium,p.large,p.jumbo,p.cracked,(p.small+p.medium+p.large+p.jumbo+p.cracked+p.dirty) total FROM production p JOIN extensions e ON e.id=p.extension_id ORDER BY p.collection_date DESC,p.id DESC').fetchall()
   self.table(area,['id','extension','date','shift','small','medium','large','jumbo','cracked','total'],rows)
  def save():
   try:n=add_production(int(ex.get().split(' - ')[0]),dt.get(),shift.get(),*[int(x.get()) for x in es],self.user['id']);audit(self.user['id'],'PRODUCTION',str(n));messagebox.showinfo('Saved',f'{n} eggs added to inventory.');refresh()
   except Exception as e:messagebox.showerror('Production error',str(e))
  ctk.CTkButton(f,text='Save Collection',command=save,fg_color=GREEN).grid(row=2,column=0,pady=10);refresh()
 def inventory(self):
  for w in self.body.winfo_children():w.destroy()
  self.heading('Egg Inventory','Stock tracked in individual pieces; one tray = 30 pieces.');f=ctk.CTkFrame(self.body);f.pack(fill='x',pady=10);cat=ctk.CTkOptionMenu(f,values=['Small','Medium','Large','Jumbo','Cracked Eggs']);cat.pack(side='left',padx=5,pady=10);qty=ctk.CTkEntry(f,placeholder_text='Quantity (pieces)',width=150);qty.pack(side='left',padx=5);kind=ctk.CTkOptionMenu(f,values=['Damage','Discard','Adjustment In','Adjustment Out']);kind.pack(side='left',padx=5);notes=ctk.CTkEntry(f,placeholder_text='Notes',width=200);notes.pack(side='left',padx=5)
  def refresh():
   for w in area.winfo_children():w.destroy()
   with connect() as c:rows=c.execute('SELECT category,quantity FROM inventory').fetchall();tx=c.execute('SELECT id,category,quantity,tx_type,tx_date,reference,notes FROM inventory_tx ORDER BY id DESC LIMIT 100').fetchall()
   self.table(area,['category','quantity'],rows);self.table(area,['id','category','quantity','tx_type','tx_date','reference','notes'],tx)
  def post():
   try:adjust_inventory(cat.get(),qty.get(),kind.get(),date.today().isoformat(),self.user['id'],notes.get());refresh()
   except Exception as e:messagebox.showerror('Inventory error',str(e))
  ctk.CTkButton(f,text='Post Adjustment',command=post).pack(side='left',padx=5);area=ctk.CTkFrame(self.body,fg_color='transparent');area.pack(fill='both',expand=True);refresh()
 def sales(self):
  for w in self.body.winfo_children():w.destroy()
  self.heading('Sales','Enter quantity in pieces or trays. Tray stock deduction is 30 pieces.');f=ctk.CTkFrame(self.body);f.pack(fill='x',pady=10);entries={}
  for i,(k,ph) in enumerate([('customer','Customer ID optional'),('date','YYYY-MM-DD'),('qty','Quantity'),('price','Price per unit'),('paid','Amount paid')]):
   e=ctk.CTkEntry(f,placeholder_text=ph,width=155);e.grid(row=i//3,column=i%3,padx=6,pady=8);entries[k]=e
  entries['date'].insert(0,date.today().isoformat());cat=ctk.CTkOptionMenu(f,values=['Small','Medium','Large','Jumbo']);cat.grid(row=0,column=3,padx=5);unit=ctk.CTkOptionMenu(f,values=['piece','tray']);unit.grid(row=1,column=3,padx=5);notes=ctk.CTkEntry(f,placeholder_text='Notes');notes.grid(row=2,column=3,padx=5)
  area=ctk.CTkFrame(self.body,fg_color='transparent');area.pack(fill='both',expand=True)
  def refresh():
   for w in area.winfo_children():w.destroy()
   with connect() as c:rows=c.execute('SELECT id,invoice,customer_id,sale_date,category,quantity,unit,price_per_unit,total,paid,payment_status FROM sales ORDER BY id DESC').fetchall()
   self.table(area,['id','invoice','customer_id','sale_date','category','quantity','unit','price_per_unit','total','paid','payment_status'],rows)
  def save():
   try:cid=int(entries['customer'].get()) if entries['customer'].get().strip() else None;inv,total=record_sale(cid,entries['date'].get(),cat.get(),entries['qty'].get(),unit.get(),entries['price'].get(),entries['paid'].get() or 0,self.user['id'],notes.get());messagebox.showinfo('Sale recorded',f'{inv}\nTotal ₱{total:,.2f}\nInventory deducted.');refresh()
   except Exception as e:messagebox.showerror('Sales error',str(e))
  ctk.CTkButton(f,text='Record Sale',command=save,fg_color=GREEN).grid(row=3,column=0,pady=8);refresh()
 def report_page(self):
  for w in self.body.winfo_children():w.destroy()
  self.heading('Reports & Financial Summary');s=summary()
  for k,v in s.items():ctk.CTkLabel(self.body,text=f'{k.title()}: {v:,.2f}' if isinstance(v,float) else f'{k.title()}: {v:,}',font=('Arial',17,'bold')).pack(anchor='w',pady=4)
  f=ctk.CTkFrame(self.body);f.pack(anchor='w',pady=15);ctk.CTkButton(f,text='Export Excel',command=self.excel).pack(side='left',padx=5);ctk.CTkButton(f,text='Export PDF',command=self.pdf).pack(side='left',padx=5)
 def excel(self):
  p=filedialog.asksaveasfilename(defaultextension='.xlsx',filetypes=[('Excel','*.xlsx')])
  if p:
   try:export_excel(p);messagebox.showinfo('Export complete',p)
   except Exception as e:messagebox.showerror('Export error',str(e))
 def pdf(self):
  p=filedialog.asksaveasfilename(defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
  if p:
   try:export_pdf(p);messagebox.showinfo('Export complete',p)
   except Exception as e:messagebox.showerror('Export error',str(e))
 def backup_page(self):
  for w in self.body.winfo_children():w.destroy()
  self.heading('Backup & Restore',f'Database location: {DB_PATH}');ctk.CTkButton(self.body,text='Create Backup',command=self.backup).pack(anchor='w',pady=8);ctk.CTkButton(self.body,text='Restore Backup',fg_color='#91443B',command=self.restore).pack(anchor='w',pady=8)
 def backup(self):
  p=filedialog.asksaveasfilename(defaultextension='.db',initialfile='egg_farm_backup.db',filetypes=[('SQLite','*.db')])
  if p:
   try:backup_database(p);messagebox.showinfo('Backup complete',p)
   except Exception as e:messagebox.showerror('Backup error',str(e))
 def restore(self):
  p=filedialog.askopenfilename(filetypes=[('SQLite','*.db')])
  if p and messagebox.askyesno('Confirm','Current database will be backed up first. Restore selected backup?'):
   try:restore_database(p);messagebox.showinfo('Restored','Database restored. Please sign in again.');self.logout()
   except Exception as e:messagebox.showerror('Restore error',str(e))
 def users(self):
  for w in self.body.winfo_children():w.destroy()
  self.heading('User Management');f=ctk.CTkFrame(self.body);f.pack(fill='x',pady=8);u=ctk.CTkEntry(f,placeholder_text='Username');u.pack(side='left',padx=5,pady=10);p=ctk.CTkEntry(f,placeholder_text='Temporary password (8+)',show='•');p.pack(side='left',padx=5);role=ctk.CTkOptionMenu(f,values=['STAFF','ADMIN']);role.pack(side='left',padx=5)
  def add():
   try:
    if len(u.get().strip())<3 or len(p.get())<8:raise ValueError('Username 3+ chars; password 8+ chars.')
    h,s=make_password(p.get())
    with connect() as c:c.execute('INSERT INTO users(username,password_hash,salt,role,created_at) VALUES(?,?,?,?,?)',(u.get().strip(),h,s,role.get(),datetime.now().isoformat()))
    messagebox.showinfo('Created','User account created.');self.users()
   except Exception as e:messagebox.showerror('User error',str(e))
  ctk.CTkButton(f,text='Create User',command=add).pack(side='left',padx=5)
  with connect() as c:rows=c.execute('SELECT id,username,role,active,created_at FROM users ORDER BY id').fetchall()
  self.table(self.body,['id','username','role','active','created_at'],rows)
 def change_password(self):
  w=ctk.CTkToplevel(self);w.title('Change Password');w.geometry('350x270');w.grab_set();old=ctk.CTkEntry(w,placeholder_text='Current password',show='•');old.pack(pady=10);new=ctk.CTkEntry(w,placeholder_text='New password (8+)',show='•');new.pack(pady=10)
  def save():
   with connect() as c:r=c.execute('SELECT * FROM users WHERE id=?',(self.user['id'],)).fetchone()
   if not verify_password(old.get(),r['password_hash'],r['salt']):messagebox.showerror('Error','Incorrect current password.');return
   if len(new.get())<8:messagebox.showerror('Error','Password must be 8+ characters.');return
   h,s=make_password(new.get())
   with connect() as c:c.execute('UPDATE users SET password_hash=?,salt=? WHERE id=?',(h,s,self.user['id']))
   w.destroy();messagebox.showinfo('Updated','Password changed.')
  ctk.CTkButton(w,text='Update Password',command=save).pack(pady=12)
 def logout(self):audit(self.user['id'],'LOGOUT');self.user=None;self.login()
if __name__=='__main__':init_db();App().mainloop()
