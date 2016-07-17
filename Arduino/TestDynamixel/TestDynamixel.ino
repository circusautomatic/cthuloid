#include <ax12.h>
#include <BioloidController2.h>    // use the bug-fixed version 
#include <PrintLevel.h>
#include <SC.h>

const int NumServos = 32;
int FirstID = 1;
int Speed = 80;

int idFromIndex(int index) {
  return FirstID + index;
}

SerialCommand::Entry CommandsList[] = {
  {"r", cmdRead},
  {"s", cmdMove},
  {"p", cmdLoadPose},
  {"speed", cmdSpeed},
  {"relax", cmdRelax},
  {"first", cmdFirstID},
  {NULL, NULL}
};

SerialCommand CmdMgr(CommandsList, cmdUnrecognized);

void cmdUnrecognized(const char *cmd) {
  printlnError("unrecognized command");
}

void setSpeed(int speed) {
  Speed = speed;
  for(int i = 0; i < NumServos; i++) {
    ax12SetRegister2(idFromIndex(i), AX_GOAL_SPEED_L, speed);
    delay(20);
  }
}

void cmdSpeed() {
  int speed = Speed;
  
  if(char *arg = CmdMgr.next()) {
    char *end;
    speed = strtol(arg, &end, 10);
    if(*end != '\0' || speed < 1 || speed > 999) return;
  }
  
  setSpeed(speed);

  Serial.print("speed ");
  Serial.println(speed);  
}

void cmdFirstID() {
  int id = FirstID;
  
  if(char *arg = CmdMgr.next()) {
    char *end;
    id = strtol(arg, &end, 10);
    if(*end != '\0' || id < 1 || id > 128) return;
  }
  
  FirstID = id;
  setSpeed(Speed);

  Serial.print("first ID ");
  Serial.println(id);
}

void cmdRead() {
  Serial.print("servo positions: ");
  for(int i = 0; i < NumServos; i++) {
    int id = idFromIndex(i);
    int pos = ax12GetRegister(id,AX_PRESENT_POSITION_L,2);
    delay(25);
    
    //sif(pos == -1) printError(id);
    
    Serial.print(pos);
    Serial.print(' ');
  }
  Serial.print('\n');
}

void printError(int id) {
  int errorBit = ax12GetLastError();
      Serial.print("    Servo # ");
      Serial.print(id);
  
  
      Serial.print("     Error Bit:");
      Serial.println(errorBit);
      
      
      if(ERR_NONE & errorBit == 0)
      {
        Serial.println("          No Errors Found");
  
      }
      
      if(ERR_VOLTAGE & errorBit)
      {
        Serial.println("          Voltage Error");
  
      }
      
      if(ERR_ANGLE_LIMIT & errorBit)
      {
        Serial.println("          Angle Limit Error");
  
      }
      
      if(ERR_OVERHEATING & errorBit)
      {
        Serial.println("          Overheating Error");
  
      }
      
      if(ERR_RANGE & errorBit)
      {
        Serial.println("          Range Error");
  
      }
      
      if(ERR_CHECKSUM & errorBit)
      {
        Serial.println("          Checksum Error");
  
      }
      
      if(ERR_OVERLOAD & errorBit)
      {
        Serial.println("          Overload Error");
  
      }
      
      
      if(ERR_INSTRUCTION & errorBit)
      {
        Serial.println("          Instruction Error");
  
      }
}

void move(int pose_[], int poseSize) {    
//  setSpeed(Speed);

  /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
  // hack in microcontroller for now:
  // invert movement of servo 28
  {
    int id = 28 - FirstID;
    if(id > 0 && poseSize > id) pose_[id] = 1024 - pose_[id];
  }
  
  // ignore position 0
  int count = 0;
  for(int i = 0; i < poseSize; i++) {
    if(pose_[i] > 0) count++;
  }

  int temp;
  int length = 4 + (count * 3);   // 3 = id + pos(2byte)
  int checksum = 254 + length + AX_SYNC_WRITE + 2 + AX_GOAL_POSITION_L;
  setTXall();
  ax12write(0xFF);
  ax12write(0xFF);
  ax12write(0xFE);
  ax12write(length);
  ax12write(AX_SYNC_WRITE);
  ax12write(AX_GOAL_POSITION_L);
  ax12write(2);
  for(int i=0; i<poseSize; i++)
  {
      temp = pose_[i];
      if(temp <= 0) continue;
      
      int id = idFromIndex(i);
      
      checksum += (temp&0xff) + (temp>>8) + id;
      ax12write(id);
      ax12write(temp&0xff);
      ax12write(temp>>8);
  } 
  ax12write(0xff - (checksum % 256));
  setRX(0);
}

