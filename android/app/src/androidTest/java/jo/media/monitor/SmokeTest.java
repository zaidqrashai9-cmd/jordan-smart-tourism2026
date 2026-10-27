package jo.media.monitor;
import androidx.test.ext.junit.runners.AndroidJUnit4;import androidx.test.platform.app.InstrumentationRegistry;import org.junit.Test;import org.junit.runner.RunWith;import org.json.*;import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class) public class SmokeTest {
 @Test public void archiveAndPythonPackages() throws Exception {
 android.content.Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
 JSONObject data=new JSONObject(MainActivity.call(c,"/api/news",""));assertTrue(data.has("items"));
 MainActivity.init(c);com.chaquo.python.Python.getInstance().getModule("trafilatura");com.chaquo.python.Python.getInstance().getModule("googlenewsdecoder");
 }
}
