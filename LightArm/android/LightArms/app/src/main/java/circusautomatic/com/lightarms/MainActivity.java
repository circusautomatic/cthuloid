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
        //public Socket socket;
        public ArrayList<Socket> sockets = new ArrayList<Socket>();
        public int id;
        PointF point;

        public Arm() {
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
    private int[] colors = { Color.BLUE, Color.RED, Color.GREEN,
            Color.BLACK, Color.CYAN, Color.GRAY, Color.RED, Color.DKGRAY,
            Color.LTGRAY, Color.YELLOW };

    private Paint textPaint;

    private String response = "";
    //private Socket socket = null;
    //private String SERVER_IP = "10.0.0.74";

    //private int SERVERPORT = 1337;
    //PrintWriter socketOut = null;

    //private String ips[] = {"192.168.0.159"};

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

        Socket makeSocket(String ip, int port) {
            try {
                InetAddress serverAddr = InetAddress.getByName(ip);
                Socket socket = new Socket(serverAddr, port);
                writeToSocket(socket, "speed 40");
                return socket;
            } catch (UnknownHostException e) {
                e.printStackTrace();
                response = "UnknownHostException: " + e.toString();
            } catch (IOException e) {
                e.printStackTrace();
                response = "IOException: " + e.toString();
            }

            return null;
        }

        @Override
        public void run() {
            int port = 1337;
            Arm arm;
            Socket s;

            arm = new Arm();
            mArms.add(arm);
            s = makeSocket("10.0.0.74", port);
            if(s != null) arm.sockets.add(s);
            s = makeSocket("10.0.0.72", port);
            if(s != null) arm.sockets.add(s);

            arm = new Arm();
            mArms.add(arm);
            s = makeSocket("10.0.0.71", port);
            if(s != null) arm.sockets.add(s);
            s = makeSocket("10.0.0.73", port);
            if(s != null) arm.sockets.add(s);
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

    int angleFromPixel(float px, float max) {
        //int lower = 200, upper = 824;
        int lower = 200+200, upper = 824-200;
        int mid = (lower + upper) / 2;
        int halfrange = mid - lower;

        int angle = (int)(mid + 2*halfrange * -(px/max - .5));
        if(angle < lower) angle = lower;
        if(angle > upper) angle = upper;
        return angle;
    }

    void sendUpdate(Arm arm) {
        if(arm == null) return;

        float pxBase = arm.point.x;
        float pxWrist = arm.point.y;
        float maxWidth = getWidth();
        float maxHeight = getHeight();

        int angleBase = angleFromPixel(pxBase, maxWidth);
        int angleWrist = angleFromPixel(pxWrist, maxHeight);

        // calculate intensity
        double offsetX = Math.abs((pxBase/maxWidth - .5));
        double offsetY = Math.abs((pxWrist/maxHeight - .5));
        //double mag = Math.sqrt(offsetX*offsetX + offsetY*offsetY);
        double mag = Math.max(offsetX, offsetY);

        //int intensity = 10;
        int intensity = (int)Math.floor(255 * .25 * (.5/mag - 1));
        if(intensity > 255) intensity = 255;
        if(intensity < 10) intensity = 10;

        String cmd = "s 1:" + angleBase + " 2:" + angleWrist;
        cmd += "\npwm " + intensity;
        for(Socket s: arm.sockets) writeToSocket(s, cmd);
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
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_LANDSCAPE);
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
