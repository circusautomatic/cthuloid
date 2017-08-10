// Arduino sketch which outputs PWM for a set of channels based on serial input.
// Serial commands accepted:
// - pwm <pwm1> <pwm2> ..., where <pwmN> is 0-65535 and N is up to NumChannels
// - pwm <index1>:<pwm1> <index2>:<pwm2> ..., where <indexN> is 1-based index into the PWMPins list
// - plevel <level>, change the amount of response text
//////////////////////////////////////////////////////////////////////////////////////


#include <PWM.h>
#include <UIPEthernet.h>


/////////////////////////////////////////////////////////////////////////////////////
// PWM globals
/////////////////////////////////////////////////////////////////////////////////////

// this flag will invert PWM output (255-output), for active-low devices
#define INVERT_HIGH_AND_LOW

#define MAX_PWM 65535


const int PWM_Pins[] = {/*3, */5/*, 6, 13, 10 11/*, 12*/};
const int NumPWMPins = sizeof(PWM_Pins) / sizeof(*PWM_Pins);
const int fanPin = 6;
const long PWM_Frequency = 1000;    // timer frequency for generating PWM
const long HR_PWM_Off = 300;       // High Resolution PWM value at which our LED turns off
const uint16_t PORT = 1337;
const uint8_t ID_IP = 251;
static uint8_t MAC[6] = {0x00, 0x01, 0x02, 0x03, 0xff, 0xfe};
IPAddress IP(10, 0, 0, ID_IP);
IPAddress GATEWAY(10, 0, 0, 1);
IPAddress SUBNET(255, 255, 255, 0);

EthernetServer TCPserver(PORT);

// print to the current ethernet client if there is one
EthernetClient Client;








long DMXtoPWM(long dmx) {
  const float bottom = HR_PWM_Off;
  static const float coeff = log(65535.0 / bottom) / log(exp(1)) / 255;
  return round(bottom * exp(dmx * coeff));
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////
// setup & loop
///////////////////////////////////////////////////////////////////////////////////////////////////////////

void setup() {
  Serial.begin(9600);


  // setup ethernet module
  // TODO: assign static IP based on lowest present servo ID
  Serial.println("Starting ethernet server on address: ");

  Ethernet.begin(MAC, IP);

  TCPserver.begin();
  Serial.println(Ethernet.localIP());



  // initialize the pins
  for (int i = 0; i < NumPWMPins; i++) {
    Serial.print("setting PWM pin ");
    Serial.println(PWM_Pins[i]);
    pinMode(PWM_Pins[i], OUTPUT);
  }

  // setting pins 7-8 with timer 4
  // TCCR4A = B00101001; // Phase and frequency correct PWM change at OCRA
  //  TCCR4B = B10001;  // System clock
  //  OCR4A = 0xffff;   // max pwm value

}

void loop() {

  // see if a client wants to say something; if so, save them as the client to respond to
  if (EthernetClient client = TCPserver.available()) {
    //client.println("Allo");
    Client = client;
  }

  if (Client)
  {
    //bool gotData = false;
    while (Client.available() > 0)
    {
      char c = Client.read();
      //gotData = true;
    }
    //if(gotData) Client.println("DATA from Server!");
  }

}
