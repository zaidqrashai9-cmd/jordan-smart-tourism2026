"""Local listening workflow helpers. No network or external services."""
import collections
import datetime as dt
import difflib
import json
import re
import unicodedata
import urllib.parse


def normalize(value):
    value = unicodedata.normalize('NFKC', str(value)).casefold()
    value = re.sub(r'[\u064b-\u065f\u0670ـ]', '', value)
    value = value.translate(str.maketrans('أإآى', 'اااي'))
    return ' '.join(re.findall(r'\w+', value))


def headline(row):
    text = row.get('title', '')
    suffix = ' - ' + row.get('source', '')
    return normalize(text[:-len(suffix)] if row.get('source') and text.endswith(suffix) else text)


def source_name(row):
    return row.get('source', '').strip() or 'غير محدد'


def same_story(a, b):
    # A deliberately conservative suggestion; never deletes or merges records.
    left, right = headline(a), headline(b)
    if not left or not right:
        return False
    if left == right:
        return True
    ta, tb = set(left.split()), set(right.split())
    if len(ta) < 6 or len(tb) < 6:
        return False
    # Distinct numbers/dates often distinguish follow-up stories.
    if re.findall(r'\d+', left) != re.findall(r'\d+', right):
        return False
    return len(ta & tb) / len(ta | tb) >= .8 and difflib.SequenceMatcher(None, left, right, autojunk=False).ratio() >= .88


def group_stories(rows):
    groups = []
    for row in rows:
        for group in groups:
            if same_story(row, group[0]):
                group.append(row)
                break
        else:
            groups.append([row])
    return groups


def load_preferences(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return {'favorites': [str(x) for x in data.get('favorites', [])],
                'searches': {str(k): v for k, v in data.get('searches', {}).items() if isinstance(v, dict)}}
    except (OSError, ValueError, TypeError, AttributeError):
        return {'favorites': [], 'searches': {}}


def save_preferences(path, data):
    # Explicit allowlist: credentials and article text never enter this file.
    clean = {'favorites': list(data.get('favorites', [])), 'searches': data.get('searches', {})}
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def csv_cell(value):
    # Prevent headlines or publisher strings being interpreted as Excel formulas.
    value = str(value or '')
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value


def summary(rows, publication_time, impact_details, topic_terms, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    days = collections.Counter()
    sources = collections.Counter()
    sentiments = collections.Counter()
    topics = collections.Counter()
    unknown = current = previous = 0
    for row in rows:
        sources[source_name(row)] += 1
        sentiments[impact_details(row)[0]] += 1
        stamp = publication_time(row)
        if stamp is None:
            unknown += 1
        elif stamp <= now:
            days[stamp.astimezone(dt.timezone(dt.timedelta(hours=3))).strftime('%Y-%m-%d')] += 1
            age = now - stamp
            if age <= dt.timedelta(hours=24): current += 1
            elif age <= dt.timedelta(hours=48): previous += 1
        evidence = normalize(' '.join(row.get(k, '') for k in ('title', 'summary', 'body')))
        for label, terms in topic_terms.items():
            if any(re.search(r'(?<!\w)' + re.escape(normalize(term)) + r'(?!\w)', evidence) for term in terms):
                topics[label] += 1
    return dict(total=len(rows), stories=len(group_stories(rows)), sources=sources,
                sentiments=sentiments, topics=topics, days=days, unknown=unknown,
                current=current, previous=previous,
                spike=previous >= 3 and current >= 10 and current >= previous * 2)
