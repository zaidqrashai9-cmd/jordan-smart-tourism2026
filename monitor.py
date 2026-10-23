"""Jordan Tourism Monitor: standard-library collector and Windows desktop client."""
from email.utils import parsedate_to_datetime
import html
import unicodedata
import queue
import argparse, concurrent.futures, csv, datetime as dt, hashlib, json, pathlib, re, threading, urllib.parse, urllib.request, webbrowser, xml.etree.ElementTree as ET
# Search topics are independent of the small user-facing keyword dropdown.
SEARCH_TOPICS = {
 'ministry': {
  'ar': ['وزارة السياحة والآثار الأردنية', 'وزارة السياحة والاثار الاردنية', 'وزارة السياحة والآثار', 'وزارة السياحه والاثار', 'وزارة السياحة الأردنية'],
  'en': ['Jordan Ministry of Tourism', 'Jordanian Ministry of Tourism', 'Ministry of Tourism and Antiquities']},
 'minister_name': {
  'ar': ['عماد حجازين', 'عماد حجازي', 'عماد الحجازين'],
  'en': ['Imad Hijazin', 'Emad Hijazin', 'Imad Hijazeen', 'Emad Hijazeen', 'Imad Hijazine', 'Emad Hijazine', 'Imad Hijazi', 'Emad Hijazi']},
 'minister_title': {
  'ar': ['وزير السياحة والآثار الدكتور عماد حجازين', 'وزير السياحة والاثار عماد حجازين', 'وزير السياحة عماد حجازين', 'الدكتور عماد حجازين', 'د. عماد حجازين'],
  'en': ['Tourism Minister Imad Hijazin', 'Tourism Minister Emad Hijazin', 'Dr Imad Hijazin', 'Dr Emad Hijazin']},
 'tourism_board': {
  'ar': ['هيئة تنشيط السياحة الأردنية', 'هيئة تنشيط السياحة الاردنية', 'هيئة تنشيط السياحة', 'هيئة تنشيط السياحه'],
  'en': ['Jordan Tourism Board', 'Jordanian Tourism Board', 'Visit Jordan', 'VisitJordan']},
 'antiquities': {
  'ar': ['دائرة الآثار العامة الأردنية', 'دائرة الاثار العامة الاردنية', 'دائرة الآثار العامة', 'دائرة الاثار العامه'],
  'en': ['Jordan Department of Antiquities', 'Department of Antiquities of Jordan', 'Department of Antiquities in Jordan', 'Jordanian Department of Antiquities']},
 'petra': {'ar': ['البترا', 'البتراء', 'بترا', 'بتراء', 'البتره'], 'en': ['Petra', 'Petra Archaeological Park', 'Rose Red City']},
 'aqaba': {'ar': ['العقبة', 'العقبه', 'عقبة', 'منطقة العقبة الاقتصادية الخاصة'], 'en': ['Aqaba', 'Al Aqaba', 'Aqaba Special Economic Zone']},
 'wadi_rum': {'ar': ['وادي رم', 'وادي رَم', 'وادي رام'], 'en': ['Wadi Rum', 'Wadi-Rum', 'Wadi Ramm', 'Valley of the Moon']},
 'dead_sea': {'ar': ['البحر الميت', 'البحرالميت'], 'en': ['Dead Sea', 'Dead-Sea']},
 'jannah': {'ar': ['أردننا جنة', 'اردننا جنة', 'أردننا جنّة', 'اردننا جنه', 'أردنناجنة'], 'en': ['Urdunna Jannah', 'Urduna Jannah', 'Urdona Jannah', 'Urdonna Janna', 'Our Jordan is Paradise']},
 'tourism_sector': {'ar': ['القطاع السياحي في الأردن', 'القطاع السياحي الأردني', 'قطاع السياحة الأردني', 'القطاع السياحي الاردني'], 'en': ['Jordan tourism sector', 'Jordanian tourism sector', 'tourism industry in Jordan']},
 'tourism_in_jordan': {'ar': ['السياحة في الأردن', 'السياحة في الاردن', 'السياحه في الاردن'], 'en': ['Tourism in Jordan', 'Travel to Jordan', 'Visit Jordan']},
 'jordanian_tourism': {'ar': ['السياحة الأردنية', 'السياحة الاردنية', 'السياحه الاردنيه'], 'en': ['Jordanian tourism', 'Jordan tourism']},
}
SEARCH_TOPICS.update({
 'ajloun': {'ar': ['عجلون', 'قلعة عجلون', 'محافظة عجلون'], 'en': ['Ajloun', 'Ajlun', 'Ajloun Castle']},
 'jerash': {'ar': ['جرش', 'آثار جرش', 'محافظة جرش'], 'en': ['Jerash', 'Jarash', 'Gerasa']},
 'madaba': {'ar': ['مادبا', 'مأدبا', 'مادبة'], 'en': ['Madaba', 'Madabah', 'Medeba']},
 'maan': {'ar': ['معان', 'محافظة معان', 'مدينة معان'], 'en': ["Ma'an", 'Maan', 'Ma’an']},
 'irbid': {'ar': ['إربد', 'اربد', 'محافظة إربد'], 'en': ['Irbid', 'Irbid Governorate']},
 'karak': {'ar': ['الكرك', 'كرك', 'قلعة الكرك', 'محافظة الكرك'], 'en': ['Karak', 'Al Karak', 'Al-Karak', 'Kerak', 'Al Kerak', 'Karak Castle', 'Kerak Castle']},
 'visitors': {'ar': ['زوار', 'الزوار'], 'en': ['visitors', 'tourist arrivals']},
})
REGIONAL_SEARCH_TOPICS = {'ajloun', 'jerash', 'madaba', 'maan', 'irbid', 'karak', 'visitors'}
RETENTION_DAYS = 4
KEYWORD_GROUPS = {
 'وزارة السياحة والآثار الأردنية': SEARCH_TOPICS['ministry']['ar'] + SEARCH_TOPICS['ministry']['en'],
 'عماد حجازين': SEARCH_TOPICS['minister_name']['ar'] + SEARCH_TOPICS['minister_name']['en'],
 'وزير السياحة والآثار الدكتور عماد حجازين': SEARCH_TOPICS['minister_title']['ar'] + SEARCH_TOPICS['minister_title']['en'],
}
REFRESH_INTERVAL_MS = 60 * 60 * 1000
QUERIES = [
    '"وزارة السياحة والآثار الأردنية"', '"عماد حجازين"',
    '"هيئة تنشيط السياحة الأردنية"', '"دائرة الآثار العامة الأردنية"',
    '"البترا"', '"العقبة"', '"أردننا جنة"',
    '"وزارة السياحة والآثار" "الأردن"', '"هيئة تنشيط السياحة"',
    '"دائرة الآثار العامة"', '"البتراء"', '"السياحة" "الأردن"',
    '"Jordan tourism"', '"Jordan travel" -"Michael Jordan" -"Jordan Brown" -"Jordan Baker"',
    '("Petra" OR "Wadi Rum" OR "Aqaba" OR "Jerash" OR "Dead Sea") (tourism OR hotel OR heritage OR visitors)',
    '"الأردن" (طيران OR فنادق OR آثار OR مهرجان OR زوار)',
    '"Jordan" (airport OR flights OR archaeology OR heritage OR hotels)'
]
def expanded_queries():
    # Small OR batches avoid one oversized query and keep original searches.
    result = list(QUERIES)
    for topic, langs in SEARCH_TOPICS.items():
        for lang, variants in langs.items():
            for i in range(0, len(variants), 4):
                terms = ' OR '.join('"' + term + '"' for term in variants[i:i + 4])
                query = '(' + terms + ')'
                # Ambiguous English place/institution names need a Jordan anchor.
                if lang == 'en' and topic in ('ministry', 'antiquities', 'petra', 'aqaba', 'wadi_rum', 'dead_sea'):
                    query += ' (Jordan OR Jordanian)'
                if topic in REGIONAL_SEARCH_TOPICS:
                    if lang == 'ar':
                        query += ' (سياحة OR السياحة OR سياحي OR سياحية OR سياح OR آثار OR متحف OR فندق OR فنادق OR تراث OR مهرجان)'
                        if topic == 'visitors': query += ' (الأردن OR الاردن)'
                    else:
                        query += ' (Jordan OR Jordanian) (tourism OR tourists OR hotel OR heritage OR archaeology OR museum OR festival)'
                result.append(query)
    return list(dict.fromkeys(result))

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

