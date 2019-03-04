// Arduino sketch which outputs PWM for a set of channels based on serial input.


#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiClient.h>
#include "/Users/jmzorko/work/circusautomatic/hardware/espressif/esp32/tools/sdk/include/soc/soc/rtc.h"
//#include "/home/fleeky/Arduino/hardware/espressif/esp32/tools/sdk/include/freertos/freertos/task.h"

const char* ssid = "ubitron";
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
#define RED_MAX_PWM 65534
#define MAX_PWM 65534

constexpr int NumPeriods = 3;     // number of steps in fade
constexpr int PeriodLength = 1;   // sleep for this many ms

//////////////////////////////////////////////////////////////////////////////////////
int freq = 20000;
int res = 16;
int steps = 1;
int defaultlight = 4000;
int maxfreq = 40000;


int ledChannel = 0;
int ledChannel1 = 1;
int ledChannel2 = 2;
int ledChannel3 = 3;
int ledChannel4 = 4;
int ledChannel5 = 5;
int ledChannel6 = 6;
int ledChannel7 = 7;
int ledChannel8 = 8;
int ledChannel9 = 9;
int ledChannel10 = 10;
int ledChannel11 = 11;

const int PWMPins[] = {32, 33, 25, 26, 27, 14, 12, 13, 2, 23, 22, 21};
const int NumPWMPins = sizeof(PWMPins) / sizeof(*PWMPins);
int PinCurrentValues[NumPWMPins] = {0};

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
void cmdSetFrequency();
void cmdPWMPins();
void cmdPWMPins2();
void cmdSetPrintLevel();
void cmdServo();

SerialCommand::Entry CommandsList[] = {
  {"plevel", cmdSetPrintLevel},
  {"freq",   cmdSetFrequency},
  {"pwm",    cmdPWMPins},
  {"pwm2",   cmdPWMPins2},
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
  //printAlways("setting pin to value: ");
  //printAlways(pin);
  //printAlways(" ");
  //printlnAlways(value);
  value = invertPWM(value);

  switch (pin) {
    case 32: ledcWrite(ledChannel, value);  break;
    case 33: ledcWrite(ledChannel1, value);  break;
    case 25: ledcWrite(ledChannel2, value);  break;
    case 26: ledcWrite(ledChannel3, value);  break;
    case 27: ledcWrite(ledChannel4, value);  break;
    case 14: ledcWrite(ledChannel5, value);  break;
    case 12: ledcWrite(ledChannel6, value);  break;
    case 13: ledcWrite(ledChannel7, value);  break;
    case 2: ledcWrite(ledChannel8, value);  break;
    case 23: ledcWrite(ledChannel9, value);  break;
    case 22: ledcWrite(ledChannel10, value);  break;
    case 21: ledcWrite(ledChannel11, value);  break;
    default: printlnError("invalid pin");
  }
}

void updateFrequency() {
  ledcSetup(ledChannel, freq, res);
  ledcAttachPin(32, ledChannel);
  myHRWrite(PWMPins[0], 0);
  
  ledcSetup(ledChannel1, freq, res);
  ledcAttachPin(33, ledChannel);
  myHRWrite(PWMPins[1], 0);
  
  ledcSetup(ledChannel2, freq, res);
  ledcAttachPin(25, ledChannel);
  myHRWrite(PWMPins[2], 0);
  
  ledcSetup(ledChannel3, freq, res);
  ledcSetup(ledChannel4, freq, res);
  ledcSetup(ledChannel5, freq, res);
  ledcSetup(ledChannel6, freq, res);
  ledcSetup(ledChannel7, freq, res);
  ledcSetup(ledChannel8, freq, res);
  ledcSetup(ledChannel9, freq, res);
  ledcSetup(ledChannel10, freq, res);
  ledcSetup(ledChannel11, freq, res);

  ledcAttachPin(32, ledChannel);
  ledcAttachPin(33, ledChannel1);
  ledcAttachPin(25, ledChannel2);
  ledcAttachPin(26, ledChannel3);
  ledcAttachPin(27, ledChannel4);
  ledcAttachPin(14, ledChannel5);
  ledcAttachPin(12, ledChannel6);
  ledcAttachPin(13, ledChannel7);
  ledcAttachPin(2, ledChannel8);
  ledcAttachPin(23, ledChannel9);
  ledcAttachPin(22, ledChannel10);
  ledcAttachPin(21, ledChannel11);
}

