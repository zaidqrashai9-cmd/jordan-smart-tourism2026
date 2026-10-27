package jo.media.monitor;
import android.app.*;import android.os.*;import android.content.*;import android.net.Uri;import android.webkit.*;import android.widget.*;import android.view.*;
import androidx.work.*;import java.util.concurrent.*;import java.io.*;import java.nio.charset.StandardCharsets;import org.json.JSONObject;
import com.chaquo.python.*;import com.chaquo.python.android.AndroidPlatform;
public class MainActivity extends Activity {
 private WebView web;private final ExecutorService executor=Executors.newSingleThreadExecutor();private String exportText="";
 static synchronized void init(Context c){if(!Python.isStarted())Python.start(new AndroidPlatform(c.getApplicationContext()));}
 static String call(Context c,String action,String body){init(c);return Python.getInstance().getModule("mobile").callAttr("execute",c.getFilesDir().getAbsolutePath(),action,body).toString();}
 @Override public void onCreate(Bundle state){super.onCreate(state);getWindow().setStatusBarColor(0xff123d32);web=new WebView(this);setContentView(web);
 // Leave system bars outside the reading area on edge-to-edge Android versions.
 web.setOnApplyWindowInsetsListener((v,i)->{v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());return i;});
 WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setAllowFileAccess(false);s.setAllowContentAccess(false);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
 web.addJavascriptInterface(new Bridge(),"Native");web.setWebViewClient(new WebViewClient(){
 @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){if(r.getUrl().toString().equals("https://app.local/index.html")){try{return new WebResourceResponse("text/html","UTF-8",getAssets().open("index.html"));}catch(Exception e){return null;}}return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0]));}
 @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){open(r.getUrl());return true;}
 });web.loadUrl("https://app.local/index.html");
 Constraints constraints=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
 WorkManager.getInstance(this).enqueueUniquePeriodicWork("hourly-tourism",ExistingPeriodicWorkPolicy.KEEP,new PeriodicWorkRequest.Builder(RefreshWorker.class,1,TimeUnit.HOURS).setConstraints(constraints).build());
 }
 private void open(Uri uri){if(!"https".equals(uri.getScheme()))return;try{startActivity(new Intent(Intent.ACTION_VIEW,uri));}catch(Exception e){Toast.makeText(this,"تعذر فتح الرابط",Toast.LENGTH_SHORT).show();}}
 public class Bridge {
 @JavascriptInterface public void request(int id,String action,String body){executor.execute(()->{try{String result=call(MainActivity.this,action,body);reply(id,true,result);}catch(Exception e){reply(id,false,e.getMessage()==null?"تعذر إتمام العملية":e.getMessage());}});}
 @JavascriptInterface public void copy(String text){runOnUiThread(()->((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("خبر",text)));}
 @JavascriptInterface public void share(String text,boolean whatsapp){runOnUiThread(()->{Intent i=new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,text);if(whatsapp)i.setPackage("com.whatsapp");try{startActivity(whatsapp?i:Intent.createChooser(i,"مشاركة الخبر"));}catch(Exception e){i.setPackage(null);startActivity(Intent.createChooser(i,"مشاركة الخبر"));}});}
 @JavascriptInterface public void exportFile(String text,String name,String type){runOnUiThread(()->{exportText=text;Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType(type).addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,name);startActivityForResult(i,10);});}
 @JavascriptInterface public void importFile(){runOnUiThread(()->startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("application/json").addCategory(Intent.CATEGORY_OPENABLE),11));}
 }
 private void reply(int id,boolean ok,String value){runOnUiThread(()->{if(!isDestroyed())web.evaluateJavascript("nativeResult("+id+","+ok+","+JSONObject.quote(value)+")",null);});}
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();
 if(request==10){try(OutputStream out=getContentResolver().openOutputStream(uri)){out.write(exportText.getBytes(StandardCharsets.UTF_8));Toast.makeText(this,"تم الحفظ",Toast.LENGTH_SHORT).show();}catch(Exception e){Toast.makeText(this,"تعذر الحفظ",Toast.LENGTH_SHORT).show();}finally{exportText="";}}
 if(request==11)executor.execute(()->{try(InputStream in=getContentResolver().openInputStream(uri);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){out.write(b,0,n);if(out.size()>15000000)throw new IOException("الملف كبير");}String text=out.toString("UTF-8");runOnUiThread(()->web.evaluateJavascript("importArchive("+JSONObject.quote(text)+")",null));}catch(Exception e){runOnUiThread(()->Toast.makeText(this,"تعذر استيراد الملف",Toast.LENGTH_SHORT).show());}});
 }
 @Override public void onBackPressed(){web.evaluateJavascript("document.querySelector('dialog[open]')!==null",v->{if("true".equals(v))web.evaluateJavascript("document.querySelector('dialog[open]').close()",null);else super.onBackPressed();});}
 @Override protected void onDestroy(){super.onDestroy();executor.shutdown();web.removeJavascriptInterface("Native");web.destroy();}
}
