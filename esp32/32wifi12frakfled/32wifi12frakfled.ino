// Arduino sketch which outputs PWM for a set of channels based on serial input.


#include <WiFi.h>
#include <ESPmDNS.h>
#include <WiFiClient.h>
#include <FastLED.h>
#include <SC.h>
#include <PrintLevel.h>

// How many leds are in the strip?
#define NUM_LEDS 114

// Data pin that led data will be written out over
#define DATA_PIN 27

// This is an array of leds.  One item for each led in your strip.
CRGB leds[NUM_LEDS];

//Initial Values for CMDSetColor
int numr = 0;
int numg = 0;
int numb = 0;

int colorSetBlock[]={0,0,0};
const int numColors = 3;


//WIFI PASS
const char* ssid = "****";
const char* password = "****";

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
void cmdSetColor();

SerialCommand::Entry CommandsList[] = {
  {"red",       cmdRed},
  {"blue",      cmdBlue},
  {"green",     cmdGreen},
  {"amber",     cmdAmber},
  {"black",     cmdBlack},  
  {"multi",     cmdMultiColor},
  {"c",      cmdSetColor},
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

void cmdMultiColor() {
    // Turn the LED amber
  fill_solid( leds, NUM_LEDS, CRGB(0, 0, 255));
  fill_solid( leds, 9, CRGB(255, 0, 0));
  FastLED.show();
//  delay(30);
}
void cmdSetColor(){
  char *arg = CmdMgr.next();
  if (arg == NULL) {
    printlnError("Error: no red arguments");
    }
  else{
   numr = atoi(arg);
  }
  char *arg1 = CmdMgr.next();
  if (arg1 == NULL) {
    printlnError("Error: no green arguments");
    }
  else{
   numg = atoi(arg1);
  }
  char *arg2 = CmdMgr.next();
  if (arg2 == NULL) {
    printlnError("Error: no blue arguments");
    }
  else{
   numb = atoi(arg2);
  }  
  for(uint8_t i=0; i < NUM_LEDS; i++){
    fill_solid( leds, NUM_LEDS, CRGB(numr, numg, numb));
     }
  FastLED.show();
  printlnError(numb);
  printlnError(numg);
  printlnError(numr);
  return;
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////
// setup & loop
///////////////////////////////////////////////////////////////////////////////////////////////////////////

void setup() {
  FastLED.addLeds<WS2811, DATA_PIN, RGB>(leds, NUM_LEDS);
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