// Accept one of two types of arguments: either a list of angles starting from FirstID,
// or a list of id:angle pairs.
// We shall constrain the angle to 200 to 824, and assume and consider 0 a no-op.
void cmdMove() {
  // see what kind of arguments we have
  char *arg = CmdMgr.next();
  if(arg == NULL) return;

  // if the first argument doesn't have a colon, consider the arguments a
  // list of angles starting from FirstID
  if(strchr(arg, ':') == NULL) {  
    int poses[NumServos];
    int i;

    for(i = 0; i < NumServos; i++) {      
      char *end;  
      int angle = strtol(arg, &end, 10);
      if(*end != '\0' || angle < 200 || angle > 812) {
        Serial.println("Angles must be between 200 and 812");
        return;
      }
      
      poses[i] = angle;
      Serial.println(angle);
  
      arg = CmdMgr.next();
      if(arg == NULL) break;
    }
    
    move(poses, i);    
    Serial.print("Moving ");
    Serial.print(i);
    Serial.println(" servos.");
  }

  // arguments are index:angle pairs
  else {   
    const char *FormatErrorMsg = "Error: takes pairs in the form <ID>:<angle>";

    // array of angles, indexed by (ID - 1)
    // angle of 0 is noop
    const int maxAngles = 128;
    int angles[maxAngles];
    int count = 0, maxID = 0;
  
    for(int i = 0; i < maxAngles; i++) angles[i] = 0;
    
    do {
      char *end;

      char *sID = strtok(arg, ":");
      if(sID == NULL) {
        printlnError(FormatErrorMsg);
        return;
      }
      int id = strtol(sID, &end, 10);
      if(*end != '\0' || id < 1 || id > 127) {
        printlnError("Error: ID must be between 1 and 127");
        return;
      }
  
      char *sAngle = strtok(NULL, ":");
      if(sAngle == NULL) {
        printlnError(FormatErrorMsg);
        return;
      }
      //contrain from -90 to 90 degrees
      int angle = strtol(sAngle, &end, 10);
      if(*end != '\0' || angle < 200 || angle > 824) {
        printlnError("Error: angle must be between 200 and 824");
        return;
      }
      
      angles[id - 1] = angle;
      maxID = max(maxID, id);
      count++;
      
    } while(arg = CmdMgr.next());

    // maxID == array length used, because IDs start at 1
    // temporarily alter FirstID to be 1
    int prevFirstID = FirstID;
    FirstID = 1;
    move(angles, maxID);
    FirstID = prevFirstID;
    
    /*for(int i = 0; i < maxID; i++) {
      Serial.print(angles[i]);
      Serial.print(", ");
    }
    Serial.println("");*/
    
    Serial.print("Moving ");
    Serial.print(count);
    Serial.println(" servos.");
  }
}

int Positions[] = {490, 500, 512, 612, 712};
int NumPositions = sizeof(Positions) / sizeof(*Positions);

void loadPose(int index) {
  int pos = Positions[index];
  int poses[NumServos];
  for(int i = 0; i < NumServos; i++) poses[i] = pos;
  move(poses, NumServos);
  
  Serial.print("Moving servos to position: ");
  Serial.println(pos);
}

void cmdLoadPose() {
  
  if(char *arg = CmdMgr.next()) {
    int index = *arg - '1';
    if(index < 0 || index >= NumPositions) return;
    loadPose(index);
  }
}

void cmdRelax() {
  
  const int maxAngles = NumServos;
  int ids[maxAngles];
  int count = 0;
  
  while(char *arg = CmdMgr.next()) {
    if(count >= NumServos) {
      printlnError("Error: too many IDs");
      return;
    }
    
    char *end;
    int id = strtol(arg, &end, 10);
    if(*end != '\0' || id < 1 || id > 127) {
      printlnError("Error: ID must be between 1 and 127");
      return;
    }
    
    ids[count++] = id;
  }
  
  if(count == 0) {
    count = NumServos;
    for(int i = 0; i < NumServos; i++) {
      Relax(idFromIndex(i));
    }
  }
  else {
    for(int i = 0; i < count; i++) {
      Relax(ids[i]);
    }
  }
  
  printAck("Relaxed ");
  printAck(count);
  printlnAck(" Servos");
}

void setup() {
  ax12Init(1000000);
  Serial.begin(38400);
  Serial.println("Servo Test Sketch");
  
  setSpeed(Speed);
}

void loop() {
  CmdMgr.readSerial();

  /*setSpeed(Speed);
  delay(500);
  loadPose(0);
  
  setSpeed(Speed);
  delay(500);
  loadPose(4);*/
}
