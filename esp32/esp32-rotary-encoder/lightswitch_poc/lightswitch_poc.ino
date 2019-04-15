// KY-040 ...  ESP32
// CLK    ...  PIN 4
// DT     ...  PIN 2
// SW     ...  PIN 5
// +      ...  3.3V
// GND    ...  GND

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiMulti.h>

long int rotValue=0, swValue=0;
uint8_t state=0;

// 10.0.0.30 1337
// 10.0.0.31 1337

WiFiClient client;
bool connected, pressed, onOrOff;
WiFiMulti wifi;

#define ROTARY_PINA 2
#define ROTARY_PINB 4
#define ROTARY_PINSW 5

portMUX_TYPE gpioMux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR isrAB() {
   uint8_t s = state & 3;

  portENTER_CRITICAL_ISR(&gpioMux);
    if (digitalRead(ROTARY_PINA)) s |= 4;
    if (digitalRead(ROTARY_PINB)) s |= 8;
    switch (s) {
      case 0: case 5: case 10: case 15:
        break;
      case 1: case 7: case 8: case 14:
        rotValue++; break;
      case 2: case 4: case 11: case 13:
        rotValue--; break;
      case 3: case 12:
        rotValue += 2; break;
      default:
        rotValue -= 2; break;
    }
    state = (s >> 2);
   portEXIT_CRITICAL_ISR(&gpioMux);
 
}


void IRAM_ATTR isrSWAll() {

 portENTER_CRITICAL_ISR(&gpioMux);
 swValue++;
 portEXIT_CRITICAL_ISR(&gpioMux);

 pressed = true;
}

void setup(){
  pinMode(ROTARY_PINA, INPUT_PULLUP);
  pinMode(ROTARY_PINB, INPUT_PULLUP);
  pinMode(ROTARY_PINSW, INPUT_PULLUP);

  attachInterrupt(ROTARY_PINA, isrAB, CHANGE);
  attachInterrupt(ROTARY_PINB, isrAB, CHANGE);
  attachInterrupt(ROTARY_PINSW, isrSWAll, CHANGE);
  Serial.begin(115200);

  wifi.addAP("ubitron", "superduper");

  Serial.println();
  Serial.println();
  Serial.print("Waiting for WiFi... ");

  while(wifi.run() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  
  connected = client.connect("10.0.0.63", 1337);

  onOrOff = false;
}


void loop(){
  Serial.print("isrSWAll ");
  Serial.print(swValue);
  Serial.print(" rotValue ");
  Serial.println(rotValue);

  if (pressed) {
    if (onOrOff) {
      Serial.print("RED\n");
      client.println("pwm2 1 0 10000 30000"); 
    } else {
      Serial.print("BLUE\n");
      client.println("pwm2 1 40000 10000 10000");       
    }
    
    pressed = false;
    onOrOff = ! onOrOff;
  }

  delay(1000);
}
