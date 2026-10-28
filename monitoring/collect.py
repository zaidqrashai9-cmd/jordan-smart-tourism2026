"""Hourly shared public-news feed. No private imports or account credentials are published."""
import sys,pathlib,json,datetime as dt,concurrent.futures,urllib.parse,urllib.request,os,re
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));import monitor as m
OUT=ROOT/'data';OUT.mkdir(exist_ok=True)
m.JORDAN_PLACES += ['عمان','عمّان','الزرقاء','السلط','الفحيص','الطفيلة','المفرق','وادي موسى','Amman','Zarqa','Tafilah','Mafraq','Fuheis','Wadi Musa']
LOC=json.loads((ROOT/'monitoring/localities.json').read_text())
PRIORITY=['السياحة الأردن','عماد حجازين','هيئة تنشيط السياحة','أردننا جنة','Jordan tourism','Jordan travel','Jordan travel advisory','الأردن تحذيرات السفر','الكرك سياحة','البترا سياح','العقبة سياحة','وادي رم سياحة']
ALL=m.expanded_queries()
for gov in sorted(set(x['governorate'] for x in LOC['items'])):
 rows=[x for x in LOC['items'] if x['governorate']==gov and x['type']=='locality']
 for lang in ['ar','en']:
  terms=list(dict.fromkeys(x[lang] for x in rows if x[lang]))
  for i in range(0,len(terms),4):
   names=' OR '.join('"'+x.replace('"','')+'"' for x in terms[i:i+4])
   ALL.append('('+names+') '+('(الأردن OR الاردن) (سياحة OR سياح OR فندق OR آثار OR تراث OR متحف OR مهرجان OR رحلات)' if lang=='ar' else '(Jordan OR Jordanian) (tourism OR tourists OR travel OR hotel OR heritage OR archaeology OR museum OR festival)'))
ALL=list(dict.fromkeys(ALL));(ROOT/'ios/Resources/queries.json').write_text(json.dumps({'priority':PRIORITY,'queries':ALL},ensure_ascii=False,separators=(',',':')))
PLACE_AR=[x['ar'] for x in LOC['items'] if len(x['ar'])>=3]
PLACE_EN=[x['en'] for x in LOC['items'] if len(x['en'])>=4]
place_pat=re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(m.normalized(x)) for x in sorted(set(PLACE_AR+PLACE_EN),key=len,reverse=True))+r')(?!\w)')
def classify(r):
 rel,reason=m.relevance_details(r);text=m.normalized(m.article_evidence(r));matches=list(dict.fromkeys(x.group() for x in place_pat.finditer(text)))[:12]
 if rel not in ['مباشر','غير مباشر'] and matches:
  country=m.has_terms(text,['الأردن','الأردني','الأردنية','Jordanian']) or bool(re.search(r'\b(?:in|to|from|of|visit) jordan\b|\bjordan tourism\b|\bjordan(?:’s|\'s)\b',text))
  if country and m.has_terms(text,m.TOURISM_TERMS):rel,reason='مباشر','سياحة وموقع أردني في المحتوى المتاح'
  elif country and m.has_terms(text,m.INDIRECT_TERMS):rel,reason='غير مباشر','موضوع مرتبط بالسياحة وموقع أردني في المحتوى المتاح'
  else:rel,reason='للمراجعة','ذكر موقع في الدليل؛ يلزم تأكيد الصلة بالأردن والسياحة'
 sentiment,why=m.impact_details(r)
 return rel,reason,[sentiment,why],matches

def social_connectors():
 statuses=[];items=[]
 specs=[('Facebook',os.getenv('FACEBOOK_PAGE_ID'),os.getenv('META_ACCESS_TOKEN')),('Instagram',os.getenv('INSTAGRAM_ACCOUNT_ID'),os.getenv('META_ACCESS_TOKEN')),('X',None,os.getenv('X_BEARER_TOKEN'))]
 for platform,account,token in specs:
  state={'platform':platform,'connected':False,'count':0,'checked':dt.datetime.now(dt.timezone.utc).isoformat()}
  if not token or (platform!='X' and (not account or not os.getenv('META_GRAPH_VERSION'))):
   state['message']='غير متصل: لم تُضبط صلاحيات API وحساب المصدر. يمكن إضافة رابط عام يدويًا على الهاتف.';statuses.append(state);continue
  try:
   if platform=='Facebook':url=f'https://graph.facebook.com/{os.environ["META_GRAPH_VERSION"]}/{account}/posts?'+urllib.parse.urlencode({'fields':'id,message,story,permalink_url,created_time','limit':50});headers={'Authorization':'Bearer '+token}
   elif platform=='Instagram':url=f'https://graph.facebook.com/{os.environ["META_GRAPH_VERSION"]}/{account}/media?'+urllib.parse.urlencode({'fields':'id,caption,permalink,timestamp','limit':50});headers={'Authorization':'Bearer '+token}
   else:url='https://api.x.com/2/tweets/search/recent?'+urllib.parse.urlencode({'query':'(Jordan OR الأردن) (tourism OR travel OR سياحة OR سياح) -is:retweet','tweet.fields':'created_at,author_id,lang','max_results':100});headers={'Authorization':'Bearer '+token}
   data=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=25).read())
   for p in data.get('data',[]):
    text=p.get('message') or p.get('story') or p.get('caption') or p.get('text') or '';url=p.get('permalink_url') or p.get('permalink') or 'https://x.com/i/status/'+p['id']
    r={'id':platform+'-'+p['id'],'title':text[:180] or 'منشور بلا نص متاح','summary':text[:600],'source':platform,'url':url,'published':p.get('created_time') or p.get('timestamp') or p.get('created_at') or '', 'discovered':state['checked'],'platform':platform,'account':p.get('author_id') or account or '', 'manual':False}
    # Normalize API timestamps for the desktop-compatible schema.
    try:r['published']=dt.datetime.fromisoformat(r['published'].replace('Z','+00:00')).strftime('%a, %d %b %Y %H:%M:%S GMT')
    except ValueError:pass
    items.append(decorate(r))
   state.update(connected=True,count=len(data.get('data',[])),message='اتصال API مصرح به؛ تغطية الحسابات/الاستعلام المحدد فقط')
  except Exception as e:state['message']='تعذر اتصال API: '+str(e)[:200]
  statuses.append(state)
 return m.prune_archive({'items':items})['items'],statuses

