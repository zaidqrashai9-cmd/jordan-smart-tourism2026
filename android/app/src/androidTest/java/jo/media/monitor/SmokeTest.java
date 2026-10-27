package jo.media.monitor;
import androidx.test.ext.junit.runners.AndroidJUnit4;import androidx.test.platform.app.InstrumentationRegistry;import org.junit.Test;import org.junit.runner.RunWith;import org.json.*;import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class) public class SmokeTest {
 @Test public void interfaceLoadsWithoutNetworkAndShowsRecovery() throws Exception {
 android.app.Instrumentation inst=InstrumentationRegistry.getInstrumentation();android.content.Context c=inst.getTargetContext();
 MainActivity activity=(MainActivity)inst.startActivitySync(new android.content.Intent(c,MainActivity.class).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK));
 final java.util.concurrent.atomic.AtomicReference<String> dom=new java.util.concurrent.atomic.AtomicReference<>("");
 JSONObject result=null;
 for(int i=0;i<100;i++){
  java.util.concurrent.CountDownLatch latch=new java.util.concurrent.CountDownLatch(1);
  inst.runOnMainSync(()->{android.webkit.WebView w=activity.findViewById(android.R.id.content).findViewWithTag("monitor-web");w.evaluateJavascript("JSON.stringify({ready:window.__monitorReady===true,title:document.title,periods:document.querySelectorAll('[data-period]').length,keywords:document.querySelectorAll('#keyword option').length,header:document.querySelector('h1')?document.querySelector('h1').getBoundingClientRect().height:0})",v->{dom.set(v);latch.countDown();});});
  latch.await(2,java.util.concurrent.TimeUnit.SECONDS);
  try{result=new JSONObject((String)new JSONTokener(dom.get()).nextValue());if(result.optBoolean("ready")&&activity.uiReady)break;}catch(Exception ignored){}
  android.os.SystemClock.sleep(200);
 }
 assertNotNull(dom.get(),result);assertTrue(dom.get(),result.getBoolean("ready"));assertTrue(activity.uiReady);
 assertEquals("رصد وحدة الاعلام",result.getString("title"));assertEquals(5,result.getInt("periods"));assertEquals(4,result.getInt("keywords"));assertTrue(result.getDouble("header")>20);
 inst.runOnMainSync(()->{assertEquals(android.view.View.GONE,activity.findViewById(android.R.id.content).findViewWithTag("startup").getVisibility());activity.showStartupError("اختبار رسالة خطأ العرض");assertEquals(android.view.View.VISIBLE,activity.findViewById(android.R.id.content).findViewWithTag("startup").getVisibility());});
 inst.runOnMainSync(activity::finish);
 }
 @Test public void archiveAndPythonPackages() throws Exception {
 android.content.Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
 JSONObject data=new JSONObject(MainActivity.call(c,"/api/news",""));assertTrue(data.has("items"));
 MainActivity.init(c);com.chaquo.python.Python.getInstance().getModule("trafilatura");com.chaquo.python.Python.getInstance().getModule("googlenewsdecoder");
 }
}
