// Arduino sketch which outputs PWM for a set of channels based on serial input.


#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiClient.h>

const char* ssid = "touchametron";
const char* password = "superduper";

// TCP server at port 80 will respond to HTTP requests
WiFiServer server(1337);
const int timeout = 30;
// Serial commands accepted:
// - pwm <pwm1> <pwm2> ..., where <pwmN> is 0-65535 and N is up to NumChannels
// - pwm <index1>:<pwm1> <index2>:<pwm2> ..., where <indexN> is 1-based index into the PWMPins list
// - plevel <level>, change the amount of response text
//
// NOTE: initHRPWM and myHRWrite are set specifically to work on MEGAS. It could be tuned to work on
// unos.
#include <SC.h>
#include <PrintLevel.h>
#define INVERT_HIGH_AND_LOW
#define RED_MAX_PWM 45000
#define MAX_PWM 65535
//////////////////////////////////////////////////////////////////////////////////////
int freq = 480;
int res = 16;
int steps = 1;

int ledChannel = 0;
int ledChannel1 = 1;
int ledChannel2 = 2;
int ledChannel3 = 3;
int ledChannel4 = 4;
int ledChannel5 = 5;
//int ledChannel4 = 3;
void ledsetup() {
  ledcSetup(ledChannel, freq, res);
  ledcSetup(ledChannel1, freq, res);
  ledcSetup(ledChannel2, freq, res);
  ledcSetup(ledChannel3, freq, res);
  ledcSetup(ledChannel4, freq, res);
  ledcSetup(ledChannel5, freq, res);
//  ledcSetup(ledChannel3, freq, res);

// Pins that work 27,26,25 23,22,21 32,33,14 12,13,2 
  ledcAttachPin(32, ledChannel);
  ledcAttachPin(33, ledChannel1);
  ledcAttachPin(25, ledChannel2);
  ledcAttachPin(26, ledChannel3);
  ledcAttachPin(27, ledChannel4);
  ledcAttachPin(14, ledChannel5);

}

const int PWMPins[] = {32, 33, 25, 26, 27, 14};
const int NumPWMPins = sizeof(PWMPins) / sizeof(*PWMPins);
// this flag will invert PWM output (65535 - PWM), for active-low devices


const char *MsgPWMTupleFormatError = "Error: takes up to 6 arguments between 0 and 255";

/////////////////////////////////////////////////////////////////////////////////////////
// Command Manager and forward declarations for commands accessible from text interface
/////////////////////////////////////////////////////////////////////////////////////////
struct IDTuple {
  int id;
  long value;
};
int parseID(const char *arg);
int parseListOfIDs(int *outIDs, int maxIDs);
void cmdUnrecognized(const char *cmd);
void cmdPWMPins();
void cmdSetPrintLevel();
void cmdServo();

SerialCommand::Entry CommandsList[] = {
  {"plevel", cmdSetPrintLevel},
  {"pwm",    cmdPWMPins},
  {"s",      cmdServo},
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

void myHRWrite(int pin, unsigned value) {
  printAlways("setting pin to value: ");
  printAlways(pin);
  printAlways(" ");
  printlnAlways(value);

  switch (pin) {
    case 32: ledcWrite(ledChannel, value);  break;
    case 33: ledcWrite(ledChannel1, value);  break;
    case 25: ledcWrite(ledChannel2, value);  break;
    case 26: ledcWrite(ledChannel3, value);  break;
    case 27: ledcWrite(ledChannel4, value);  break;
    case 14: ledcWrite(ledChannel5, value);  break;
//    case 5:  ledcWrite(ledChannel4, value);  break;
    default: printlnError("invalid pin");
  }
}

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns 0 if there is a parse error or the ID is out of range.
int parseID(const char *arg) {
  char *end;
  int id = strtol(arg, &end, 10);

  if (*end != '\0' || id < 1 || id > 253) {
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

  if (*end != '\0' || v < 0 || v > maxPWM) {
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
  const char *SetPWMUsageMsg = "Error: takes up to 6 arguments between 0 and 65535 (except argument 3's max is 45000).";

  long channelValues[NumPWMPins];
  int count = 0;

  char *arg = CmdMgr.next();
  if (arg == NULL) {
    printlnError("Error: no arguments");
    return;
  }

  do {
    int index;
    long value;

    if (count >= NumPWMPins) {
      printlnError(SetPWMUsageMsg);
      return;
    }

    char *end;
    index = count;
    value = parsePWM(arg, count % 3 == 0 ? RED_MAX_PWM : MAX_PWM);
    if (value < 0) {
      printlnError(SetPWMUsageMsg);
      return;
    }

    printInfo("Set pin ");
    printInfo(PWMPins[index]);
    printInfo(" to ");
    printlnInfo(value);
    channelValues[index] = value;
    count++;
  } while (arg = CmdMgr.next());

  for (int i = 0; i < count; i++) {
    unsigned long c = channelValues[i];
    //analogWrite(PWMPins[i], invertPWM(c));
    printlnAlways(c);
    myHRWrite(PWMPins[i], invertPWM(c));
  }

  printAck("OK set ");
  printAck(count);
  printlnAck(" pins");
}

void cmdSetPrintLevel() {
  if (char *arg = CmdMgr.next()) {
    if (CmdMgr.next()) {
      printlnAlways("Error: takes 0 or 1 arguments");
      return;
    }

    if (!PrintLevel::set(arg)) {
      PrintLevel::printErrorString();
      return;
    }
  }

  printAck("print level ");
  printlnAck(PrintLevel::toString());
}

void cmdServo() {
  Serial.print("Got Servo shit");

}

///////////////////////////////////////////////////////////////////////////////////////////////////////////
// setup & loop
///////////////////////////////////////////////////////////////////////////////////////////////////////////

void setup() {
  ledsetup();
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.println("");

  // Wait for connection
  int i = 0;

  while (WiFi.status() != WL_CONNECTED ) {
    if (i < timeout) {
      delay(500);
      Serial.print(".");
      i++;
    }
    else {
      Serial.println(" ");
      break;
    }
  }
  if (WiFi.status() == WL_CONNECTED ) {
    Serial.println("");
    Serial.print("Connected to ");
    Serial.println(ssid);
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());

    // Set up mDNS responder:
    // - first argument is the domain name, in this example
    //   the fully-qualified domain name is "esp8266.local"
    // - second argument is the IP address to advertise
    //   we send our IP address on the WiFi network
    if (!MDNS.begin("esp32")) {
      Serial.println("Error setting up MDNS responder!");
      while (1) {
        delay(1000);
      }
    }
    Serial.println("mDNS responder started");

    // Start TCP (HTTP) server
    server.begin();
    Serial.println("TCP server started");

    // Add service to MDNS-SD
    MDNS.addService("telnet", "tcp", 23);
  }
  Serial.println("Initial LED Setup");
}

void loop() {
  CmdMgr.readSerial();
  WiFiClient client = server.available();
  if (client) {                             // if you get a client,
    Serial.println("New Client.");           // print a message out the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        CmdMgr.handleChar(c);
        Serial.write(c);  // print it out the serial monitor
      }
    }
  }
}



