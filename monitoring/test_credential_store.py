import unittest,os,tempfile,pathlib,sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import credential_store as c
class Tests(unittest.TestCase):
 def test_missing(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(c.load_key(pathlib.Path(d)/'missing'),'')
 def test_invalid(self):
  with self.assertRaises(ValueError):c.save_key(' ')
 @unittest.skipUnless(os.name=='nt','DPAPI requires Windows')
 def test_windows_roundtrip_and_delete(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'key.dpapi';key='test-only-not-a-real-api-key'
   c.save_key(key,p);self.assertNotIn(key.encode(),p.read_bytes())
   self.assertEqual(c.load_key(p),key)
   c.forget_key(p);self.assertFalse(p.exists());c.forget_key(p)
 @unittest.skipUnless(os.name=='nt','DPAPI requires Windows')
 def test_corrupt(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'key.dpapi';p.write_bytes(b'not-dpapi')
   with self.assertRaises(RuntimeError):c.load_key(p)
 def test_encrypt_failure_never_writes_plaintext(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'key'
   with patch.object(c,'_crypt',side_effect=RuntimeError('failed')):
    with self.assertRaises(RuntimeError):c.save_key('secret',p)
   self.assertFalse(p.exists())
if __name__=='__main__':unittest.main()