def prune_archive(data, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=RETENTION_DAYS)
    result = dict(data)
    kept = []
    for original in data.get('items', []):
        row = dict(original)
        timestamp = publication_time(row)
        if timestamp is None:
            try:
                discovered = dt.datetime.fromisoformat(row.get('discovered', '').replace('Z', '+00:00'))
                timestamp = discovered if discovered.tzinfo else None
            except (ValueError, TypeError): pass
            if timestamp is None:
                row['discovered'] = now.isoformat()
                timestamp = now
        if timestamp >= cutoff: kept.append(row)
    result['items'] = kept
    return result

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
    text = text.translate(str.maketrans('أإآى', 'اااي'))
    return re.sub(r'\s+', ' ', text).strip()

def has_terms(text, terms):
    return any(re.search(r'(?<!\w)' + re.escape(normalized(term)) + r'(?!\w)', text) for term in terms)

def article_evidence(row):
    return ' '.join([row.get('title', '').rsplit(' - ', 1)[0], row.get('summary', ''), row.get('body', '')])

def search_matches(row, query):
    return normalized(query) in normalized(article_evidence(row) + ' ' + row.get('source', ''))

def text_status(row):
    if row.get('body'): return 'نص مستخرج من المصدر'
    return 'عنوان وملخص فقط' if row.get('body_checked') else 'بانتظار جلب النص'

