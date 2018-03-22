#include <ax12.h>
#include <BioloidController2.h>    // use the bug-fixed version 

BioloidController Servos(1000000);
const int BroadcastID = 254;

int sinToServoPos(float sinx) {
  return round(512 + (sinx * 300));
}

void circle() {
  int id1 = 1;
  int id2 = id1 + 1;

  float seconds = 10;
  float msDuration = 1000 * seconds;
  
  long start = millis();
  long end = start + msDuration;
  long now;
  
  do {
    now = millis();
    float angle = (now - start) / msDuration * 2*3.14159;
    float sinx = sin(angle);
    float cosx = cos(angle);

    Servos.setCurPose(id1, sinToServoPos(sin(angle)));
    Servos.setCurPose(id2, sinToServoPos(cos(angle)));
    Servos.writePose();
    
    while(millis() < 30 + now);

  } while(now < end);
}

void setCompliance(int comp) {
  int ms = 50;
  
  Serial.println("setting copmpliance...");
  ax12SetRegister(1, AX_CW_COMPLIANCE_SLOPE, comp);   delay(ms); 
  ax12SetRegister(2, AX_CW_COMPLIANCE_SLOPE, comp);   delay(ms);
  ax12SetRegister(1, AX_CCW_COMPLIANCE_SLOPE, comp);  delay(ms); 
  ax12SetRegister(2, AX_CCW_COMPLIANCE_SLOPE, comp);  delay(ms);

  Serial.print("AX_CW_COMPLIANCE_SLOPE: ");
  Serial.print(ax12GetRegister(1, AX_CW_COMPLIANCE_SLOPE, 1));    delay(ms);
  Serial.print(' ');
  Serial.println(ax12GetRegister(2, AX_CW_COMPLIANCE_SLOPE, 1));  delay(ms);
  
  Serial.print("AX_CCW_COMPLIANCE_SLOPE: ");
  Serial.print(ax12GetRegister(1, AX_CCW_COMPLIANCE_SLOPE, 1));   delay(ms);
  Serial.print(' ');
  Serial.println(ax12GetRegister(2, AX_CCW_COMPLIANCE_SLOPE, 1)); delay(ms);
}

void setup() {
 // analogWrite(11, 250);
  Serial.begin(38400);
  Servos.setup(2);
  delay(500);
  ax12SetRegister2(BroadcastID, AX_GOAL_SPEED_L, 100);

  Serial.println("------------------------\nstarting...");
  delay(500);
    
  //Serial.print("punch: ");
  //Serial.println(ax12GetRegister(1, 48, 2));

  //Serial.println("turning torque enable off...");
  //ax12SetRegister(1, AX_TORQUE_ENABLE, 0); delay(100);
  //ax12SetRegister(2, AX_TORQUE_ENABLE, 0); delay(1000);

  //setCompliance(32);
  //circle();  

  //setCompliance(64);
  //circle();  

  setCompliance(128);
  circle();  
}

void loop() {
  // put your main code here, to run repeatedly:

}
