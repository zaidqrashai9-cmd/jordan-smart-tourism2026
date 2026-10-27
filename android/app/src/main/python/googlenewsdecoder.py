"""Android-compatible Google News link resolver, without native selectolax.
Protocol reference: googlenewsdecoder (SSujitX), MIT licensed project.
All network requests have explicit timeouts and certificate verification.
"""
import json,urllib.parse,urllib.request
from html.parser import HTMLParser
class Attributes(HTMLParser):
 def __init__(self):super().__init__();self.params=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('data-n-a-sg') and a.get('data-n-a-ts'):self.params=(a['data-n-a-sg'],a['data-n-a-ts'])
def gnewsdecoder(url,timeout=10):
 try:
  parsed=urllib.parse.urlparse(url)
  if parsed.hostname!='news.google.com':return {'success':True,'decoded_url':url}
  token=parsed.path.rstrip('/').split('/')[-1]
  if not token or len(token)>10000:raise ValueError('Invalid news URL')
  headers={'User-Agent':'Mozilla/5.0'}
  params=None
  for prefix in ['articles/','rss/articles/']:
   try:
    request=urllib.request.Request('https://news.google.com/'+prefix+urllib.parse.quote(token,safe=''),headers=headers)
    with urllib.request.urlopen(request,timeout=timeout) as r:html=r.read(2000000).decode('utf-8','replace')
    p=Attributes();p.feed(html);params=p.params
    if params:break
   except (OSError,ValueError):continue
  if not params:raise ValueError('تعذر تحديد رابط المصدر')
  signature,timestamp=params
  arguments=['garturlreq',[['X','X',['X','X'],None,None,1,1,'US:en',None,1,None,None,None,None,None,0,1],'X','X',1,[1,1,1],1,1,None,0,0,None,0],token,int(timestamp),signature]
  payload=[[['Fbv4je',json.dumps(arguments),None,'generic']]]
  body=urllib.parse.urlencode({'f.req':json.dumps(payload)}).encode()
  req=urllib.request.Request('https://news.google.com/_/DotsSplashUi/data/batchexecute',data=body,headers={**headers,'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'})
  with urllib.request.urlopen(req,timeout=timeout) as r:raw=r.read(2000000).decode()
  for line in raw.splitlines():
   if not line.startswith('['):continue
   try:
    for part in json.loads(line):
     if isinstance(part,list) and len(part)>2 and part[1]=='Fbv4je':
      result=json.loads(part[2]);target=result[1]
      if urllib.parse.urlparse(target).scheme=='https':return {'success':True,'decoded_url':target}
   except (ValueError,TypeError,IndexError):continue
  raise ValueError('تعذر فك رابط المصدر')
 except Exception as e:return {'success':False,'message':str(e)}
