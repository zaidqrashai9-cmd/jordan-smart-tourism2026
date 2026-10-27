package jo.media.monitor;
import androidx.test.ext.junit.runners.AndroidJUnit4;import androidx.test.platform.app.InstrumentationRegistry;import org.junit.Test;import org.junit.runner.RunWith;import org.json.*;import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class) public class SmokeTest {
 @Test public void mobileInterfaceLoads() throws Exception {
 androidx.test.platform.app.InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{});
 android.app.Instrumentation inst=InstrumentationRegistry.getInstrumentation();
 android.content.Context c=inst.getTargetContext();
 android.app.Activity activity=inst.startActivitySync(new android.content.Intent(c,MainActivity.class).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK));
 final java.util.concurrent.atomic.AtomicReference<String> dom=new java.util.concurrent.atomic.AtomicReference<>("");
 for(int i=0;i<100;i++){
  java.util.concurrent.CountDownLatch latch=new java.util.concurrent.CountDownLatch(1);
  inst.runOnMainSync(()->{android.view.ViewGroup content=activity.findViewById(android.R.id.content);android.webkit.WebView w=(android.webkit.WebView)content.getChildAt(0);w.evaluateJavascript("JSON.stringify({title:document.title,periods:document.querySelectorAll('[data-period]').length,keyword:document.querySelectorAll('#keyword option').length})",v->{dom.set(v);latch.countDown();});});
  latch.await(2,java.util.concurrent.TimeUnit.SECONDS);
  if(dom.get().contains("periods\\\":5"))break;
  android.os.SystemClock.sleep(200);
 }
 assertTrue(dom.get(),dom.get().contains("رصد وحدة الاعلام"));
 assertTrue(dom.get(),dom.get().contains("periods\\\":5"));
 android.graphics.Bitmap shot=inst.getUiAutomation().takeScreenshot();
 try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(c.getExternalFilesDir(null),"android-ui.png"))){shot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
 inst.runOnMainSync(activity::finish);
 }
 @Test public void archiveAndPythonPackages() throws Exception {
 android.content.Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
 JSONObject data=new JSONObject(MainActivity.call(c,"/api/news",""));assertTrue(data.has("items"));
 MainActivity.init(c);com.chaquo.python.Python.getInstance().getModule("trafilatura");com.chaquo.python.Python.getInstance().getModule("googlenewsdecoder");
 }
}
