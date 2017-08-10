#include <Conceptinetics.h>
#include <PWM.h>

// this flag will invert PWM output, for active-low devices
#define INVERT_HIGH_AND_LOW

int DMX_Address = 13;  // The DMX address of the first channel (using 1-based indexing)

// These pins will be mapped onto DMX channels in order (1-based indexing)
const int PWM_Pins[] = {7, 8, 44, 45};
const int Num_PWM_Pins = sizeof(PWM_Pins)/sizeof(*PWM_Pins);

const long PWM_Frequency = 1000;    // timer frequency for generating PWM
const long HR_PWM_Off = 300;       // High Resolution PWM value at which our LED turns off

// map a log function while converting from 8-bits to 16-bits
// dmx: input [0-255]
// output: [HR_PWM_Off-65535]
long DMXtoPWM(long dmx) {
  const float bottom = HR_PWM_Off;
  static const float coeff = log(65535.0 / bottom) / log(exp(1)) / 255;
  return round(bottom * exp(dmx * coeff));
}


//
// CTC-DRA-13-1 ISOLATED DMX-RDM SHIELD JUMPER INSTRUCTIONS
//
// If you are using the above mentioned shield you should 
// place the RXEN jumper towards G (Ground), This will turn
// the shield into read mode without using up an IO pin
//
// The !EN Jumper should be either placed in the G (GROUND) 
// position to enable the shield circuitry 
//   OR
// if one of the pins is selected the selected pin should be
// set to OUTPUT mode and set to LOGIC LOW in order for the 
// shield to work
//

//
// Pin number to change read or write mode on the shield
// Uncomment the following line if you choose to control 
// read and write via a pin
//
// On the CTC-DRA-13-1 shield this will always be pin 2,
// if you are using other shields you should look it up 
// yourself
//
///// #define RXEN_PIN                2


// Create a DMX slave controller
const int Num_DMX_Channels = Num_PWM_Pins;
DMX_Slave dmx_slave ( Num_DMX_Channels );

// If you are using an IO pin to control the shields RXEN
// the use the following line instead
///// DMX_Slave dmx_slave ( DMX_SLAVE_CHANNELS , RXEN_PIN );

void setup() {             
  Serial.begin(38400);

  Serial.print("DMX starting address: ");
  Serial.println(DMX_Address);
  dmx_slave.enable();  
  dmx_slave.setStartAddress(DMX_Address);

  // initialize the pins
  for(int i = 0; i < Num_PWM_Pins; i++) {
    Serial.print("setting PWM pin ");
    Serial.println(PWM_Pins[i]);
    pinMode(PWM_Pins[i], OUTPUT);
  }
 
  // setting pins 7-8 with timer 4
  TCCR4A = B00101001; // Phase and frequency correct PWM change at OCRA
  TCCR4B = B10001;  // System clock
  OCR4A = 0xffff;   // max pwm value

  // setting pins 44-45 with timer 5
  TCCR5A = B00101001; // Phase and frequency correct PWM change at OCRA
  TCCR5B = B10001;  // System clock
  OCR5A = 0xffff;   // max pwm value

}

long get_HR_DMX(int index) {
  int brightness = dmx_slave.getChannelValue(index + 1);
    
  //if(brightness > 0) Serial.println(brightness);

  // apply a logarithmic function to give finer control at lower brightness
  long hr = DMXtoPWM(brightness);
    
    //invert high and low
#ifdef INVERT_HIGH_AND_LOW
    hr = 65535 - hr;
#endif

  return hr;
}

void loop()
{
    // might need to put OCR4B first
    OCR4B = get_HR_DMX(0);    // mega pin 7
    OCR4C = get_HR_DMX(1);    // mega pin 8
    OCR5C = get_HR_DMX(2);    // mega pin 44
    OCR5B = get_HR_DMX(3);    // mega pin 45
}