def enrich_article(row):
    result = dict(row)
    result['body_checked'] = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        from googlenewsdecoder import gnewsdecoder
        from trafilatura import extract
        url = result.get('article_url') or result['url']
        if urllib.parse.urlparse(url).hostname == 'news.google.com':
            decoded = gnewsdecoder(url, timeout=10)
            if not decoded.get('success'): raise ValueError('تعذر الوصول لرابط المصدر')
            url = decoded['decoded_url']
        if urllib.parse.urlparse(url).scheme != 'https':
            raise ValueError('رابط المصدر لا يدعم HTTPS')
        if urllib.parse.urlparse(url).hostname == 'news.google.com':
            raise ValueError('لم يتم تحديد رابط الناشر')
        result['article_url'] = url
        raw = fetch(url)
        body = extract(raw, url=url, include_comments=False, include_tables=False, favor_precision=True)
        if not body or len(body.strip()) < 120: raise ValueError('المصدر لم يوفر نصا قابلا للاستخراج')
        result['body'] = body.strip()[:100000]
        result.pop('body_error', None)
    except Exception as exc:
        result['body_error'] = str(exc)[:300]
    return result

def enrich_pending(rows, limit=40):
    pending = [r for r in sorted_articles(rows.values()) if not r.get('body_checked')][:limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(enrich_article, pending): rows[result['id']] = result
    return rows

def matches_keyword(row, selected):
    if selected == 'كل الكلمات': return True
    text = normalized(article_evidence(row))
    if selected == 'وزير السياحة والآثار الدكتور عماد حجازين':
        return has_terms(text, KEYWORD_GROUPS['عماد حجازين']) and has_terms(text, ['وزير السياحة', 'وزير السياحة والآثار', 'tourism minister', 'minister of tourism'])
    return has_terms(text, KEYWORD_GROUPS.get(selected, [selected]))

JORDAN_PLACES = SEARCH_TOPICS['karak']['ar'] + SEARCH_TOPICS['karak']['en'] + ['العقبة', 'العقبه', 'البترا', 'البتراء', 'بتراء', 'وادي رم', 'وادي رام', 'جرش', 'عجلون', 'مادبا', 'ام قيس', 'ام الجمال', 'المغطس', 'معان', 'محافظة معان', 'مدينة معان', 'اربد', 'إربد', 'Irbid', "Ma'an", 'Ma’an', 'Aqaba', 'Wadi Rum', 'Wadi Ramm', 'Jerash', 'Ajloun', 'Madaba', 'Umm Qais', 'Umm al Jimal']
JORDAN_BODIES = ['وزارة السياحة والآثار الأردنية', 'وزارة السياحة الأردنية', 'هيئة تنشيط السياحة الأردنية', 'دائرة الآثار العامة الأردنية', 'Jordan Tourism Board', 'Jordanian Tourism Board', 'Jordan Ministry of Tourism', 'Jordanian Ministry of Tourism', 'Jordan Department of Antiquities', 'Department of Antiquities of Jordan']
JORDAN_PEOPLE = ['عماد حجازين', 'عماد الحجازين', 'Imad Hijazin', 'Emad Hijazin', 'Imad Hijazeen', 'Emad Hijazeen', 'Imad Hijazine', 'Emad Hijazine']
TOURISM_TERMS = ['tourism', 'tourist', 'tourists', 'travel', 'hotel', 'hotels', 'resort', 'resorts', 'destination', 'السياحة', 'السياحه', 'للسياحة', 'بالسياحة', 'والسياحة', 'السياحي', 'السياحية', 'السياحيه', 'السياح', 'سياح', 'سياحا', 'سائح', 'سائحا', 'السائحين', 'فندق', 'فنادق', 'الفنادق', 'منتجع', 'المنتجعات']
INDIRECT_TERMS = ['airport', 'flights', 'airline', 'heritage', 'archaeology', 'archaeological', 'festival', 'museum', 'conservation', 'nature reserve', 'مطار', 'المطار', 'الطيران', 'طيران', 'رحلات', 'الرحلات', 'الرحلات الجوية', 'تراث', 'التراث', 'آثار', 'الآثار', 'الأثرية', 'اثرية', 'مهرجان', 'مهرجانات', 'متحف', 'قلعة', 'مواقع اثرية', 'تلفريك', 'محمية', 'محميات']
FOREIGN_TERMS = ['Egypt', 'Egyptian', 'Cairo', 'Luxor', 'Aswan', 'Sharm el Sheikh', 'Hurghada', 'مصر', 'المصرية', 'المصري', 'القاهرة', 'الاقصر', 'اسوان', 'شرم الشيخ', 'الغردقة', 'Saudi', 'السعودية', 'Dubai', 'دبي', 'Turkey', 'تركيا', 'Lebanon', 'لبنان']

def jordan_anchor(text):
    text = normalized(text)
    return has_terms(text, ['الأردن', 'الأردني', 'الأردنية', 'الأردنيين', 'Jordan', 'Jordanian']) or has_terms(text, JORDAN_PLACES + JORDAN_BODIES + JORDAN_PEOPLE + SEARCH_TOPICS['jannah']['ar'] + SEARCH_TOPICS['jannah']['en'])

def relevance_details(row):
    title = row.get('title', '').rsplit(' - ', 1)[0]
    lead = normalized(title)
    text = normalized(article_evidence(row))
    # Publisher identity and retrieval queries never establish geographic relevance.
    if not jordan_anchor(text):
        return 'مستبعد', 'لا توجد دلالة على الأردن أو جهة أو موقع أردني في المحتوى المتاح'
    person = bool(re.search(r'\bjordan\s+(brown|baker|spieth|pickford|henderson|love|poole|peele|peterson|chiles)\b|\bmichael jordan\b|\bair jordan\b', text))
    specific = has_terms(text, JORDAN_PLACES + JORDAN_BODIES + JORDAN_PEOPLE + SEARCH_TOPICS['jannah']['ar'] + SEARCH_TOPICS['jannah']['en'])
    country_ar = has_terms(text, ['الأردن', 'الأردنية', 'الأردني', 'الأردنيين'])
    country_en = has_terms(text, ['Jordanian']) or bool(re.search(r"\b(?:in|to|from|of|visit) jordan\b|\bjordan(?:'s|’s)\b|\bjordan (?:tourism|travel|tourists|hotels|flights|heritage|minister|ministry)\b", text))
    if person and not (specific or country_ar or country_en):
        return 'مستبعد', 'Jordan مستخدمة كاسم شخص وليس دلالة على البلد'
    if not (specific or country_ar or country_en):
        return 'للمراجعة', 'ذكر Jordan يحتاج تأكيد أنه البلد وليس اسم شخص'
    # A foreign headline with only a passing Jordan mention in the body is not
    # automatically relevant. Bilateral news and Jordanian delegations are kept.
    if has_terms(lead, FOREIGN_TERMS) and not jordan_anchor(lead):
        return 'للمراجعة', 'العنوان عن وجهة خارجية وذكر الأردن موجود داخل النص فقط'
    local_official = has_terms(text, JORDAN_BODIES + JORDAN_PEOPLE + SEARCH_TOPICS['jannah']['ar'] + SEARCH_TOPICS['jannah']['en'])
    if local_official:
        return 'مباشر', 'يتناول جهة سياحية أردنية أو الوزير أو أردننا جنة'
    # Evaluate topic and geography together in the headline or nearby text,
    # rather than combining unrelated mentions from different paragraphs.
    segments = [lead] + [normalized(x) for x in re.split(r'[.!?؟\n]+', row.get('summary', '') + '\n' + row.get('body', '')) if x.strip()]
    for segment in segments:
        if not jordan_anchor(segment): continue
        if has_terms(segment, TOURISM_TERMS):
            return 'مباشر', 'سياق سياحي مرتبط بالأردن أو أحد مواقعه في نفس المقطع'
        if has_terms(segment, INDIRECT_TERMS):
            return 'غير مباشر', 'طيران أو تراث أو فعالية مرتبطة بالأردن في نفس المقطع'
    return 'للمراجعة', 'صلة بالأردن موجودة لكن ارتباطها السياحي يحتاج مراجعة'

def relevance(row):
    return relevance_details(row)[0]

def impact_details(row):
    """Conservative editorial triage, not a verified economic impact assessment."""
    title = row.get('title', '').rsplit(' - ', 1)[0]
    text = normalized(article_evidence(row))
    if relevance(row) not in ('مباشر', 'غير مباشر'):
        return 'يحتاج مراجعة', 'صلة الخبر بالسياحة الأردنية غير مؤكدة'
    # Negation, rebuttals and allegation reports cannot safely use keyword polarity.
    uncertainty = [r'نفي', r'ينفي', r'تنفي', r'غير صحيح', r'لا صحة', r'لم يتراجع', r'لم تنخفض', r'لا توجد شكاوي', r'لا توجد شكاوى', r'مزاعم', r'اشاع', r'\bdenies?\b', r'\bnot true\b', r'\brumou?rs?\b', r'\bno decline\b']
    if any(re.search(p, text) for p in uncertainty):
        return 'يحتاج مراجعة', 'يتضمن نفيا أو ادعاء أو صياغة تحتاج قراءة الخبر'
    negative = [
        (r'(تراجع|انخفاض|هبوط|تدهور|انهيار).{0,45}(السياح|السياحة|الزوار|الحجوزات|الاشغال|الايرادات)', 'تراجع في مؤشر سياحي'),
        (r'(ارتفاع|زيادة|تصاعد).{0,35}(الاسعار|اسعار|التكاليف|الشكاوي|الشكاوى|الاعتداءات)', 'ارتفاع تكاليف أو شكاوى'),
        (r'(انتقاد|ينتقد|تنتقد|شكاوي|شكاوى|يشتكي|يشكو|استياء|تذمر|سوء الخدمات)', 'انتقاد أو شكوى مرتبطة بالقطاع'),
        (r'(الغاء|تعليق|وقف).{0,35}(رحلات|الرحلات|حجوزات|الحجوزات|فعالية|مهرجان)', 'تعطل رحلات أو حجوزات أو فعاليات'),
        (r'(اغلاق|افلاس|تسريح|خسائر|احتيال|نصب|تخريب|تلوث|اعتداء|اصابة سياح|وفاة سائح|وفاة سياح|تحذير من السفر|تحذيرات سفر|تحذيرات السفر)', 'مشكلة تشغيلية أو ضرر أو مخاوف سلامة'),
        (r'\b(decline|drop|fall|slump)\b.{0,55}\b(touris[mt]|visitors|bookings|occupancy|revenue)', 'Declining tourism indicator'),
        (r'\b(touris[mt]\w*|visitors|bookings|occupancy|revenue)\b.{0,40}\b(decline|drop|fall|slump|down)\b', 'Declining tourism indicator'),
        (r'\b(critici[sz]\w*|complaints?|fraud|scam|vandalism|pollution|bankrupt\w*|layoffs?|travel warning|travel warnings|travel advisory)\b', 'Criticism, disruption or safety concern'),
        (r'\b(cancelled|canceled|suspended|halted)\b.{0,35}\b(flights|bookings|tours|festival)', 'Travel or event disruption'),
    ]
    positive = [
        (r'(ارتفاع|زيادة|نمو|تحسن|انتعاش|تعافي).{0,45}(السياح|السياحة|الزوار|الحجوزات|الاشغال|الايرادات)', 'تحسن في مؤشر سياحي'),
        (r'(انخفاض|تراجع).{0,35}(الشكاوي|الشكاوى|الحوادث|التلوث)', 'انخفاض مشكلات أو شكاوى'),
        (r'(اشادة|يشيد|تشيد|ثناء|جائزة|يفوز|تفوز|تطوير الخدمات|تحسين الخدمات|ترميم|تاهيل المواقع|افتتاح متحف|افتتاح فندق|تدشين رحلات|استئناف الرحلات|اعفاء من التاشيرة)', 'تقدير أو تطوير أو تحسن في تجربة الزائر'),
        (r'\b(growth|increase|rise|recovery|surge)\b.{0,55}\b(touris[mt]|visitors|bookings|occupancy|revenue)', 'Improving tourism indicator'),
        (r'\b(touris[mt]\w*|visitors|bookings|occupancy|revenue)\b.{0,40}\b(grow\w*|increase\w*|ris\w*|recover\w*|up)\b', 'Improving tourism indicator'),
        (r'\b(award|wins|praise|restoration|visa.free|new flights|flights resume)\b', 'Recognition or improved access or heritage'),
        (r'\b(fewer|falling|declining) complaints\b', 'Fewer complaints'),
    ]
    # Remove explicit improvement-in-problems phrases before checking harm words.
    negative_text = re.sub(r'(انخفاض|تراجع).{0,35}(الشكاوي|الشكاوى|الحوادث|التلوث)|\b(fewer|falling|declining) complaints\b', '', text)
    neg = [reason for pattern, reason in negative if re.search(pattern, negative_text)]
    pos = [reason for pattern, reason in positive if re.search(pattern, text)]
    if neg and pos: return 'يحتاج مراجعة', 'يحمل مؤشرات إيجابية وسلبية معا'
    if neg: return 'سلبي', neg[0]
    if pos: return 'إيجابي', pos[0]
    return 'محايد', 'لا توجد دلالة واضحة على أثر إيجابي أو سلبي في العنوان والملخص'

def share_message(row):
    title = str(row.get('title', '')).strip()
    source = str(row.get('source', '')).strip() or 'غير محدد'
    suffix = ' - ' + source
    if title.endswith(suffix): title = title[:-len(suffix)]
    candidates = (row.get('article_url'), row.get('url'))
    url = next((u for u in candidates if isinstance(u, str) and urllib.parse.urlparse(u).scheme == 'https'), None)
    if not title or not url: raise ValueError('الخبر لا يحتوي عنوانا ورابط HTTPS صالحين')
    return title + '\n\nالمصدر: ' + source + '\nالرابط: ' + url

def whatsapp_share_url(message):
    # Prefills a composer without selecting a recipient or sending a message.
    return 'https://wa.me/?' + urllib.parse.urlencode({'text': message})

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
    rows={r['id']:r for r in prune_archive(previous or {}).get('items',[])}; status=[]
    jobs = [(q, window) for window in ('1d', '7d') for q in expanded_queries()]
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
                if old:
                    r = {**old, **r}
                    r['discovered'] = old.get('discovered', r['discovered'])
                rows[r['id']] = r
            status.append(dict(query=q,count=len(items),error=error))
    rows = {r['id']: r for r in prune_archive({'items': list(rows.values())})['items']}
    enrich_pending(rows)
    rows = {r['id']: r for r in prune_archive({'items': list(rows.values())})['items']}
    return dict(updated=dt.datetime.now(dt.timezone.utc).isoformat(),items=sorted_articles(rows.values()),sources=status,social_coverage='Not connected: Facebook, Instagram, X')
def desktop():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    root=tk.Tk(); root.title('رصد السياحة الأردنية — 1.2'); root.geometry('1150x720')
    cache=pathlib.Path.home()/'JordanTourismMonitor'; cache.mkdir(exist_ok=True); path=cache/'feed.json'
    state=json.loads(path.read_text('utf-8')) if path.exists() else {'items':[]}
    state=prune_archive(state)
    path.write_text(json.dumps(state,ensure_ascii=False),encoding='utf-8')
    inbox = queue.Queue()
    language=tk.StringVar(value='الكل / All')
    selected_keyword=tk.StringVar(value='كل الكلمات')
    impact=tk.StringVar(value='كل الاتجاهات')
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
    ttk.Label(filters,text='الكلمة المفتاحية').pack(side='right',padx=8)
    ttk.Combobox(filters,textvariable=selected_keyword,values=('كل الكلمات', *KEYWORD_GROUPS),state='readonly',width=30).pack(side='right')
    impact_bar=ttk.Frame(root); impact_bar.pack(fill='x',padx=16,pady=4)
    ttk.Label(impact_bar,text='اتجاه الخبر').pack(side='right',padx=8)
    ttk.Combobox(impact_bar,textvariable=impact,values=('كل الاتجاهات', 'إيجابي', 'سلبي', 'محايد', 'يحتاج مراجعة'),state='readonly',width=20).pack(side='right')
    ttk.Label(impact_bar,text='تصنيف تقديري من النص المتاح • اختر خبرا لعرض السبب').pack(side='right',padx=12)
    reason_note=tk.StringVar()
    ttk.Label(root,textvariable=reason_note,wraplength=1050).pack(pady=3)
    ttk.Label(root,textvariable=count).pack(pady=4)
    table=ttk.Treeview(root,columns=('title','source','published','relevance','impact','text'),show='headings')
    for c,label,width in [('title','العنوان',650),('source','المصدر',180),('published','وقت النشر — الأردن',170),('relevance','الصلة',90),('impact','الاتجاه التقديري',110),('text','نطاق القراءة',150)]: table.heading(c,text=label); table.column(c,width=width)
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
            if not matches_keyword(row, selected_keyword.get()): continue
            direction, reason = impact_details(row)
            if impact.get() != 'كل الاتجاهات' and direction != impact.get(): continue
            if search_matches(row, keyword.get()):
                shown.append(row); table.insert('', 'end',iid=str(len(shown)-1),values=(row['title'],row['source'],publication_time(row).astimezone(JORDAN_TIME).strftime('%Y-%m-%d %H:%M') if publication_time(row) else 'غير معروف',label,direction,text_status(row)))
        count.set(f'المعروض: {len(shown)} من {len(state["items"])} | بتوقيت الأردن | حسب وقت النشر؛ التواريخ غير المعروفة تظهر في الكل فقط')
    def show_reason(_):
        if table.selection():
            direction, reason = impact_details(shown[int(table.selection()[0])])
            reason_note.set('الصلة بالأردن: ' + relevance_details(shown[int(table.selection()[0])])[1] + ' | الاتجاه: ' + direction + ' — ' + reason + ' | ' + text_status(shown[int(table.selection()[0])]))
        else: reason_note.set('')
    table.bind('<<TreeviewSelect>>',show_reason)
    def open_item(_):
        if table.selection(): webbrowser.open(shown[int(table.selection()[0])]['url'])
    table.bind('<Double-1>',open_item); keyword.trace_add('write',render); period.trace_add('write',render); scope.trace_add('write',render); language.trace_add('write',render); selected_keyword.trace_add('write',render); impact.trace_add('write',render)
    def done(result):
        nonlocal state
        state=prune_archive(result); path.write_text(json.dumps(state,ensure_ascii=False),encoding='utf-8'); render()
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
    def read_selected():
        if not table.selection():
            note.set('اختر خبرا ثم اضغط قراءة النص'); return
        row = dict(shown[int(table.selection()[0])])
        def work(): inbox.put(('article', enrich_article(row)))
        threading.Thread(target=work, daemon=True).start()
        note.set('جارٍ جلب نص الخبر من المصدر...')
    def accept_article(row):
        for index, current in enumerate(state['items']):
            if current['id'] == row['id']:
                state['items'][index] = row; break
        state['items'] = prune_archive(state)['items']
        path.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
        render()
        note.set(text_status(row) + (' — ' + row.get('body_error', '') if not row.get('body') else ' — تم تحديث الفلاتر والتصنيف'))
        if row.get('body'):
            window=tk.Toplevel(root); window.title(row.get('title','نص الخبر')); window.geometry('850x600')
            text=tk.Text(window, wrap='word', font=('Arial',13)); text.pack(fill='both',expand=True)
            text.insert('1.0', row['body']); text.config(state='disabled')
    def selected_share_message():
        if not table.selection():
            note.set('اختر خبرا من القائمة أولا'); return None
        try: return share_message(shown[int(table.selection()[0])])
        except (ValueError, IndexError) as exc:
            note.set(str(exc)); return None
    def copy_message():
        message = selected_share_message()
        if message is None: return
        try:
            root.clipboard_clear(); root.clipboard_append(message)
            note.set('تم نسخ العنوان والمصدر والرابط؛ الصقها في الشخص أو المجموعة المطلوبة')
        except tk.TclError:
            note.set('تعذر النسخ للحافظة؛ حاول مرة أخرى')
    def share_whatsapp():
        message = selected_share_message()
        if message is None: return
        try:
            opened = webbrowser.open(whatsapp_share_url(message))
            if opened: note.set('اختر الشخص أو المجموعة وراجع الرسالة واضغط إرسال داخل واتساب؛ لم يرسل البرنامج أي رسالة')
            else: note.set('تعذر فتح واتساب؛ استخدم زر نسخ الرسالة والصقها يدويا')
        except Exception:
            note.set('تعذر فتح واتساب؛ استخدم زر نسخ الرسالة والصقها يدويا')
    share_bar=ttk.Frame(root); share_bar.pack(fill='x',padx=16,pady=5)
    ttk.Button(share_bar,text='مشاركة على واتساب',command=share_whatsapp).pack(side='right')
    ttk.Button(share_bar,text='نسخ الرسالة',command=copy_message).pack(side='right',padx=8)
    ttk.Label(share_bar,text='للخبر المحدد • تختار المستلم وتضغط إرسال بنفسك داخل واتساب').pack(side='right',padx=8)
    def export():
        target=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if target:
            with open(target,'w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f); w.writerow(['العنوان','المصدر','وقت النشر','الرابط','الاتجاه التقديري','سبب التصنيف','نطاق القراءة','رابط المصدر'])
                for r in shown: w.writerow([r['title'],r['source'],r['published'],r['url'],*impact_details(r),text_status(r),r.get('article_url',r['url'])])
    ttk.Button(bar,text='قراءة نص الخبر',command=read_selected).pack(side='left')
    refresh=ttk.Button(bar,text='تحديث',command=update); refresh.pack(side='left'); ttk.Button(bar,text='تصدير CSV',command=export).pack(side='left')
    ttk.Label(root,text='بحث كل ساعة • حذف تلقائي بعد 4 أيام من النشر (ومن الاكتشاف عند غياب التاريخ) • جلب حتى 40 نصا بكل دورة').pack(pady=4)
    ttk.Label(root,text='رابط HTTPS لنتائج الخدمة السحابية (اختياري؛ تركه فارغًا يجمع الأخبار على الجهاز)').pack()
    ttk.Entry(root,textvariable=endpoint,width=100).pack(pady=5); ttk.Label(root,textvariable=note,wraplength=1050).pack(pady=8)
    def poll():
        try:
            kind, payload = inbox.get_nowait()
            if kind == 'ok': done(payload)
            elif kind == 'article': accept_article(payload)
            else:
                note.set('تعذّر التحديث؛ النتائج المعروضة محفوظة: ' + payload)
                refresh.config(state='normal')
        except queue.Empty: pass
        root.after(100, poll)
    def auto_refresh():
        update()
        root.after(REFRESH_INTERVAL_MS, auto_refresh)
    def tick():
        retained = prune_archive(state)
        if retained['items'] != state['items']:
            state['items'] = retained['items']
            path.write_text(json.dumps(state,ensure_ascii=False),encoding='utf-8')
        render()
        root.after(60000, tick)
    tick(); poll(); root.after(300, auto_refresh); root.mainloop()
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--self-check',action='store_true'); p.add_argument('--collect',action='store_true'); p.add_argument('--output',default='feed.json'); a=p.parse_args()
    if a.self_check:
        from googlenewsdecoder import gnewsdecoder
        from trafilatura import extract
        sample = '<html><body><article><p>' + ('Jordan tourism and heritage news. ' * 30) + '</p></article></body></html>'
        assert extract(sample, include_comments=False, favor_precision=True)
        assert callable(gnewsdecoder)
    elif a.collect:
        dest=pathlib.Path(a.output); previous=json.loads(dest.read_text('utf-8')) if dest.exists() else None
        result=collect(previous); dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        if all(s['error'] for s in result['sources']): raise SystemExit('All sources failed; see feed.json')
    else: desktop()