void ledsetup() {
  updateFrequency();

// Pins that work 27,26,25 23,22,21 32,33,14 12,13,2 
  

  //for(uint8_t i=0; i < 12; i++)
  // ledcWrite(channel, dutycycle)
  // For 8-bit resolution duty cycle is 0 - 255
//  ledcWrite(ledChannel, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel1, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel2, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel3, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel4, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel5, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel6, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel7, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel8, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel9, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel10, 0);  // test high output of all leds in sequence
//  ledcWrite(ledChannel11, 0);  // test high output of all leds in sequence
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

// if no argument, prints the frequency
// if one argument, sets the frequency and then prints it
void cmdSetFrequency() {
  if(char *arg = CmdMgr.next()) {
    if(CmdMgr.next()) {
      printlnError("Error: takes 0 or 1 arguments");
      return;
    }

    char *end;
    double v = strtod(arg, &end);

    if(*end != '\0' || v < 1 || v > maxfreq) {
      printlnError("Error: speed is in angle-units per second; between 1 and 1000");
      return;
    }
    
    freq = round(v);
  }
  
  updateFrequency();
  printAck("frequency: ");
  printlnAck(freq);
}

void cmdPWMPins2() {
  const char *SetPWM2UsageMsg = "Error: takes up to 13 arguments between 0 and 65535 (except argument 3's max is 45000).";

  long channelValues[NumPWMPins];
  int count = 0;

  char *arg = CmdMgr.next();
  if (arg == NULL) {
    printlnError("Error: no arguments");
    return;
  }

  long numPeriods = parsePWM(arg, 100);
  arg = CmdMgr.next();
  long periodLength = parsePWM(arg, 100);
  arg = CmdMgr.next();
      
  do {
    int index;
    long value;

    if (count >= NumPWMPins) {
      printlnError(SetPWM2UsageMsg);
      return;
    }

    char *end;
    index = count;
    value = parsePWM(arg, count % 3 == 2 ? RED_MAX_PWM : MAX_PWM);
    if (value < 0) {
      printlnError(SetPWM2UsageMsg);
//      value = 4000;
      return;
    }

    //printInfo("Set pin ");
    //printInfo(PWMPins[index]);
    //printInfo(" to ");
    //printlnInfo(value);
    channelValues[index] = value;
    count++;
  } while (arg = CmdMgr.next());

  // interpolate over a period of time
  const TickType_t xDelay = periodLength / portTICK_PERIOD_MS;

  float frameDelay = 9.14;   // 9.14ms - length of time between frames at 60fps

  long beginTime = micros();
  long endTime = beginTime + 9140;

  for (long period = 1; period < 1+numPeriods; period++) {
    //long beginTime = millis();
    float fraction = period / (float)numPeriods;
    for (int i = 0; i < count; i++) {
      unsigned long v = PinCurrentValues[i] + (channelValues[i] - PinCurrentValues[i]) * fraction;
      //printlnAlways(v);
      myHRWrite(PWMPins[i], v);
    }
    //long endTime = millis();
    //printlnAlways(endTime - beginTime);
    //vTaskDelay(xDelay); 
  }

  for (int i = 0; i < count; i++) {
    unsigned long v = channelValues[i];
    PinCurrentValues[i] = v;
    myHRWrite(PWMPins[i], v);
  }
  
  //printAck("OK set ");
  //printAck(count);
  //printlnAck(" pins");
}

// expects space-delimited ints 0-65535, or space delimited <index>:<pwm> pairs
void cmdPWMPins() {
  const char *SetPWMUsageMsg = "Error: takes up to 12 arguments between 0 and 65535 (except argument 3's max is 45000).";

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
    value = parsePWM(arg, count % 3 == 2 ? RED_MAX_PWM : MAX_PWM);
    if (value < 0) {
      printlnError(SetPWMUsageMsg);
//      value = 4000;
      return;
    }

    printInfo("Set pin ");
    printInfo(PWMPins[index]);
    printInfo(" to ");
    printlnInfo(value);
    channelValues[index] = value;
    count++;
  } while (arg = CmdMgr.next());

  // interpolate over a period of time
  const TickType_t xDelay = PeriodLength / portTICK_PERIOD_MS;

  for (int period = 1; period < 1+NumPeriods; period++) {
    float fraction = period / (float)NumPeriods;
    for (int i = 0; i < count; i++) {
      unsigned long v = PinCurrentValues[i] + (channelValues[i] - PinCurrentValues[i]) * fraction;
      //printlnAlways(v);
      myHRWrite(PWMPins[i], v);
    }
    //vTaskDelay(xDelay); 
  }

  for (int i = 0; i < count; i++) {
    unsigned long v = channelValues[i];
    PinCurrentValues[i] = v;
    myHRWrite(PWMPins[i], v);
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
  rtc_clk_cpu_freq_set(RTC_CPU_FREQ_240M);
  ledsetup();
  for (int i=0; i < NumPWMPins; i++){
    myHRWrite(PWMPins[i], 0);
    PinCurrentValues[i] = 0;
    delay(10);
  }
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

WiFiClient LastClient;

void loop() {
  CmdMgr.readSerial();
  if (WiFiClient newClient = server.available()) {
      Serial.println("New Client.");
      LastClient = newClient;
  }

  if (LastClient && LastClient.connected()) {
      while (LastClient.available()) {
        char c = LastClient.read();             // read a byte, then
        CmdMgr.handleChar(c);
        Serial.write(c);  // print it out the serial monitor
      }
    }
}
