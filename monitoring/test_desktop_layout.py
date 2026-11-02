"""Windows Tk regression: translation controls must fit small windows."""
import sys,pathlib,tempfile,json,datetime as dt,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import monitor,tkinter as tk
from tkinter import ttk
def descendants(parent):
 for child in parent.winfo_children():
  yield child
  yield from descendants(child)
class LayoutTests(unittest.TestCase):
 def test_translation_controls_visible(self):
  with tempfile.TemporaryDirectory() as d:
   folder=pathlib.Path(d)/'JordanTourismMonitor';folder.mkdir()
   (folder/'feed.json').write_text(json.dumps({'items':[{'id':'layout-test','title':'السياحة في الأردن','source':'test','url':'https://example.org','published':dt.datetime.now(dt.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}] }),encoding='utf-8')
   def inspect(root):
    try:
     root.geometry('900x650');root.tk.call('tk','scaling',1.5);root.update_idletasks()
     buttons=[w for w in descendants(root) if isinstance(w,ttk.Button) and w.cget('text')=='ترجمة إلى الإنجليزية']
     self.assertEqual(len(buttons),1)
     button=buttons[0]
     self.assertTrue(button.winfo_ismapped())
     self.assertLessEqual(button.winfo_rootx()+button.winfo_width(),root.winfo_rootx()+root.winfo_width())
     table=next(w for w in descendants(root) if isinstance(w,ttk.Treeview))
     table.selection_set(table.get_children()[0]);button.invoke();root.update_idletasks()
     dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
     dialog.geometry('900x600');root.update_idletasks()
     translate=next(w for w in descendants(dialog) if isinstance(w,ttk.Button) and w.cget('text')=='ترجمة إلى الإنجليزية')
     self.assertTrue(translate.winfo_ismapped())
     self.assertGreaterEqual(translate.winfo_rooty(),dialog.winfo_rooty())
     self.assertLessEqual(translate.winfo_rooty()+translate.winfo_height(),dialog.winfo_rooty()+dialog.winfo_height())
     self.assertTrue(any(isinstance(w,ttk.Scrollbar) for w in descendants(dialog)))
    finally:root.destroy()
   with patch.object(pathlib.Path,'home',return_value=pathlib.Path(d)),patch.object(monitor.credential_store,'load_key',return_value=''),patch.object(tk.Tk,'mainloop',inspect):
    monitor.desktop()
if __name__=='__main__':unittest.main()
