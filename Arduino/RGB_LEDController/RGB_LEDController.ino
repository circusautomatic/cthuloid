// Arduino sketch which outputs PWM for a set of channels based on serial input.
// Serial commands accepted:
// - pwm <pwm1> <pwm2> ..., where <pwmN> is 0-65535 and N is up to NumChannels
// - pwm <index1>:<pwm1> <index2>:<pwm2> ..., where <indexN> is 1-based index into the PWMPins list
// - plevel <level>, change the amount of response text
// 
// NOTE: initHRPWM and myHRWrite are set specifically to work on MEGAS. It could be tuned to work on
// unos.
//////////////////////////////////////////////////////////////////////////////////////

#include <SC.h>
#include "Adafruit_TLC59711.h"
#include <SPI.h>
//#include <PWM.h>

// Comment this out to read and write from Serial instead of Ethernet.
// Arduino IDE is wigging out when selecting which ethernet library to use; see line 35.
#define COMM_ETHERNET


/////////////////////////////////////////////////////////////////////////////////////
// PWM globals
/////////////////////////////////////////////////////////////////////////////////////

// this flag will invert PWM output (65535 - PWM), for active-low devices
#define INVERT_HIGH_AND_LOW

#define RED_MAX_PWM 36000
#define MAX_PWM 65535
//#define PWM_FREQ 1000

// How many boards do you have chained?
#define NUM_TLC59711 1

#define data   11
#define clock  13

Adafruit_TLC59711 tlc = Adafruit_TLC59711(NUM_TLC59711, clock, data);

// change initHRPWM and myHRWrite if you change these pins
// The first pin is assumed to be red, second assume to be green, etc.
//const int PWMPins[] = {7, 8, 44, 45};
const int NumPWMPins = 12;//sizeof(PWMPins)/sizeof(*PWMPins);

// Ethernet via ENC28J60 
// Library: https://github.com/ntruchsess/arduino_uip
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Pinout - Arduino Mega:
// VCC (Green) -   3.3V
// GND (Gr Wh) -    GND 
// SCK (Bl Wh) - Pin 52
// SO  (Blue)  - Pin 50
// SI  (Br Wh) - Pin 51
// CS  (Brown) - Pin 53  # Selectable with the ether.begin() function
//
// Pinout - Arduino Uno:
// VCC (Green) -   3.3V
// GND (Gr Wh) -    GND
// SCK (Bl Wh) - Pin 13
// SO  (Blue)  - Pin 12  
// SI  (Br Wh) - Pin 11
// CS  (Brown) - Pin 8   # Selectable with the ether.begin() function
#ifdef COMM_ETHERNET
  
  // For ENC28J60 card
  //#include <UIPEthernet.h>
  
  // For Arduino Ethernet Shield
  #include <SPI.h>
  #include <Ethernet.h>
  //For Arduino Nano + nano ethernet shield
  //#include <UIPEthernet.h>
  const uint16_t PORT = 1337;
  const uint8_t ID_IP = 84;
  static uint8_t MAC[6] = {0x00,0x01,0x02,0x03,0xff,ID_IP};

  IPAddress IP(10,0,0,ID_IP);
  IPAddress GATEWAY(10,0,0,1);
  IPAddress SUBNET(255, 255, 255, 0);

  EthernetServer TCPserver(PORT);

  // print to the current ethernet client if there is one
  EthernetClient Client;
  #define gPrinter Client
#endif

#include <PrintLevel.h>


const char *MsgPWMTupleFormatError = "Error: takes up to 6 arguments between 0 and 255";

/////////////////////////////////////////////////////////////////////////////////////////
// Command Manager and forward declarations for commands accessible from text interface
/////////////////////////////////////////////////////////////////////////////////////////

struct IDTuple { int id; long value; };

int parseID(const char *arg);
int parseListOfIDs(int *outIDs, int maxIDs);

void cmdUnrecognized(const char *cmd);
void cmdPWMPins();
void cmdSetPrintLevel();

SerialCommand::Entry CommandsList[] = {
  {"plevel", cmdSetPrintLevel},
  {"pwm",    cmdPWMPins},
  {NULL,     NULL}
};

SerialCommand CmdMgr(CommandsList, cmdUnrecognized);


/////////////////////////////////////////////////////////////////////////////////////////////
// helpers
/////////////////////////////////////////////////////////////////////////////////////////////

unsigned long invertPWM(unsigned long c) {
  #ifdef INVERT_HIGH_AND_LOW
    c = 65535 - c;
  #endif
  return c;
}

//void initHRPWM() {
//  // setting MEGA pins 7-8 with timer 4
//  TCCR4A = B00101001; // Phase and frequency correct PWM change at OCRA
//  TCCR4B = B10001;  // System clock
//  OCR4A = 0xffff;   // max pwm value
//
//  // setting MEGA pins 44-45 with timer 5
//  TCCR5A = B00101001; // Phase and frequency correct PWM change at OCRA
//  TCCR5B = B10001;  // System clock
//  OCR5A = 0xffff;   // max pwm value
//}

