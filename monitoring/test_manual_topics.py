"""Regression checks for additions from the media team's manual examples."""
import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import monitor as m
class RelevanceTests(unittest.TestCase):
 def test_context(self):
  cases=[('السياحة الرياضية بوابة جديدة لتعزيز حضور الأردن عالمياً','مباشر'),('الأكاديمية الأردنية للسياحة والفندقة تؤهل كوادر جديدة','مباشر'),('صون مكتشفات البادية الجنوبية الشرقية في الأردن','غير مباشر'),('معبد هرقل في جبل القلعة بالعاصمة عمان','غير مباشر'),('الأمير علي يستضيف رونالدينيو في عمان','للمراجعة'),('رونالدينيو يزور الأردن للترويج للسياحة الرياضية','مباشر'),('رونالدينيو يسجل هدفا في البرازيل','مستبعد'),('السياحة الرياضية في مصر','مستبعد'),('افتتاح مستشفى في الأردن','للمراجعة')]
  for title,expected in cases:
   with self.subTest(title=title):self.assertEqual(m.relevance({'title':title}),expected)
 def test_filters_unchanged(self):self.assertEqual(len(m.KEYWORD_GROUPS),3)
 def test_context_queries(self):
  for q in m.expanded_queries():
   if any(k in q for k in ['Ronaldinho','رونالدينيو','MICE']):self.assertTrue('Jordan' in q or 'الأردن' in q)
if __name__=='__main__':unittest.main()
