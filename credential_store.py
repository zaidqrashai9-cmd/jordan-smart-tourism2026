"""Per-Windows-user DPAPI credential storage outside the distributable app."""
import os,pathlib,ctypes,tempfile
def key_path():
    base=os.environ.get('LOCALAPPDATA')
    return (pathlib.Path(base) if base else pathlib.Path.home()/'AppData'/'Local')/'JordanTourismMonitor'/'gemini-key.dpapi'
def _crypt(data,decrypt=False):
    if os.name!='nt':raise RuntimeError('حفظ المفتاح المشفر متاح على Windows فقط')
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_ubyte))]
    raw=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(raw,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
    if decrypt:
        fn=crypt.CryptUnprotectData
        fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
        args=(ctypes.byref(source),None,None,None,None,1,ctypes.byref(out))
    else:
        fn=crypt.CryptProtectData
        fn.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
        # No LOCAL_MACHINE flag: protected for the current Windows user.
        args=(ctypes.byref(source),'Media Unit Gemini key',None,None,None,1,ctypes.byref(out))
    fn.restype=wintypes.BOOL
    if not fn(*args):raise RuntimeError('تعذر استخدام تشفير Windows؛ لم يحفظ المفتاح كنص عادي')
    try:return ctypes.string_at(out.pbData,out.cbData)
    finally:kernel.LocalFree(ctypes.cast(out.pbData,ctypes.c_void_p))
def save_key(key,path=None):
    key=key.strip()
    if not key or len(key)>512 or any(c.isspace() for c in key):raise ValueError('أدخل مفتاحا صالحا أولا')
    encrypted=_crypt(key.encode('utf-8'))
    target=pathlib.Path(path) if path else key_path();target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='gemini-',suffix='.tmp',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(encrypted)
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def load_key(path=None):
    target=pathlib.Path(path) if path else key_path()
    if not target.exists():return ''
    try:return _crypt(target.read_bytes(),decrypt=True).decode('utf-8')
    except Exception:raise RuntimeError('تعذر قراءة المفتاح المحفوظ. احذفه وأعد إدخاله على حساب Windows الحالي.') from None
def forget_key(path=None):
    target=pathlib.Path(path) if path else key_path()
    target.unlink(missing_ok=True)
