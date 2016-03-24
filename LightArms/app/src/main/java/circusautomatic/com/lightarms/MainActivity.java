package circusautomatic.com.lightarms;

import android.content.Context;
import android.content.pm.ActivityInfo;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PointF;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.util.AttributeSet;
import android.view.Menu;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.View;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.Socket;
import java.net.UnknownHostException;
import java.util.ArrayList;


class LightArmMultitouchView extends View {

    private static final int SIZE = 150;

    class Arm {
        public Socket socket;
        public int id;
        PointF point;

        public Arm(Socket s) {
            socket = s;
            point = new PointF();
            unassign();
        }

        void assign(int i) { id = i; }
        void unassign() { id = -1; }
        boolean assigned() { return id != -1; }
    }

    private ArrayList<Arm> mArms = new  ArrayList<Arm>();

    Arm findArm(int id) {
        for(int i = 0; i < mArms.size(); i++) {
            if(mArms.get(i).id == id) return mArms.get(i);
        }
        return null;
    }

    private Paint mPaint;
    private int[] colors = { Color.BLUE, Color.GREEN, Color.MAGENTA,
            Color.BLACK, Color.CYAN, Color.GRAY, Color.RED, Color.DKGRAY,
            Color.LTGRAY, Color.YELLOW };

    private Paint textPaint;

    private String response = "";
    //private Socket socket = null;
    //private String SERVER_IP = "10.0.0.74";

    private int SERVERPORT = 1337;
    //PrintWriter socketOut = null;

    //private String ips[] = {"192.168.0.159"};
    private String ips[] = {"10.0.0.74", "10.0.0.72"};
    //private Socket sockets[] = new Socket[ips.length];

    Thread socketThread;

    public void writeToSocket(Socket s, String cmd) {
        try {
            PrintWriter socketOut = new PrintWriter(new BufferedWriter(
                    new OutputStreamWriter(s.getOutputStream())),
                    true);
            socketOut.println(cmd + "\n");
        } catch (IOException e) {
            e.printStackTrace();
            response = "IOException socketOut: " + e.toString();
        }
    }

    class ClientThread implements Runnable {

        @Override
        public void run() {

            for(int i = 0; i < ips.length; i++) {
            //for(int i = 0; i < 2; i++) {
                try {
                    InetAddress serverAddr = InetAddress.getByName(ips[i]);
                    Socket socket = new Socket(serverAddr, SERVERPORT);
                    writeToSocket(socket, "speed 40");
                    mArms.add(new Arm(socket));

                } catch (UnknownHostException e) {
                    e.printStackTrace();
                    response = "UnknownHostException: " + e.toString();
                } catch (IOException e) {
                    e.printStackTrace();
                    response = "IOException: " + e.toString();
                }
            }
        }

    }

    public LightArmMultitouchView(Context context, AttributeSet attrs) {
        super(context, attrs);
        initView();

        socketThread = new Thread(new ClientThread());
        socketThread.start();
    }

    private void initView() {
        mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        // set painter color to a color you like
        mPaint.setColor(Color.BLUE);
        mPaint.setStyle(Paint.Style.FILL_AND_STROKE);
        textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        textPaint.setTextSize(20);
    }

    int angleFromPixel(float px, int max) {
        int lower = 200, upper = 824;
        int mid = (lower + upper) / 2;
        int halfrange = mid - lower;

        int angle = (int)(mid + 2*halfrange * (px/(float)max - .5));
        if(angle < lower) angle = lower;
        if(angle > upper) angle = upper;
        return angle;
    }

    void sendUpdate(Arm arm) {
        if(arm == null) return;

        float pxBase = arm.point.x;
        float pxWrist = arm.point.y;

        int angleBase = angleFromPixel(pxBase, getWidth());
        int angleWrist = angleFromPixel(pxWrist, getHeight());

        String cmd = "s 1:" + angleBase + " 2:" + angleWrist;
        writeToSocket(arm.socket, cmd);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {

        // get pointer index from the event object
        int pointerIndex = event.getActionIndex();

        // get pointer ID
        int pointerId = event.getPointerId(pointerIndex);

        // get masked (not specific to a pointer) action
        int maskedAction = event.getActionMasked();

        switch (maskedAction) {

            case MotionEvent.ACTION_DOWN:
            case MotionEvent.ACTION_POINTER_DOWN: {
                // We have a new pointer. Lets add it to the list of pointers
                Arm arm = null;

                // find unassigned arm
                for(int i = 0; i < mArms.size(); i++) {
                  arm = mArms.get(i);
                  if(arm.assigned()) arm = null;
                  else break;
                }

                if(arm != null)  {
                    arm.assign(pointerId);
                    arm.point.x = event.getX(pointerIndex);
                    arm.point.y = event.getY(pointerIndex);
                    sendUpdate(arm);
                }

                break;
            }
            case MotionEvent.ACTION_MOVE: { // a pointer was moved
                for (int size = event.getPointerCount(), i = 0; i < size; i++) {
                    Arm arm = findArm(event.getPointerId(i));
                    if (arm != null) {
                        arm.point.x = event.getX(i);
                        arm.point.y = event.getY(i);
                        sendUpdate(arm);
                    }
                }
                break;
            }
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_POINTER_UP:
            case MotionEvent.ACTION_CANCEL: {
                Arm arm = findArm(pointerId);
                if(arm != null) arm.unassign();
                break;
            }
        }
        invalidate();

        return true;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        //mPaint.setColor(Color.BLACK);
        //canvas.drawLine(getWidth()/2, 0, getWidth()/2, getHeight(), mPaint);

        // draw all pointers
        for (int size = mArms.size(), i = 0; i < size; i++) {
            Arm arm = mArms.get(i);
            if(arm == null) continue;

            PointF point = arm.point;
            if (point != null)
                mPaint.setColor(colors[i % 9]);
            canvas.drawCircle(point.x, point.y, SIZE, mPaint);
        }

        String output = !response.isEmpty()? response: "";//"Total pointers: " + mActivePointers.size();
        canvas.drawText(output, 10, 40 , textPaint);
    }

}

public class MainActivity extends ActionBarActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT);
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }
}
