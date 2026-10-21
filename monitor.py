"""Jordan Tourism Monitor: standard-library collector and Windows desktop client."""
from email.utils import parsedate_to_datetime
import html
import unicodedata
import queue
import argparse, concurrent.futures, csv, datetime as dt, hashlib, json, pathlib, re, threading, urllib.parse, urllib.request, webbrowser, xml.etree.ElementTree as ET
QUERIES = [
    '"وزارة السياحة والآثار" "الأردن"', '"عماد حجازين"',
    '"هيئة تنشيط السياحة"', '"أردننا جنة"', '"السياحة" "الأردن"',
    '"Jordan tourism"', '"Jordan travel" -"Michael Jordan" -"Jordan Brown" -"Jordan Baker"',
    '("Petra" OR "Wadi Rum" OR "Aqaba" OR "Jerash" OR "Dead Sea") (tourism OR hotel OR heritage OR visitors)',
    '"الأردن" (طيران OR فنادق OR آثار OR مهرجان OR زوار)',
    '"Jordan" (airport OR flights OR archaeology OR heritage OR hotels)'
]
JORDAN_TIME = dt.timezone(dt.timedelta(hours=3), 'Amman')
PERIODS = ('الكل', 'اليوم', 'أمس', 'آخر 3 ساعات', 'آخر 9 ساعات')
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
    if period == 'أمس':
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return end - dt.timedelta(days=1) <= published < end
    if period == 'اليوم':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now - dt.timedelta(hours={'آخر 3 ساعات': 3, 'آخر 9 ساعات': 9}[period])
    return start <= published <= now

def article_language(row):
    # Use the headline, excluding the publisher suffix. Mixed titles use the
    # dominant script; ambiguous titles remain visible in the All view.
    title = row.get('title', '').rsplit(' - ', 1)[0]
    arabic = sum('ARABIC' in unicodedata.name(c, '') and c.isalpha() for c in title)
    latin = sum('LATIN' in unicodedata.name(c, '') and c.isalpha() for c in title)
    if arabic > latin: return 'AR'
    if latin > arabic: return 'EN'
    return 'UNKNOWN'

def matches_language(row, language):
    return language == 'الكل / All' or article_language(row) == language

def normalized(text):
    text = unicodedata.normalize('NFKC', text).casefold()
    text = re.sub(r'[\u064b-\u065f\u0670ـ]', '', text)
    return text.translate(str.maketrans('أإآى', 'اااي'))

def has_terms(text, terms):
    return any(re.search(r'(?<!\w)' + re.escape(normalized(term)) + r'(?!\w)', text) for term in terms)

def relevance(row):
    # Queries and publisher names are not evidence that an article is about Jordan.
    title = row.get('title', '').rsplit(' - ', 1)[0]
    text = normalized(title + ' ' + row.get('summary', ''))
    official = has_terms(text, ['وزارة السياحة والآثار', 'هيئة تنشيط السياحة', 'أردننا جنة', 'عماد حجازين', 'Jordan Tourism Board', 'Jordan Ministry of Tourism'])
    destination = has_terms(text, ['Wadi Rum', 'Aqaba', 'Jerash', 'Ajloun', 'Madaba', 'Umm Qais', 'Umm al Jimal', 'Baptism Site', 'وادي رم', 'العقبة', 'جرش', 'عجلون', 'مادبا', 'أم قيس', 'أم الجمال', 'المغطس', 'البتراء', 'البترا'])
    # Petra alone may be a person's name; require Jordan or a tourism context below.
    country = has_terms(text, ['Jordan', 'Jordanian', 'الأردن', 'الأردنية', 'الأردني', 'الاردن'])
    direct = has_terms(text, ['tourism', 'tourist', 'tourists', 'travel', 'hotel', 'hotels', 'resort', 'resorts', 'destination', 'visitors', 'سياحة', 'السياحة', 'السياحي', 'السياحية', 'السياحيه', 'السياح', 'سياح', 'زوار', 'الزوار', 'فندق', 'فنادق', 'الفنادق', 'منتجع', 'المنتجعات'])
    indirect = has_terms(text, ['airport', 'flights', 'airline', 'heritage', 'archaeology', 'archaeological', 'festival', 'museum', 'conservation', 'nature reserve', 'مطار', 'المطار', 'الطيران', 'طيران', 'رحلات', 'تراث', 'التراث', 'آثار', 'الآثار', 'الأثرية', 'اثرية', 'مهرجان', 'مهرجانات', 'متحف', 'محمية', 'محميات'])
    person = bool(re.search(r'\bjordan\s+(brown|baker|spieth|pickford|henderson|love|poole|peele|peterson|chiles)\b|\bmichael jordan\b|\bair jordan\b', text))
    if official: return 'مباشر'
    if person and not destination: return 'مستبعد'
    if (country or destination) and direct: return 'مباشر'
    if (country or destination) and indirect: return 'غير مباشر'
    if destination or (has_terms(text, ['Petra']) and direct): return 'للمراجعة'
    if country and not person: return 'للمراجعة'
    return 'مستبعد'

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
        rows.append(dict(id=hashlib.sha256(link.encode()).hexdigest(),title=title,url=link,source=item.findtext('source',''),published=item.findtext('pubDate',''),summary=html.unescape(re.sub('<[^>]+>', ' ', item.findtext('description',''))),query=query,discovered=dt.datetime.now(dt.timezone.utc).isoformat()))
    return rows
