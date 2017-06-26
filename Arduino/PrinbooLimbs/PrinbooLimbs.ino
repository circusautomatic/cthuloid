#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <SC.h>
#include <PrintLevel.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
// you can also call it with a different address you want
//Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x41);

// Depending on your servo make, the pulse width min and max may vary, you 
// want these to be as small/large as possible without hitting the hard stop
// for max range. You'll have to tweak them as necessary to match the servos you
// have!
#define SERVO_MIN_PULSE 150 // this is the 'minimum' pulse length count (out of 4096)
#define SERVO_MAX_PULSE 560 // this is the 'maximum' pulse length count (out of 4096)
#define SERVO_MAX_ANGLE 180

//angle for each servo in degrees
volatile int16_t servoAngles[] =   {
  90, 90, 180,         // neck turn, neck nod, face twist
  0, 0, 0, 90,         // left shoulder, upperarm, forearm, hand
  180, 180, 180, 90    // right shoulder, upperarm, forearm, hand
};
const int NumServos = sizeof(servoAngles) / sizeof(servoAngles[0]);

int16_t idFromIndex(int16_t index) {
  if(index < 0 || index > NumServos) return -1;
  return index + 1;
}

int16_t indexFromId(int16_t id) {
  int16_t index = id - 1;
  if(index < 0 || index > NumServos) return -1;
  return index;
}

// retrieve servo angle
int16_t getServo(int16_t id) {
  int16_t index = indexFromId(id);
  if(index == -1) return -1;
  return servoAngles[index];
}

// tell servo to move to angle in servoAngles
bool moveServo(int16_t id) {
  int16_t i = indexFromId(id);
  if(i == -1) return false;
  uint16_t pulselen = map(servoAngles[i], 0, SERVO_MAX_ANGLE, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  pwm.setPWM(i, 0, pulselen);
  return true;
}

// change servoAngle and move the servo
bool setAndMoveServo(int16_t id, int16_t angle) {
  int16_t index = indexFromId(id);
  if(index == -1 || angle < 0 || angle > SERVO_MAX_ANGLE) return false;
  servoAngles[index] = angle;
  return moveServo(id);
}

const char *MsgPositionTupleFormatError = "Error: takes pairs in the form <ID>:<angle>";
const char *MsgPWMTupleFormatError = "Error: takes pairs in the form <index>:<PWM>";

/////////////////////////////////////////////////////////////////////////////////////////
// Command Manager and forward declarations for commands accessible from text interface
/////////////////////////////////////////////////////////////////////////////////////////

struct IDTuple { int id; long value; };

int parseID(const char *arg);
int parseAngle(const char *arg, int minAngle = 0, int maxAngle = 180);
boolean parsePositionTuple(char *s, IDTuple *out);
int parseListOfIDs(int *outIDs, int maxIDs);

void cmdUnrecognized(const char *cmd);
void readServoPositions();
void cmdSetPrintLevel();
void cmdLoadPose();
void cmdMoveServos();

static const SerialCommand::Entry CommandsList[] = {
  {"plevel",  cmdSetPrintLevel},
  {"r",       readServoPositions},
  {"s",       cmdMoveServos},
  {NULL,      NULL}
};

SerialCommand CmdMgr(CommandsList, cmdUnrecognized);


/////////////////////////////////////////////////////////////////////////////////////////////
// helpers
/////////////////////////////////////////////////////////////////////////////////////////////
/*
// Converts string to double; returns true if successful.
// Returns false if str contains any inappropriate characters, including whitespace.
// See strtod for accepted number formats.
boolean toDouble(const char *str, double *result) {
  char *end;
  if(*str == ' ') return false;
  *result = strtod(str, &end);

  // if end == str, str is empty or begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

// Converts string to long; returns true if successful.
// Returns false if str contains any characters other than numbers or a negative sign.
boolean toLong(const char *str, long *result) {
  char *end;
  //if(*str == ' ') return false;
  *result = strtol(str, &end, 10);
  
  // if end == str, str is empty or begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}

// converts string to int; returns true if successful
// Returns false if str contains any characters other than numbers or a negative sign.
boolean toInt(const char *str, int *result) {
  char *end;
  //if(*str == ' ') return false;
  long r = strtol(str, &end, 10);
  
  // TODO check if out of int range
  //if((unsigned long)r >> (8*sizeof(*result))) return false;
  *result = r;
  
  // if end == str, str is empty or begins with an erroneous character
  // if end does not point at a null-terminator, the string contained errorneous characters
  return end != str && *end == '\0';
}
*/

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns 0 if there is a parse error or the ID is out of range.
int parseID(const char *arg) {
  char *end;
  int id = strtol(arg, &end, 10);

  if(*end != '\0' || id < 1 || id > NumServos) {
      printError("Error: ID must be between 1 and ");
      printlnError(NumServos);
      return 0;
  }
  
  return id;
}

// Takes a string of an integer (numeric chars only). Returns the integer on success.
// Prints error and returns -1 if there is a parse error or the angle is out of range.
int parseAngle(const char *arg, int minAngle, int maxAngle) {
  char *end;
  int angle = strtol(arg, &end, 10);
  
  if(*end != '\0' || angle < minAngle || angle > maxAngle) {
    printError("Error: angle must be between ");
    printError(minAngle);
    printError(" and ");
    printlnError(maxAngle);
    return -1;
  }
  
  return angle;
}

// parse a list of IDs from CmdMgr into an array
// returns -1 on error
int parseListOfIDs(int *outIDs, int maxIDs) {
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= maxIDs) {
      printlnError("Error: too many IDs");
      return -1;
    }
    
    int id = parseID(arg);
    if(id == 0) return -1;
    outIDs[count++] = id;
  }
  
  return count;
}