//void myHRWrite(int pin, unsigned value) {
//    /*printAlways("setting pin to value: ");
//    printAlways(pin);
//    printAlways(" ");
//    printlnAlways(value);*/
//    
//    switch(pin) {
//      case 7: OCR4B = value;  break;   // MEGA pin 7
//      case 8: OCR4C = value;  break;   // MEGA pin 8
//      case 44: OCR5C = value; break;   // MEGA pin 44
//      case 45: OCR5B = value; break;   // MEGA pin 45
//      default: printlnError("invalid pin");
//    }
//}

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns 0 if there is a parse error or the ID is out of range.
int parseID(const char *arg) {
  char *end;
  int id = strtol(arg, &end, 10);

  if(*end != '\0' || id < 1 || id > 253) {
      printlnError("Error: ID must be between 1 and 253");
      return 0;
  }
  
  return id;
}

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns -1 if there is a parse error or the PWM value is out of range.
long parsePWM(const char *arg, long maxPWM) {
  char *end;
  long v = strtol(arg, &end, 10);

  if(*end != '\0' || v < 0 || v > maxPWM) {
      printlnError("Error: PWM value must be between 0 and ");
      printlnError(maxPWM);
      return -1;
  }
  
  return v;
}

void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

// expects space-delimited ints 0-65535, or space delimited <index>:<pwm> pairs
void cmdPWMPins() {
  const char *SetPWMUsageMsg = "Error: takes up to 4 arguments between 0 and 65535 (except argument 3's max is 36000).";

  long channelValues[NumPWMPins] = {0};
  int count = 0;

  char *arg = CmdMgr.next();
  if(arg == NULL) {
   printlnError("Error: no arguments");
   return;
  }
  
  do {
    int index;
    long value;
    
    if(count >= NumPWMPins) {
      printlnError(SetPWMUsageMsg);
      return;
    }

    char *end;
    index = count;
    value = parsePWM(arg, count == 0? RED_MAX_PWM: MAX_PWM);
    if (value < 0) {
      printlnError(SetPWMUsageMsg);
      return;
    }
    
    /*printInfo("Set pin ");
    printInfo(PWMPins[index]);
    printInfo(" to ");
    printlnInfo(value);*/
    channelValues[index] = value;
    count++;
  } while(arg = CmdMgr.next());
  
  /*for(int i = 0; i < count; i++) {
    unsigned long c = channelValues[i];
    //analogWrite(PWMPins[i], invertPWM(c));
    printlnAlways(c);
    myHRWrite(PWMPins[i], invertPWM(c));
  }*/

  tlc.setLED(0, channelValues[0], channelValues[1], channelValues[2]);
  tlc.write();  

  printAck("OK set ");
  printAck(count);
  printlnAck(" pins");
}

void cmdSetPrintLevel() {  
  if(char *arg = CmdMgr.next()) {
    if(CmdMgr.next()) {
      printlnAlways("Error: takes 0 or 1 arguments");
      return;
    }
    
    if(!PrintLevel::set(arg)) {
      PrintLevel::printErrorString();
      return;
    }
  }
  
  printAck("print level ");
  printlnAck(PrintLevel::toString());
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////
// setup & loop
///////////////////////////////////////////////////////////////////////////////////////////////////////////

void setup() {
  Serial.begin(38400);
  Serial.println("RGB Controller");

#ifdef COMM_ETHERNET
  // setup ethernet module
  // TODO: assign static IP based on lowest present servo ID
  Serial.print("Starting ethernet server on address: ");

  Ethernet.begin(MAC, IP, GATEWAY, GATEWAY, SUBNET);
    
  TCPserver.begin();
  Serial.println(Ethernet.localIP());
#endif

  pinMode(10, OUTPUT);
  tlc.begin();
  tlc.write();

  // Initialize the high resolution PWM library.
  // Frequency: 10000 Hz
  // Run PWM.h example sketch to see all possible PWM settings for a given pin
//  InitTimersSafe(); //initialize all timers except for 0, to save time keeping functions
  
/*  for(int i = 0; i < NumPWMPins; i++) {
    pinMode(PWMPins[i], OUTPUT);
    analogWrite(PWMPins[i], 0);
    //Serial.print("setting PWM pin ");
    //Serial.print(PWMPins[i]);
    //Serial.print(" frequeny: ");
    //Serial.println(SetPinFrequency(PWMPins[i], PWM_FREQ));
  }

  initHRPWM();
*/
  /*    OCR4B = 65535;    // MEGA pin 7
      OCR4C = 65535;    // MEGA pin 8
      OCR5C = 45000;    // MEGA pin 44
      OCR5B = 45000;    // MEGA pin 44
*/
  /*printAlways("PWM controller. PWM pins are expected to be ");
  
/*  for(int i = 0; i < NumPWMPins; i++) {
    pinMode(PWMPins[i], OUTPUT);
    
    // high = off, so start high
    //analogWrite(PWMPins[i], 255);

    if(i != 0) printAlways(", ");
    printAlways(PWMPins[i]);
  }
  
  printAlways(".\n");*/
}

void loop() {
// read from EITHER serial OR network; otherwise we'll need multiple read buffers...
#ifndef COMM_ETHERNET
  CmdMgr.readSerial();

#else
  // TODO: edit EthernetServer to separate accepting a connection
  // from reading from one, so we can great connectors
  // Multiple connections? Yikes. Requires multiple buffers. Probably not.

  // see if a client wants to say something; if so, save them as the client to respond to
  if(EthernetClient client = TCPserver.available()) {
    //client.println("Allo");
    Client = client;
  }

  if(Client)
  {
    //bool gotData = false;
    while(Client.available() > 0)
    {
      char c = Client.read();
      CmdMgr.handleChar(c);
      //gotData = true;
    }
    //if(gotData) Client.println("DATA from Server!");
  }
#endif
}
