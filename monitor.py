"""Jordan Tourism Monitor: standard-library collector and Windows desktop client."""
from email.utils import parsedate_to_datetime
import argparse, concurrent.futures, csv, datetime as dt, hashlib, json, pathlib, re, threading, urllib.parse, urllib.request, webbrowser, xml.etree.ElementTree as ET
QUERIES = ['"وزارة السياحة والآثار" الأردن', '"عماد حجازين"', '"هيئة تنشيط السياحة"', '"أردننا جنة"', 'السياحة الأردن', 'Jordan tourism', 'Jordan travel Petra Wadi Rum', 'Jordan tourism Aqaba Dead Sea Jerash']
JORDAN_TIME = dt.timezone(dt.timedelta(hours=3), 'Amman')
PERIODS = ('الكل', 'اليوم', 'آخر 3 ساعات', 'آخر 9 ساعات')
def publication_time(row):
    try:
        value = parsedate_to_datetime(row.get('published', ''))
        if value.tzinfo is None:
            return None
        return value.astimezone(dt.timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None

def matches_period(row, period, now=None):
    if period == 'الكل':
        return True
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(JORDAN_TIME)
    published = publication_time(row)
    if published is None or published > now:
        return False
    if period == 'اليوم':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now - dt.timedelta(hours={'آخر 3 ساعات': 3, 'آخر 9 ساعات': 9}[period])
    return start <= published <= now

def fetch(url):
    if urllib.parse.urlparse(url).scheme != 'https':
        raise ValueError('HTTPS is required')
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'JordanTourismMonitor/0.1'}), timeout=20) as r:
        return r.read(10_000_000)
def parse_feed(data, query):
    rows=[]
    for item in ET.fromstring(data).findall('./channel/item'):
        title=item.findtext('title','').strip(); link=item.findtext('link','').strip()
        if not title or urllib.parse.urlparse(link).scheme not in ('https','http'): continue
        rows.append(dict(id=hashlib.sha256(link.encode()).hexdigest(),title=title,url=link,source=item.findtext('source',''),published=item.findtext('pubDate',''),query=query,discovered=dt.datetime.now(dt.timezone.utc).isoformat()))
    return rows
def collect(previous=None):
    rows={r['id']:r for r in (previous or {}).get('items',[])}; status=[]
    def one(q):
        url='https://news.google.com/rss/search?'+urllib.parse.urlencode(dict(q=q+' when:7d',hl='ar',gl='JO',ceid='JO:ar'))
        try: return q,parse_feed(fetch(url),q),None
        except Exception as e: return q,[],str(e)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for q,items,error in pool.map(one,QUERIES):
            for r in items: rows.setdefault(r['id'],r)
            status.append(dict(query=q,count=len(items),error=error))
    return dict(updated=dt.datetime.now(dt.timezone.utc).isoformat(),items=sorted(rows.values(),key=lambda r:r['discovered'],reverse=True),sources=status,social_coverage='Not connected: Facebook, Instagram, X')
def desktop():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    root=tk.Tk(); root.title('رصد السياحة الأردنية — 0.2'); root.geometry('1150x720')
    cache=pathlib.Path.home()/'JordanTourismMonitor'; cache.mkdir(exist_ok=True); path=cache/'feed.json'
    state=json.loads(path.read_text('utf-8')) if path.exists() else {'items':[]}
    shown=[]; period=tk.StringVar(value='الكل'); count=tk.StringVar(); keyword=tk.StringVar(); endpoint=tk.StringVar(); note=tk.StringVar(value='الأخبار عبر RSS • فيسبوك وإنستغرام وX غير مربوطين بعد')
    ttk.Label(root,text='رصد السياحة الأردنية',font=('Arial',22)).pack(pady=12)
    bar=ttk.Frame(root); bar.pack(fill='x',padx=16)
    ttk.Label(bar,text='بحث').pack(side='right'); ttk.Entry(bar,textvariable=keyword,width=45).pack(side='right')
    ttk.Label(bar,text='الفترة').pack(side='right',padx=8)
    ttk.Combobox(bar,textvariable=period,values=PERIODS,state='readonly',width=18).pack(side='right')
    ttk.Label(root,textvariable=count).pack(pady=4)
    table=ttk.Treeview(root,columns=('title','source','published'),show='headings')
    for c,label,width in [('title','العنوان',650),('source','المصدر',180),('published','وقت النشر كما ورد من المصدر',270)]: table.heading(c,text=label); table.column(c,width=width)
    table.pack(fill='both',expand=True,padx=16,pady=10)
    def render(*_):
        table.delete(*table.get_children()); shown.clear()
        now = dt.datetime.now(dt.timezone.utc)
        for row in state['items']:
            if not matches_period(row, period.get(), now): continue
            if keyword.get().casefold() in (row['title']+' '+row['source']).casefold():
                shown.append(row); table.insert('', 'end',iid=str(len(shown)-1),values=(row['title'],row['source'],row['published']))
        count.set(f'المعروض: {len(shown)} من {len(state["items"])} | بتوقيت الأردن | حسب وقت النشر؛ التواريخ غير المعروفة تظهر في الكل فقط')
    def open_item(_):
        if table.selection(): webbrowser.open(shown[int(table.selection()[0])]['url'])
    table.bind('<Double-1>',open_item); keyword.trace_add('write',render); period.trace_add('write',render)
    def done(result):
        nonlocal state
        state=result; path.write_text(json.dumps(state,ensure_ascii=False),encoding='utf-8'); render()
        errors=sum(bool(x.get('error')) for x in state.get('sources',[]))
        note.set(f"المواد: {len(state['items'])} | آخر محاولة: {state.get('updated','')} | مصادر تعذّر تحديثها: {errors}")
        refresh.config(state='normal')
    def update():
        refresh.config(state='disabled'); note.set('جارٍ التحديث...')
        def work():
            try:
                result=json.loads(fetch(endpoint.get())) if endpoint.get().strip() else collect(state)
                if not isinstance(result.get('items'),list): raise ValueError('Invalid feed')
                root.after(0,lambda:done(result))
            except Exception as e:
                msg=str(e)
                def fail(): note.set(msg); refresh.config(state='normal')
                root.after(0,fail)
        threading.Thread(target=work,daemon=True).start()
    def export():
        target=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if target:
            with open(target,'w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f); w.writerow(['العنوان','المصدر','وقت النشر','الرابط'])
                for r in shown: w.writerow([r['title'],r['source'],r['published'],r['url']])
    refresh=ttk.Button(bar,text='تحديث',command=update); refresh.pack(side='left'); ttk.Button(bar,text='تصدير CSV',command=export).pack(side='left')
    ttk.Label(root,text='رابط HTTPS لنتائج الخدمة السحابية (اختياري؛ تركه فارغًا يجمع الأخبار على الجهاز)').pack()
    ttk.Entry(root,textvariable=endpoint,width=100).pack(pady=5); ttk.Label(root,textvariable=note,wraplength=1050).pack(pady=8)
    def tick():
        render()
        root.after(60000, tick)
    tick(); root.mainloop()
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--collect',action='store_true'); p.add_argument('--output',default='feed.json'); a=p.parse_args()
    if a.collect:
        dest=pathlib.Path(a.output); previous=json.loads(dest.read_text('utf-8')) if dest.exists() else None
        result=collect(previous); dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        if all(s['error'] for s in result['sources']): raise SystemExit('All sources failed; see feed.json')
    else: desktop()
