import json,pathlib,threading,datetime as dt
import monitor
_lock=threading.RLock()
def decorate(row):
 r=dict(row);r['_relevance']=monitor.relevance(r);r['_impact']=monitor.impact_details(r);return r
def execute(directory,action,body=''):
 with _lock:
  path=pathlib.Path(directory)/'feed.json'
  try:data=json.loads(path.read_text()) if path.exists() else {'items':[],'sources':[]}
  except (ValueError,OSError):data={'items':[],'sources':[]}
  data=monitor.prune_archive(data)
  if action=='/api/refresh':data=monitor.collect(data)
  elif action=='/api/import':
   incoming=json.loads(body)
   if not isinstance(incoming.get('items'),list):raise ValueError('ملف غير صالح')
   rows={r['url']:r for r in data['items']}
   for row in incoming['items']:
    if not isinstance(row,dict) or not isinstance(row.get('title'),str) or not isinstance(row.get('url'),str) or not row['url'].startswith('https://'):continue
    row=dict(row);row.setdefault('id',monitor.hashlib.sha256(row['url'].encode()).hexdigest());row.setdefault('summary','');row.setdefault('source','');rows[row['url']]=row
   data['items']=list(rows.values());data=monitor.prune_archive(data)
  elif action=='/api/article':
   row=json.loads(body)
   row=monitor.enrich_article(row)
   data['items']=[row if r['url']==row['url'] else r for r in data['items']]
  elif action!='/api/news':raise ValueError('Unknown action')
  # Atomic writes preserve the saved archive across an interrupted refresh.
  tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False));tmp.replace(path)
  if action=='/api/article':return json.dumps(decorate(row),ensure_ascii=False)
  data['items']=[decorate(r) for r in data['items']];data['serverNow']=dt.datetime.now(dt.timezone.utc).isoformat()
  return json.dumps(data,ensure_ascii=False)