def sorted_articles(rows):
    floor = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    return sorted(rows, key=lambda r: publication_time(r) or floor, reverse=True)

def collect(previous=None):
    rows={r['id']:r for r in (previous or {}).get('items',[])}; status=[]
    jobs = [(q, window) for window in ('1d', '7d') for q in QUERIES]
    def one(job):
        q, window = job
        english = q.isascii()
        url='https://news.google.com/rss/search?'+urllib.parse.urlencode(dict(q=q+' when:'+window,hl='en' if english else 'ar',gl='US' if english else 'JO',ceid='US:en' if english else 'JO:ar'))
        try: return q,parse_feed(fetch(url),q),None
        except Exception as e: return q,[],str(e)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for q,items,error in pool.map(one,jobs):
            for r in items:
                old = rows.get(r['id'])
                if old: r['discovered'] = old.get('discovered', r['discovered'])
                rows[r['id']] = r
            status.append(dict(query=q,count=len(items),error=error))
    return dict(updated=dt.datetime.now(dt.timezone.utc).isoformat(),items=sorted_articles(rows.values()),sources=status,social_coverage='Not connected: Facebook, Instagram, X')
def desktop():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    root=tk.Tk(); root.title('رصد السياحة الأردنية — 0.5'); root.geometry('1150x720')
    cache=pathlib.Path.home()/'JordanTourismMonitor'; cache.mkdir(exist_ok=True); path=cache/'feed.json'
    state=json.loads(path.read_text('utf-8')) if path.exists() else {'items':[]}
    inbox = queue.Queue()
    language=tk.StringVar(value='الكل / All')
    scope=tk.StringVar(value='مرتبط بالسياحة'); shown=[]; period=tk.StringVar(value='الكل'); count=tk.StringVar(); keyword=tk.StringVar(); endpoint=tk.StringVar(); note=tk.StringVar(value='الأخبار عبر RSS • فيسبوك وإنستغرام وX غير مربوطين بعد')
    ttk.Label(root,text='رصد السياحة الأردنية',font=('Arial',22)).pack(pady=12)
    bar=ttk.Frame(root); bar.pack(fill='x',padx=16)
    ttk.Label(bar,text='بحث').pack(side='right'); ttk.Entry(bar,textvariable=keyword,width=45).pack(side='right')
    ttk.Label(bar,text='الفترة').pack(side='right',padx=8)
    ttk.Combobox(bar,textvariable=period,values=PERIODS,state='readonly',width=18).pack(side='right')
    filters=ttk.Frame(root); filters.pack(fill='x',padx=16,pady=6)
    ttk.Label(filters,text='الصلة').pack(side='right',padx=8)
    ttk.Combobox(filters,textvariable=scope,values=('مرتبط بالسياحة', 'مباشر', 'غير مباشر', 'للمراجعة', 'مستبعد'),state='readonly',width=18).pack(side='right',padx=8)
    ttk.Label(filters,text='اللغة / Language').pack(side='right',padx=8)
    ttk.Combobox(filters,textvariable=language,values=('الكل / All', 'EN', 'AR'),state='readonly',width=14).pack(side='right')
    ttk.Label(root,textvariable=count).pack(pady=4)
    table=ttk.Treeview(root,columns=('title','source','published','relevance'),show='headings')
    for c,label,width in [('title','العنوان',650),('source','المصدر',180),('published','وقت النشر — الأردن',170),('relevance','الصلة',100)]: table.heading(c,text=label); table.column(c,width=width)
    table.pack(fill='both',expand=True,padx=16,pady=10)
    def render(*_):
        table.delete(*table.get_children()); shown.clear()
        now = dt.datetime.now(dt.timezone.utc)
        for row in sorted_articles(state['items']):
            label = relevance(row)
            if scope.get() == 'مرتبط بالسياحة':
                if label not in ('مباشر', 'غير مباشر'): continue
            elif label != scope.get(): continue
            if not matches_period(row, period.get(), now): continue
            if not matches_language(row, language.get()): continue
            if keyword.get().casefold() in (row['title']+' '+row['source']).casefold():
                shown.append(row); table.insert('', 'end',iid=str(len(shown)-1),values=(row['title'],row['source'],publication_time(row).astimezone(JORDAN_TIME).strftime('%Y-%m-%d %H:%M') if publication_time(row) else 'غير معروف',label))
        count.set(f'المعروض: {len(shown)} من {len(state["items"])} | بتوقيت الأردن | حسب وقت النشر؛ التواريخ غير المعروفة تظهر في الكل فقط')
    def open_item(_):
        if table.selection(): webbrowser.open(shown[int(table.selection()[0])]['url'])
    table.bind('<Double-1>',open_item); keyword.trace_add('write',render); period.trace_add('write',render); scope.trace_add('write',render); language.trace_add('write',render)
    def done(result):
        nonlocal state
        state=result; path.write_text(json.dumps(state,ensure_ascii=False),encoding='utf-8'); render()
        errors=sum(bool(x.get('error')) for x in state.get('sources',[]))
        today = sum(matches_period(r, 'اليوم') and relevance(r) in ('مباشر', 'غير مباشر') for r in state['items'])
        latest = next((publication_time(r) for r in sorted_articles(state['items']) if publication_time(r)), None)
        latest_label = latest.astimezone(JORDAN_TIME).strftime('%Y-%m-%d %H:%M') if latest else 'غير معروف'
        current = dt.datetime.now(JORDAN_TIME).strftime('%Y-%m-%d %H:%M')
        prefix = 'فشل جلب جميع عمليات البحث؛ المعروض أرشيف محفوظ' if errors and errors == len(state.get('sources', [])) else ('تحديث جزئي' if errors else 'تم التحديث')
        note.set(f"{prefix} | آخر محاولة على الجهاز: {current} | نتائج اليوم: {today} | أحدث خبر: {latest_label} | عمليات بحث متعذرة: {errors}")
        refresh.config(state='normal')
    def update():
        if str(refresh.cget('state')) == 'disabled': return
        refresh.config(state='disabled'); note.set('جارٍ جلب آخر الأخبار...')
        remote = endpoint.get().strip()
        snapshot = state
        def work():
            try:
                result=json.loads(fetch(remote)) if remote else collect(snapshot)
                if not isinstance(result.get('items'),list): raise ValueError('Invalid feed')
                inbox.put(('ok', result))
            except Exception as e:
                inbox.put(('error', str(e)))
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
    def poll():
        try:
            kind, payload = inbox.get_nowait()
            if kind == 'ok': done(payload)
            else:
                note.set('تعذّر التحديث؛ النتائج المعروضة محفوظة: ' + payload)
                refresh.config(state='normal')
        except queue.Empty: pass
        root.after(100, poll)
    def auto_refresh():
        update()
        root.after(15 * 60 * 1000, auto_refresh)
    def tick():
        render()
        root.after(60000, tick)
    tick(); poll(); root.after(300, auto_refresh); root.mainloop()
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--collect',action='store_true'); p.add_argument('--output',default='feed.json'); a=p.parse_args()
    if a.collect:
        dest=pathlib.Path(a.output); previous=json.loads(dest.read_text('utf-8')) if dest.exists() else None
        result=collect(previous); dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        if all(s['error'] for s in result['sources']): raise SystemExit('All sources failed; see feed.json')
    else: desktop()