def decorate(r):
 rel,why,impact,places=classify(r);row=dict(r);row.update(_relevance=rel,_relevance_reason=why,_impact=impact,_language=m.article_language(r),_places=places,_matched_keywords=[k for k in m.KEYWORD_GROUPS if m.matches_keyword(r,k)])
 if r.get('_analysis_title')==r['title'] and r.get('body_checked'):
  row['_matched_keywords']=list(dict.fromkeys(row['_matched_keywords']+r.get('_matched_keywords',[])))
  if r.get('_relevance') in ['مباشر','غير مباشر'] and row['_relevance'] not in ['مباشر','غير مباشر']:
   row['_relevance']=r['_relevance'];row['_relevance_reason']=r.get('_relevance_reason',row['_relevance_reason']);row['_impact']=r.get('_impact',row['_impact'])
 row['_analysis_title']=r['title']
 body=r.get('body','');row['text_scope']='body analyzed; excerpt displayed' if body else 'headline and summary only';row['body']=body[:450];row['summary']=r.get('summary','')[:450]
 row.pop('query',None);return row

def main(seed=False):
 p=OUT/'news.json'
 old=json.loads(p.read_text()) if p.exists() else {'items':[],'cursor':0}
 old=m.prune_archive(old);cursor=int(old.get('cursor',0));batch=16 if seed else 24
 jobs=list(dict.fromkeys(PRIORITY+[ALL[(cursor+i)%len(ALL)] for i in range(batch)]))
 rows={r['id']:r for r in old['items']};status=[]
 def one(q):
  en=q.isascii();url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q+' when:4d','hl':'en' if en else 'ar','gl':'US' if en else 'JO','ceid':'US:en' if en else 'JO:ar'})
  try:return q,m.parse_feed(m.fetch(url),q),None
  except Exception as e:return q,[],str(e)[:180]
 for q,found,error in concurrent.futures.ThreadPoolExecutor(max_workers=3).map(one,jobs):
  status.append({'query':q,'count':len(found),'error':error,'provider':'Google News'})
  for r in found:
   previous=rows.get(r['id'],{});r={**previous,**r};r['discovered']=previous.get('discovered',r['discovered']);rows[r['id']]=r
 rows={r['id']:r for r in m.prune_archive({'items':list(rows.values())})['items']}
 if not seed:
  pending=[r for r in m.sorted_articles(rows.values()) if not r.get('body_checked')][:12]
  for r in concurrent.futures.ThreadPoolExecutor(max_workers=3).map(m.enrich_article,pending):rows[r['id']]=r
 now=dt.datetime.now(dt.timezone.utc).isoformat();successful=sum(not x['error'] for x in status);new=len(set(rows)-set(r['id'] for r in old['items']))
 items=[decorate(r) for r in m.sorted_articles(rows.values())][:6000]
 social,socialstatus=social_connectors()
 data={'items':items,'sources':status,'updated':now,'last_success':now if successful else old.get('last_success'),'new_items':new,'cursor':(cursor+batch)%len(ALL),'total_queries':len(ALL),'checked_queries':len(jobs),'last_check_successful':successful>0,'schedule':'GitHub Actions, hourly target at minute 17; runs may be delayed or disabled by provider inactivity rules.','localities':{'count':LOC['locality_count'],'governorates':12,'source':LOC['source'],'year':2025},'social_items':social,'social_sources':socialstatus}
 p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
 # The native offline bundle contains real collected news, never production fixtures.
 if seed:(ROOT/'ios/Resources/news.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
 print(json.dumps({'items':len(items),'new':new,'failed':len(status)-successful,'queries':len(ALL),'localities':LOC['locality_count']},ensure_ascii=False))
if __name__=='__main__':main('--seed' in sys.argv)
