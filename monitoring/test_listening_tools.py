import datetime as dt
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import listening_tools as tools

class ListeningTests(unittest.TestCase):
 def test_duplicates_preserve_all_sources_and_numbers(self):
  a={'id':'1','title':'نشاط سياحي لافت في عجلون واستقبال 10 حافلات ضمن برنامج أردننا جنة - بترا','source':'بترا'}
  b={**a,'id':'2','title':a['title'].replace(' - بترا',' - عمون'),'source':'عمون'}
  c={**b,'id':'3','title':b['title'].replace('10','20')}
  groups=tools.group_stories([a,b,c])
  self.assertEqual([len(g) for g in groups],[2,1]);self.assertEqual(sum(map(len,groups)),3)
  self.assertFalse(tools.same_story({'title':''},{'title':''}))
  self.assertFalse(tools.same_story({'title':'Tourism in Jordan grows'},{'title':'Tourism in Egypt grows'}))
 def test_preferences_roundtrip_and_no_secrets(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'prefs.json'
   tools.save_preferences(p,{'favorites':['a'],'searches':{'العقبة':{'query':'العقبة','period':'اليوم'}},'api_key':'secret'})
   self.assertNotIn('secret',p.read_text());self.assertEqual(tools.load_preferences(p)['searches']['العقبة']['period'],'اليوم')
   p.write_text('broken');self.assertEqual(tools.load_preferences(p),{'favorites':[],'searches':{}})
 def test_summary_counts_only_input_and_handles_dates(self):
  now=dt.datetime(2026,11,22,12,tzinfo=dt.timezone.utc)
  rows=[{'title':'السياحة في العقبة','source':'بترا','stamp':now-dt.timedelta(hours=1)},
        {'title':'Tourism in Jordan','source':'BBC','stamp':None}]
  s=tools.summary(rows,lambda r:r['stamp'],lambda r:('محايد',''),{'العقبة':['العقبة']},now)
  self.assertEqual(s['total'],2);self.assertEqual(s['unknown'],1);self.assertEqual(s['current'],1)
  self.assertEqual(s['topics']['العقبة'],1);self.assertEqual(sum(s['sources'].values()),2)
  self.assertFalse(s['spike']);self.assertEqual(tools.summary([],lambda r:None,lambda r:('',''),{})['total'],0)
 def test_excel_formula_escape(self):
  self.assertEqual(tools.csv_cell(' =HYPERLINK("bad")'),'\' =HYPERLINK("bad")')
  self.assertEqual(tools.csv_cell('السياحة الأردنية'),'السياحة الأردنية')
if __name__=='__main__':unittest.main()
