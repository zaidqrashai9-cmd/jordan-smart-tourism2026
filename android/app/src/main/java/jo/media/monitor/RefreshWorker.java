package jo.media.monitor;
import android.content.Context;import androidx.work.*;
public class RefreshWorker extends Worker {
 public RefreshWorker(Context context,WorkerParameters params){super(context,params);}
 @Override public Result doWork(){try{MainActivity.call(getApplicationContext(),"/api/refresh","");return Result.success();}catch(Exception e){return Result.retry();}}
}
