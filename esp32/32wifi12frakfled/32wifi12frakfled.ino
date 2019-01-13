// Arduino sketch which outputs PWM for a set of channels based on serial input.


#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiClient.h>
#include <FastLED.h>
#include <SC.h>
#include <PrintLevel.h>

// How many leds are in the strip?
#define NUM_LEDS 18

// Data pin that led data will be written out over
#define DATA_PIN 27

// This is an array of leds.  One item for each led in your strip.
CRGB leds[NUM_LEDS];

//Max RGB value
#define MAX_RGB 255

//Initial Values for CMDSetColor
int id = 0;
int ledr = 0;
int ledg = 0;
int ledb = 0;
int numr = 0;
int numg = 0;
int numb = 0;

//Values for individiaul rgb setting
const int rows = 18;
const int cols = 3;
//int carray[ rows ][ cols ] = {};

int colorSetBlock[] = {0, 0, 0};
const int numColors = 3;


//WIFI PASS
const char* ssid = "touchametron";
const char* password = "superduper";

// TCP server at port 80 will respond to HTTP requests
WiFiServer server(1337);
const int timeout = 30;

/////////////////////////////////////////////////////////////////////////////////////////
// Command Manager and forward declarations for commands accessible from text interface
/////////////////////////////////////////////////////////////////////////////////////////

void cmdUnrecognized(const char *cmd);
void cmdRed();
void cmdBlue();
void cmdGreen();
void cmdAmber();
void cmdBlack();
void cmdMultiColor();
void cmdMultiMultiColor();
void cmdSetColor();
void cmdSetInd();
//void cmdSetIndHelper();

SerialCommand::Entry CommandsList[] = {
  {"red",       cmdRed},
  {"blue",      cmdBlue},
  {"green",     cmdGreen},
  {"amber",     cmdAmber},
  {"black",     cmdBlack},
  {"m",     cmdMultiColor},
  {"mm",     cmdMultiMultiColor},
  {"c",      cmdSetColor},
  {"i",      cmdSetInd},
//  {"test",  cmdSetIndHelper},
  {NULL,     NULL}
};
SerialCommand CmdMgr(CommandsList, cmdUnrecognized);


/////////////////////////////////////////////////////////////////////////////////////////////
// helpers
/////////////////////////////////////////////////////////////////////////////////////////////

void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

void cmdRed() {
  // Turn the LED red
  fill_solid( leds, NUM_LEDS, CRGB(255, 0, 0));
  FastLED.show();
  //  delay(30);

}

void cmdBlue() {
  // Turn the LED blue
  fill_solid( leds, NUM_LEDS, CRGB(0, 0, 255));
  FastLED.show();
  //  delay(30);
}

void cmdGreen() {
  // Turn the LED green
  fill_solid( leds, NUM_LEDS, CRGB(0, 255, 0));
  FastLED.show();
  //  delay(30);
}

void cmdBlack() {
  // Turn the LED off
  fill_solid( leds, NUM_LEDS, CRGB(0, 0, 0));
  FastLED.show();
  //  delay(30);
}

void cmdAmber() {
  // Turn the LED amber
  fill_solid( leds, NUM_LEDS, CRGB(178, 68, 0));
  FastLED.show();
  //  delay(30);
}

void cmdMultiMultiColor() {
  int index = 0;
  while (1) {
    char *larg = CmdMgr.next();
    if (larg == NULL) {
      printlnError("Error: no id arguments");
      break;
    }
    else {
      index = atoi(larg);
    }
    char *larg1 = CmdMgr.next();
    if (larg1 == NULL) {
      printlnError("Error: no red arguments");
    }
    else {
      ledr = atoi(larg1);
    }
    char *larg2 = CmdMgr.next();
    if (larg2 == NULL) {
      printlnError("Error: no green arguments");
    }
    else {
      ledg = atoi(larg2);
    }
    char *larg3 = CmdMgr.next();
    if (larg3 == NULL) {
      printlnError("Error: no blue arguments");
    }
    else {
      ledb = atoi(larg3);
    }
    leds[index].setRGB( ledr, ledg, ledb);
    FastLED.show();
  }
}

