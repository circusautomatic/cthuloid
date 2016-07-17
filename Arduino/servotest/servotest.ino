/*************************************************** 
  This is an example for our Adafruit 16-channel PWM & Servo driver
  Servo test - this will drive 16 servos, one after the other

  Pick one up today in the adafruit shop!
  ------> http://www.adafruit.com/products/815

  These displays use I2C to communicate, 2 pins are required to  
  interface. For Arduino UNOs, thats SCL -> Analog 5, SDA -> Analog 4

  Adafruit invests time and resources providing this open source code, 
  please support Adafruit and open-source hardware by purchasing 
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.  
  BSD license, all text above must be included in any redistribution
 ****************************************************/

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
// you can also call it with a different address you want
//Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x41);

// Depending on your servo make, the pulse width min and max may vary, you 
// want these to be as small/large as possible without hitting the hard stop
// for max range. You'll have to tweak them as necessary to match the servos you
// have!
const int SERVO_MIN = 150; // this is the 'minimum' pulse length count (out of 4096)
const int SERVO_MAX = 560; // this is the 'maximum' pulse length count (out of 4096)
//const int SERVO_HALF = map(90, 0, 180, SERVO_MIN, SERVO_MAX);

// starting angles, not currently updated by commands
int angles[] = {
  90, 0, 180, 0,    // left shoulder, upperarm, forearm, hand
  90, 180, 0, 0,    // right shoulder, upperarm, forearm, hand
  0, 90, 0          // neck, nod, face
};

const int NUM_ANGLES = sizeof(angles) / sizeof(*angles);

uint16_t pwmFromAngle(int angle) {
  return map(angle, 0, 180, SERVO_MIN, SERVO_MAX);
}

void setup() {
  Serial.begin(9600);
  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
  
  for(int i = 0; i < NUM_ANGLES; i++) {
    pwm.setPWM(i, 0, pwmFromAngle(angles[i]));
  }
  
  Serial.print("Servos hello\n");
}

void loop() {  
  // commands are 3 bytes long and end with \n
  if (Serial.available() >= 3)
  {
    byte servonum = Serial.read();
    byte angle = Serial.read();
    byte newline = Serial.read();

    if (newline != '\n') { return; }
    if (angle > 180) angle = 180;

    //Pyserial freezes blender when arduino says stuff and blender doesnt read it
    /*Serial.print(servonum);
    Serial.print(':');
    Serial.print(angle);
    Serial.println(" degrees");*/

    pwm.setPWM(servonum, 0, map(angle, 0, 180, SERVO_MIN, SERVO_MAX));
  }
}
