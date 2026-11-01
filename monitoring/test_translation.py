import json,unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import translation as t
class TranslationTests(unittest.TestCase):
 def test_request(self):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,*args):return json.dumps({'message':{'content':'Hijazin said Jordan welcomes visitors.'},'done_reason':'stop'}).encode()
  def fake(req,timeout):
   self.assertEqual(req.full_url,'http://127.0.0.1:11434/api/chat')
   data=json.loads(req.data);self.assertFalse(data['stream']);self.assertFalse(data['think']);self.assertIn('السياحة',data['messages'][1]['content']);self.assertIn('Do not silently summarize',data['messages'][0]['content']);return Response()
  self.assertIn('Hijazin',t.translate('السياحة',opener=fake))
 def test_empty(self):
  with self.assertRaises(ValueError):t.messages(' ')
 def test_length(self):
  with self.assertRaises(ValueError):t.messages('ا'*45001)
 def test_no_remote_fallback(self):
  def fail(*args,**kwargs):raise OSError('offline')
  with self.assertRaisesRegex(ValueError,'Ollama'):t.translate('الأردن',opener=fail)
if __name__=='__main__':unittest.main()
