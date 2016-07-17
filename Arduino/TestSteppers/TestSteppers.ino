
const int dirPins[] =  {4, 6};//, 8, 10};
const int stepPins[] = {5, 7};//, 9, 11};
boolean dirValues[] = {false, false, false, false};
const int numPins = sizeof stepPins / sizeof *stepPins;

void setup() { 
  Serial.begin(9600);

    pinMode(8, OUTPUT);     
    pinMode(9, OUTPUT);
    digitalWrite(8, LOW);
    digitalWrite(9, LOW);
  
  for(int i = 0; i < numPins; i++) {  
    pinMode(stepPins[i], OUTPUT);     
    pinMode(dirPins[i], OUTPUT);
    digitalWrite(stepPins[i], LOW);
    digitalWrite(dirPins[i], LOW);
  }
  
  randomSeed(0);
}

const int us = 100;

void loop() {

  for(int i = 0; i < numPins; i++) {
    if(random(128) == 0) {
      dirValues[i] = !dirValues[i];
      digitalWrite(dirPins[i], dirValues[i]? HIGH: LOW);
    }
  }
  //Serial.println("a");
  
  for(int i = 0; i < numPins; i++) digitalWrite(stepPins[i], HIGH);
  delayMicroseconds(us);
  
  for(int i = 0; i < numPins; i++) digitalWrite(stepPins[i], LOW); 
  //delay(us);
  delayMicroseconds(us);
}
  
