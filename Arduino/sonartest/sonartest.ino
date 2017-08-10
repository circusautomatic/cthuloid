#include <NewPing.h>
 
#define TRIGGER_PIN  4
#define ECHO_PIN     2
#define MAX_DISTANCE 100  //centimeters
 
NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE);
 
void setup() {
  Serial.begin(115200);
}
 
void loop() {
  delay(50);
  Serial.print("Ping: ");
  Serial.print(sonar.ping_cm());
  Serial.println("cm");
}
