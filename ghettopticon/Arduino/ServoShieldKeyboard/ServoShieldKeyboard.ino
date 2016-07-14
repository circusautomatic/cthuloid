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
#define SERVOMIN  150 // this is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  560 // this is the 'maximum' pulse length count (out of 4096)

//angle for each servo in degrees
volatile int16_t servoAngles[] =   {
  90, 0, 180, 0,    // left shoulder, upperarm, forearm, hand
  90, 180, 0, 0,    // right shoulder, upperarm, forearm, hand
  0, 90, 0          // neck, nod, face
};
const int NUM_SERVOS = sizeof(servoAngles) / sizeof(servoAngles[0]);

// our servo # counter
uint16_t servonum = 0;

const int degreeInc = 2;

void setup() {
  Serial.begin(9600);

  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
  
  for(int i = 0; i < NUM_SERVOS; i++) 
    pwm.setPWM(i, 0, map(servoAngles[i], 0, 180, SERVOMIN, SERVOMAX));
  
  Serial.println("Cardbot Servos activated.");
}

// you can use this function if you'd like to set the pulse length in seconds
// e.g. setServoPulse(0, 0.001) is a ~1 millisecond pulse width. its not precise!
void setServoPulse(uint8_t n, double pulse) {
  double pulselength;
  
  pulselength = 1000000;   // 1,000,000 us per second
  pulselength /= 60;   // 60 Hz
  pulselength /= 4096;  // 12 bits of resolution
  pulse *= 1000;
  pulse /= pulselength;
  pwm.setPWM(n, 0, pulse);
}

void loop() {  
  if (Serial.available())
  {
    char b = Serial.read();
    //Serial.print("I got: ");
    //Serial.println(b);
    
    // keyboard numbers 1-9 determine which servo we're talking to
    // '1' addresses index 0, etc.
    if (b >= '1' && b <= '9') {
      servonum = b - '1';
      Serial.print("Servo #");
      Serial.println(b);
    }
    
    // otherwise increment/decrement the servo position
    else {
      if (b == '-') servoAngles[servonum] -= degreeInc;
      else if (b == '=') servoAngles[servonum] += degreeInc;
      else return;

      // ensure we didn't go out of bounds
      if (servoAngles[servonum] < 0) {
        servoAngles[servonum] = 0;
        Serial.println("At movement limit");
      }
      if (servoAngles[servonum] > 180) {
        servoAngles[servonum] = 180;
        Serial.println("At movement limit");
      }
      
      Serial.print("Angle in degrees: ");
      Serial.println(servoAngles[servonum]);
      
      uint16_t pulselen = map(servoAngles[servonum], 0, 180, SERVOMIN, SERVOMAX);
      pwm.setPWM(servonum, 0, pulselen);
    }
  }
}
