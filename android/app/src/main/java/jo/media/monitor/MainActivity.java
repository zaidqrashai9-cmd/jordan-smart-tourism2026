package jo.media.monitor;
import android.app.*;import android.os.*;import android.content.*;import android.net.Uri;import android.webkit.*;import android.widget.*;import android.view.*;
import androidx.work.*;import java.util.concurrent.*;import java.io.*;import java.nio.charset.StandardCharsets;import org.json.JSONObject;
import com.chaquo.python.*;import com.chaquo.python.android.AndroidPlatform;
public class MainActivity extends Activity {
 private WebView web;private FrameLayout shell;private LinearLayout startup;private TextView startupText;private Button retry;volatile boolean uiReady=false;private final Handler startupHandler=new Handler(Looper.getMainLooper());private final ExecutorService executor=Executors.newSingleThreadExecutor();private String exportText="";
 static synchronized void init(Context c){if(!Python.isStarted())Python.start(new AndroidPlatform(c.getApplicationContext()));}
 static String call(Context c,String action,String body){init(c);return Python.getInstance().getModule("mobile").callAttr("execute",c.getFilesDir().getAbsolutePath(),action,body).toString();}
 @Override public void onCreate(Bundle state){super.onCreate(state);getWindow().setStatusBarColor(0xff123d32);
 shell=new FrameLayout(this);shell.setBackgroundColor(0xfff3f5f1);setContentView(shell);
 startup=new LinearLayout(this);startup.setOrientation(LinearLayout.VERTICAL);startup.setGravity(Gravity.CENTER);startup.setPadding(32,32,32,32);startup.setBackgroundColor(0xfff3f5f1);startup.setTag("startup");
 TextView title=new TextView(this);title.setText("رصد وحدة الاعلام");title.setTextSize(25);title.setTextColor(0xff123d32);title.setGravity(Gravity.CENTER);startup.addView(title);
 startupText=new TextView(this);startupText.setText("جارٍ فتح الواجهة…");startupText.setTextSize(16);startupText.setGravity(Gravity.CENTER);startupText.setPadding(0,28,0,28);startup.addView(startupText);
 retry=new Button(this);retry.setText("إعادة المحاولة");retry.setVisibility(View.GONE);retry.setOnClickListener(v->recreate());startup.addView(retry);
 shell.addView(startup,new FrameLayout.LayoutParams(-1,-1));
 shell.setFitsSystemWindows(true);
 try{
  web=new WebView(this);web.setLayerType(View.LAYER_TYPE_SOFTWARE,null);web.setTag("monitor-web");web.setBackgroundColor(0xfff3f5f1);shell.addView(web,0,new FrameLayout.LayoutParams(-1,-1));
  WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(true);settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);settings.setBlockNetworkLoads(true);
  web.addJavascriptInterface(new Bridge(),"Native");
  web.setWebChromeClient(new WebChromeClient(){@Override public boolean onConsoleMessage(ConsoleMessage m){if(m.messageLevel()==ConsoleMessage.MessageLevel.ERROR&&!uiReady)showStartupError("تعذر تشغيل الواجهة: "+m.message());return true;}});
  web.setWebViewClient(new WebViewClient(){
   @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){open(r.getUrl());return true;}
   @Override public void onReceivedError(WebView v,WebResourceRequest r,WebResourceError e){if(r.isForMainFrame())showStartupError("تعذر عرض الواجهة: "+e.getDescription());}
   @Override public boolean onRenderProcessGone(WebView v,RenderProcessGoneDetail d){shell.removeView(v);v.destroy();web=null;uiReady=false;showStartupError("توقف محرك عرض Android. أعد المحاولة أو حدّث Android System WebView.");return true;}
  });
  // The complete bundled page is supplied directly: no local-domain lookup,
  // intercepted main-frame request or internet is required to draw the UI.
  String html;try(InputStream in=getAssets().open("index.html");ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);html=out.toString("UTF-8");}
  web.loadDataWithBaseURL("https://appassets.androidplatform.net/",html,"text/html",null,"https://appassets.androidplatform.net/");
  startupHandler.postDelayed(()->{if(!uiReady&&!isDestroyed())showStartupError("لم يكتمل فتح الواجهة. جرّب إعادة المحاولة، وتأكد أن Android System WebView وChrome محدّثان.");},15000);
 }catch(Exception e){showStartupError("تعذر بدء محرك العرض: "+e.getClass().getSimpleName());}
 try{
  Constraints constraints=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
  WorkManager.getInstance(this).enqueueUniquePeriodicWork("hourly-tourism",ExistingPeriodicWorkPolicy.KEEP,new PeriodicWorkRequest.Builder(RefreshWorker.class,1,TimeUnit.HOURS).setConstraints(constraints).build());
 }catch(Exception ignored){/* Opening the interface must never depend on the scheduler. */}
 }
 void showStartupError(String message){runOnUiThread(()->{if(isDestroyed())return;String version="";try{android.content.pm.PackageInfo p=WebView.getCurrentWebViewPackage();if(p!=null)version=p.packageName+" "+p.versionName;}catch(Exception ignored){}startupText.setText(message+"\n\nAndroid "+Build.VERSION.RELEASE+" · "+version+"\nنسخة التطبيق 1.1");retry.setVisibility(View.VISIBLE);startup.setVisibility(View.VISIBLE);startup.bringToFront();});}
 private void open(Uri uri){if(!"https".equals(uri.getScheme()))return;try{startActivity(new Intent(Intent.ACTION_VIEW,uri));}catch(Exception e){Toast.makeText(this,"تعذر فتح الرابط",Toast.LENGTH_SHORT).show();}}
 public class Bridge {
 @JavascriptInterface public void ready(){runOnUiThread(()->{uiReady=true;startupHandler.removeCallbacksAndMessages(null);startup.setVisibility(View.GONE);});}
 @JavascriptInterface public void uiError(String message){if(!uiReady)showStartupError(message);}

 @JavascriptInterface public void request(int id,String action,String body){executor.execute(()->{try{String result=call(MainActivity.this,action,body);reply(id,true,result);}catch(Exception e){reply(id,false,e.getMessage()==null?"تعذر إتمام العملية":e.getMessage());}});}
 @JavascriptInterface public void copy(String text){runOnUiThread(()->((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("خبر",text)));}
 @JavascriptInterface public void share(String text,boolean whatsapp){runOnUiThread(()->{Intent i=new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,text);if(whatsapp)i.setPackage("com.whatsapp");try{startActivity(whatsapp?i:Intent.createChooser(i,"مشاركة الخبر"));}catch(Exception e){i.setPackage(null);startActivity(Intent.createChooser(i,"مشاركة الخبر"));}});}
 @JavascriptInterface public void exportFile(String text,String name,String type){runOnUiThread(()->{exportText=text;Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType(type).addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,name);startActivityForResult(i,10);});}
 @JavascriptInterface public void importFile(){runOnUiThread(()->startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("application/json").addCategory(Intent.CATEGORY_OPENABLE),11));}
 }
 private void reply(int id,boolean ok,String value){runOnUiThread(()->{if(!isDestroyed()&&web!=null)web.evaluateJavascript("nativeResult("+id+","+ok+","+JSONObject.quote(value)+")",null);});}
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();
 if(request==10){try(OutputStream out=getContentResolver().openOutputStream(uri)){out.write(exportText.getBytes(StandardCharsets.UTF_8));Toast.makeText(this,"تم الحفظ",Toast.LENGTH_SHORT).show();}catch(Exception e){Toast.makeText(this,"تعذر الحفظ",Toast.LENGTH_SHORT).show();}finally{exportText="";}}
 if(request==11)executor.execute(()->{try(InputStream in=getContentResolver().openInputStream(uri);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){out.write(b,0,n);if(out.size()>15000000)throw new IOException("الملف كبير");}String text=out.toString("UTF-8");runOnUiThread(()->web.evaluateJavascript("importArchive("+JSONObject.quote(text)+")",null));}catch(Exception e){runOnUiThread(()->Toast.makeText(this,"تعذر استيراد الملف",Toast.LENGTH_SHORT).show());}});
 }
 @Override public void onBackPressed(){if(web==null){super.onBackPressed();return;}web.evaluateJavascript("document.querySelector('dialog[open]')!==null",v->{if("true".equals(v))web.evaluateJavascript("document.querySelector('dialog[open]').close()",null);else super.onBackPressed();});}
 @Override protected void onDestroy(){super.onDestroy();startupHandler.removeCallbacksAndMessages(null);executor.shutdown();if(web!=null){web.removeJavascriptInterface("Native");web.destroy();}}
}
