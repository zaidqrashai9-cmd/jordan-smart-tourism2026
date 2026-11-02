import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import petra_names as p
class Tests(unittest.TestCase):
 def test_domain(self):
  self.assertTrue(p.petra_url('https://petra.gov.jo/en/news/test'))
  for u in ['https://petra.gov.jo.evil/en/a','http://petra.gov.jo/en/a','https://petra.gov.jo/ar/a','https://evil/en/a']:self.assertFalse(p.petra_url(u))
 def test_evidence(self):
  doc={'text':'Tourism Minister Imad Hijazin said this.','url':'https://petra.gov.jo/en/news/a','date':'2026-11-02'}
  person={'ar':'عماد حجازين'}
  self.assertIsNotNone(p.validate_candidate({'en':'Imad Hijazin','role':'Tourism Minister','quote':doc['text']},doc,person))
  self.assertIsNone(p.validate_candidate({'en':'Imad Hijazin','role':'Prime Minister','quote':doc['text']},doc,person))
 def test_latest_not_input_order(self):
  self.assertEqual(p.newest([{'date':'2025-01-01','role':'Old'},{'date':'2026-11-01','role':'New'}])['role'],'New')
 def test_same_date_conflict(self):
  self.assertTrue(p.newest([{'date':'2026-11-01','role':'A'},{'date':'2026-11-01','role':'B'}])['conflict'])
 def test_no_evidence(self):self.assertIsNone(p.newest([]))
if __name__=='__main__':unittest.main()
