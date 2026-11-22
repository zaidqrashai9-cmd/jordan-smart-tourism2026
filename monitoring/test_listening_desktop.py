"""Real Tk workflow checks on Windows; network is disabled in the fixture."""
import sys,pathlib,tempfile,json,datetime as dt,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import monitor,tkinter as tk
from tkinter import ttk

def descendants(parent):
 for child in parent.winfo_children():
  yield child
  yield from descendants(child)

class WorkflowTests(unittest.TestCase):
 def test_listening_workflow(self):
  with tempfile.TemporaryDirectory() as d:
   folder=pathlib.Path(d)/'JordanTourismMonitor';folder.mkdir()
   published=dt.datetime.now(dt.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
   title='السياحة في الأردن تشهد نشاطا في العقبة واستقبال 10 حافلات'
   items=[{'id':str(i),'title':t+' - '+source,'source':source,'published':published,'url':'https://example.org/'+str(i)} for i,(t,source) in enumerate([(title,'بترا'),(title,'عمون'),(title.replace('10','20'),'بترا'),('السياحة في مصر','الخارج')])]
   (folder/'feed.json').write_text(json.dumps({'items':items}),encoding='utf-8')
   def inspect(root):
    try:
     root.geometry('1000x760');root.update_idletasks()
     def button(text):return next(w for w in descendants(root) if isinstance(w,ttk.Button) and w.cget('text')==text)
     table=next(w for w in descendants(root) if isinstance(w,ttk.Treeview))
     self.assertEqual(len(table.get_children()),3) # Foreign tourism remains excluded.
     self.assertFalse(any(isinstance(w,ttk.Button) and w.cget('text')=='ترجمة إلى الإنجليزية' for w in descendants(root)))
     group=next(w for w in descendants(root) if isinstance(w,ttk.Checkbutton) and w.cget('text')=='تجميع المتشابه')
     group.invoke();self.assertEqual(len(table.get_children()),2)
     table.selection_set(table.get_children()[0]);button('مصادر الخبر').invoke();root.update_idletasks()
     copies=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
     copy_table=next(w for w in descendants(copies) if isinstance(w,ttk.Treeview))
     self.assertEqual(len(copy_table.get_children()),2);copies.destroy()
     button('★ المفضلة').invoke()
     self.assertEqual(json.loads((folder/'listening-preferences.json').read_text(encoding='utf-8'))['favorites'],['0'])
     with patch('tkinter.simpledialog.askstring',return_value='بحث تجريبي'):button('حفظ البحث').invoke()
     data=json.loads((folder/'listening-preferences.json').read_text(encoding='utf-8'));self.assertTrue(data['searches']['بحث تجريبي']['grouped'])
     source_box=next(w for w in descendants(root) if isinstance(w,ttk.Combobox) and 'كل المصادر' in w.cget('values'))
     source_box.set('عمون');self.assertEqual(len(table.get_children()),1)
     source_box.set('كل المصادر');self.assertEqual(len(table.get_children()),2)
     button('لوحة التحليل').invoke();root.update_idletasks()
     dashboard=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
     notebook=next(w for w in descendants(dashboard) if isinstance(w,ttk.Notebook))
     self.assertEqual(len(notebook.tabs()),4);dashboard.destroy()
     target=folder/'export.csv'
     with patch('tkinter.filedialog.asksaveasfilename',return_value=str(target)):button('تصدير CSV').invoke()
     self.assertEqual(len(target.read_text(encoding='utf-8-sig').splitlines()),4) # All 3 materials despite grouping.
     for text in ('لوحة التحليل','★ المفضلة','مصادر الخبر','حفظ البحث'):
      w=button(text);self.assertTrue(w.winfo_ismapped());self.assertLessEqual(w.winfo_rootx()+w.winfo_width(),root.winfo_rootx()+root.winfo_width())
    finally:root.destroy()
   with patch.object(pathlib.Path,'home',return_value=pathlib.Path(d)),patch.object(tk.Tk,'mainloop',inspect),patch.object(monitor.threading.Thread,'start'),patch.object(monitor.credential_store,'load_key',side_effect=AssertionError('Hidden translation must not load key')):
    monitor.desktop()
if __name__=='__main__':unittest.main()