// convert "<id>:<angle>" into 2 integers in a struct
// returns false on error
boolean parsePositionTuple(char *s, IDTuple *out) {
  char *sID = strtok(s, ":");
  if(sID == NULL) {
    printlnError(MsgPositionTupleFormatError);
    return false;
  }
  
  int id = parseID(sID);
  if(id == 0) return false;

  char *sAngle = strtok(NULL, ":");
  if(sAngle == NULL) {
    printlnError(MsgPositionTupleFormatError);
    return false;
  }
  
  int angle = parseAngle(sAngle);
  if(angle == -1) return false;
  
  out->id = id;
  out->value = angle;
  return true;
}

// you can use this function if you'd like to set the pulse length in seconds
// e.g. setServoPulse(0, 0.001) is a ~1 millisecond pulse width. it's not precise!
void setServoPulse(uint8_t n, double pulse) {
  double pulselength;
  
  pulselength = 1000000;   // 1,000,000 us per second
  pulselength /= 60;   // 60 Hz
  pulselength /= 4096;  // 12 bits of resolution
  pulse *= 1000;
  pulse /= pulselength;
  pwm.setPWM(n, 0, pulse);
}

//////////////////////////////////////////////////////////////////////////////////
// commands accessible from text interface

void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

void readServoPositions() {
  printAck("Servo Readings: ");
  /*printlnAck(NumServos);
  
  //Servos.readPose();

  /*for(int i = 0; i < NumServos; i++) {
    int id = idFromIndex(i);
    int pos = getServo(id);
    //Serial.println(pos);
    
    // print key:value pairs space delimited, but column-aligned
    char buf[16];
    int ixEnd = sprintf(buf, "ID:%d", id);
    while(ixEnd < 5) buf[ixEnd++] = ' ';
    buf[ixEnd] = '\0';

    printInfo(buf);
    printInfo(" pos:");
    printlnInfo(pos);
  }*/

  // python dictionary notation;
  // allocate 3 for {}\0, and 8 for each pos, though (4 + comma) should be max digits
  char dictBuf[3 + NumServos * (3+1+4+1)] = "{}";
  int ix = 1;

  for(int i = 0; i < NumServos; i++) {
    int id = idFromIndex(i);
    int pos = getServo(id);
    if(pos < 0 || pos > 1024) continue;

    ix += sprintf(dictBuf+ix, "%d:%d,", id, pos);
  }
  
  if(ix > 1) dictBuf[ix - 1] = '}';    //overwrite the final comma
  printlnAlways(dictBuf);
}

// arguments are index:angle pairs
void cmdMoveServos() {
  //broadcastSpeed();    // servos can forget their speed, or may have reset since we booted
  
  IDTuple tuple;
  int count = 0;
  
  char *arg = CmdMgr.next();
   if(arg == NULL) {
     printlnError("Error: no arguments");
     return;
   }

   // see what kind of arguments we have
   do {
    if(count >= NumServos) {
      printlnError("Too many arguments");
      return;
    }

    if(parsePositionTuple(arg, &tuple) == false) return;
    count++;
    
    setAndMoveServo(tuple.id, tuple.value);
  } while(arg = CmdMgr.next());
  
  Serial.print("Moving ");
  Serial.print(count);
  Serial.println(" servos");
}

// changes the amount of response text; see PrintLevel.h
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
  
  printAlways("print level ");
  printlnAlways(PrintLevel::toString());
}

void setup() {
  Serial.begin(38400);

  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
  
  for(int i = 0; i < NumServos; i++) moveServo(i);
  
  Serial.println("Cardbot Servos activated.");
  readServoPositions();
}

void loop() {  
  CmdMgr.readSerial();
  
  /*if (Serial.available())
  {
    char b = Serial.read();
    //Serial.print("I got: ");
    //Serial.println(b);
    
    // keyboard numbers 1-9 determine which servo we're talking to
    // '1' addresses index 0, etc.
    if (b >= '1' && b <= '9') {
      servonum = b - '1';
      Serial.print("Servo #");
      Serial.println(b);
    }
    
    // otherwise increment/decrement the servo position
    else {
      if (b == '-') servoAngles[servonum] -= degreeInc;
      else if (b == '=') servoAngles[servonum] += degreeInc;
      else return;

      // ensure we didn't go out of bounds
      if (servoAngles[servonum] < 0) {
        servoAngles[servonum] = 0;
        Serial.println("At movement limit");
      }
      if (servoAngles[servonum] > 180) {
        servoAngles[servonum] = 180;
        Serial.println("At movement limit");
      }
      
      Serial.print("Angle in degrees: ");
      Serial.println(servoAngles[servonum]);
      
      uint16_t pulselen = map(servoAngles[servonum], 0, 180, SERVOMIN, SERVOMAX);
      pwm.setPWM(servonum, 0, pulselen);
    }
  }*/
}