void cmdMultiColor() {
  char *larg = CmdMgr.next();
  if (larg == NULL) {
    printlnError("Error: no id arguments");
  }
  else {
    id = atoi(larg);
  }
  char *larg1 = CmdMgr.next();
  if (larg1 == NULL) {
    printlnError("Error: no red arguments");
  }
  else {
    ledr = atoi(larg1);
  }
  char *larg2 = CmdMgr.next();
  if (larg2 == NULL) {
    printlnError("Error: no green arguments");
  }
  else {
    ledg = atoi(larg2);
  }
  char *larg3 = CmdMgr.next();
  if (larg3 == NULL) {
    printlnError("Error: no blue arguments");
  }
  else {
    ledb = atoi(larg3);
  }
  leds[id].setRGB( ledr, ledg, ledb);
  FastLED.show();
  //  delay(30);
}

void cmdSetColor() {
  char *arg = CmdMgr.next();
  if (arg == NULL) {
    printlnError("Error: no red arguments");
  }
  else {
    numr = atoi(arg);
  }
  char *arg1 = CmdMgr.next();
  if (arg1 == NULL) {
    printlnError("Error: no green arguments");
  }
  else {
    numg = atoi(arg1);
  }
  char *arg2 = CmdMgr.next();
  if (arg2 == NULL) {
    printlnError("Error: no blue arguments");
  }
  else {
    numb = atoi(arg2);
  }
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    leds[i].setRGB(numr, numg, numb);
  }
  FastLED.show();
  Serial.println(numb);
  Serial.println(numg);
  Serial.println(numr);
  return;
}

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns -1 if there is a parse error or the PWM value is out of range.
long parseRGB(const char *arg, long maxRGB) {
  char *end;
  long v = strtol(arg, &end, 10);
  
  if (*end != '\0' || v < 0 || v > maxRGB) {
    printlnError("Error: RGB value must be between 0 and ");
    printlnError(maxRGB);
    return -1;
  }

  return v;
}
void cmdSetInd() {
   int count = 0;
   char *arg = CmdMgr.next();
   if (arg == NULL) {
     printlnError("you missed something");
   }
   for ( int i = 0; i < NUM_LEDS; i++ ) {
      // loop through columns of current row
      for ( int j = 0; j < 3; j++ ){
          leds[i][j] = parseRGB(arg, MAX_RGB);//need j here
          char *arg = CmdMgr.next();
          break;
//          leds[i][1] = parseRGB(arg, MAX_RGB);
//          leds[i][2] = parseRGB(arg, MAX_RGB);
      //leds[i].b = arg[arg%3=0] basically you want every 3rd argument to be here and then for it to restart at 0, so try and find the math that accomplishes that.
      } 
   }
   FastLED.show();
  }
//}

//// void cmdSetIndHelper(int & r[], int & g[], int & b[], int r_sz, int g_sz, int b_sz, int n){
//  int rx = 0;
//  int gx =0;
//  int bx = 0;
//  
//  for (int i=0; i < r_sz; i+n){
//    r[rx++]=r[i];
//    printlnError(i);
//    }
//  for (int i=1; i < g_sz; i+n){
//    g[gx++]=g[i];
//    printlnError(i);
//    }
//  for (int i=2; i < b_sz; i+n){
//    b[bx++]=b[i];
//    printlnError(i);
//    }
//  
//}
//
//void cmdTest() {
//  cmdSetIndHelper();
//}


///////////////////////////////////////////////////////////////////////////////////////////////////////////
// setup & loop
///////////////////////////////////////////////////////////////////////////////////////////////////////////

void setup() {
  FastLED.addLeds<WS2812, DATA_PIN, GRB>(leds, NUM_LEDS);
  fill_solid( leds, NUM_LEDS, CRGB(0, 0, 0));
  FastLED.show();
  delay(10);
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.println("");

  //  cmdPWMPins();



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
    MDNS.addService("telnet", "tcp", 1337);
  }
  Serial.println("Done setting up");
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
