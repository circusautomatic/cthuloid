// Arduino sketch which outputs PWM for a set of channels based on serial input.
// Serial commands accepted:
// - pwm <pwm1> <pwm2> ..., where <pwmN> is 0-65535 and N is up to NumChannels
// - pwm <index1>:<pwm1> <index2>:<pwm2> ..., where <indexN> is 1-based index into the PWMPins list
// - plevel <level>, change the amount of response text
//////////////////////////////////////////////////////////////////////////////////////

#include <SC.h>
#include <PWM.h>

// Comment this out to read and write from Serial instead of Ethernet.
// Arduino IDE is wigging out when selecting which ethernet library to use; see line 35.
#define COMM_ETHERNET


/////////////////////////////////////////////////////////////////////////////////////
// PWM globals
/////////////////////////////////////////////////////////////////////////////////////

// this flag will invert PWM output (255-output), for active-low devices
#define INVERT_HIGH_AND_LOW

#define MAX_PWM 65535

const int PWMPins[] = {/*3, 5, 6, 9, 10,*/ 11};  // Arduino Uno PWM pins
const int NumPWMPins = sizeof(PWMPins)/sizeof(*PWMPins);


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

  const uint16_t PORT = 1337;
  const uint8_t ID_IP = 69;
  static uint8_t MAC[6] = {0x00,0x01,0x02,0x03,0xa4,ID_IP};

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
boolean parsePWMTuple(char *s, IDTuple *out);
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
long parsePWM(const char *arg) {
  char *end;
  long v = strtol(arg, &end, 10);

  if(*end != '\0' || v < 0 || v > MAX_PWM) {
      printlnError("Error: PWM value must be between 0 and ");
      printlnError(MAX_PWM);
      return -1;
  }
  
  return v;
}

// convert "<index>:<value>" into 2 integers in a struct
// returns false on error
boolean parsePWMTuple(char *s, IDTuple *out) {
  char *sIndex = strtok(s, ":");
  if(sIndex == NULL) {
    printlnError(MsgPWMTupleFormatError);
    return false;
  }
  
  int index = parseID(sIndex);
  if(index == 0) return false;

  char *sPWM = strtok(NULL, ":");
  if(sPWM == NULL) {
    printlnError(MsgPWMTupleFormatError);
    return false;
  }
  
  long pwm = parsePWM(sPWM);
  if(pwm == -1) return false;
  
  out->id = index;
  out->value = (int)pwm;
  return true;
}


void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

// expects space-delimited ints 0-65535, or space delimited <index>:<pwm> pairs
void cmdPWMPins() {
  const char *SetPWMUsageMsg = "Error: takes up to 6 arguments between 0 and 65535, or <index>:<value> pairs where <index> starts at 1.";

  long channelValues[NumPWMPins];
  int count = 0;

  char *arg = CmdMgr.next();
  if(arg == NULL) {
   printlnError("Error: no arguments");
   return;
  }
  
  // see if we have a <index>:<value> tuple, or just an integer
  boolean parsingTuples = strstr(arg, ":") != NULL;
  
  do {
    int index;
    long value;
    
    if(count >= NumPWMPins) {
      printlnError(SetPWMUsageMsg);
      return;
    }

    // <index>:<PWM value>
    if(parsingTuples) {
      IDTuple tuple;
      if(parsePWMTuple(arg, &tuple) == false) return;
      index = tuple.id - 1;   // convert to zero-based index
      value = tuple.value;
      
      if(index < 0 || index >= NumPWMPins) {
        printError("Index must be between 1 and ");
        printlnError(NumPWMPins);
        return;
      }
    }
    
    // just a PWM value
    else {
      char *end;
      index = count;
      value = parsePWM(arg);
      if (value < 0) {
        printlnError(SetPWMUsageMsg);
        return;
      }
    }
    
    printInfo("Set pin ");
    printInfo(PWMPins[index]);
    printInfo(" to ");
    printlnInfo(value);
    channelValues[index] = value;
    count++;
  } while(arg = CmdMgr.next());
  
  for(int i = 0; i < count; i++) {
    long c = channelValues[i];
#ifdef INVERT_HIGH_AND_LOW
    c = MAX_PWM - c;
#endif
    //analogWrite(PWMPins[i], c);
    pwmWriteHR(PWMPins[i], c);
  }
  
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
  
  //Frequency: 151 Hz
  //Number of Possible Duties: 52981
  //Resolution: 15 bit
  //Tests indicate full 16 bits of PWM division
  InitTimersSafe(); //initialize all timers except for 0, to save time keeping functions
  Serial.print("setting PWM pin frequeny: ");
  Serial.println(SetPinFrequency(PWMPins[0], 151));    // TODO for all PWM pins on arduino mega

#ifdef COMM_ETHERNET
  // setup ethernet module
  // TODO: assign static IP based on lowest present servo ID
  Serial.print("Starting ethernet server on address: ");

  Ethernet.begin(MAC, IP);//, GATEWAY, SUBNET);
    
  TCPserver.begin();
  Serial.println(Ethernet.localIP());
#endif

  printAlways("PWM controller. PWM pins are expected to be ");
  
  for(int i = 0; i < NumPWMPins; i++) {
    pinMode(PWMPins[i], OUTPUT);
    
    // high = off, so start high
    //analogWrite(PWMPins[i], 255);

    if(i != 0) printAlways(", ");
    printAlways(PWMPins[i]);
  }
  
  printAlways(".\n");
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
