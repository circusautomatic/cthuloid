#include <SC.h>
#include <PrintLevel.h>

template<const char *const Name, class T, T & Property, T Min, T Max> 
void cmdSet() {
  if(char *arg = 0){//CmdMgr.next()) { 
    /*if(CmdMgr.next()) {
      printlnError("Error: takes 1 argument");
      return;
    }*/

    char *end;
    long v = strtol(arg, &end, 10);
    if(*end != '\0' || v < Min || v > Max) {
      printlnError("Error: argument out of range");
      return;
    }
    
    Property = v;
  }
  
  printAck(Name);
  printAck(": ");
  printlnAck(Property);
}

template<const char *const Name, double & Property, double Min, double Max> 
void cmdSet() {
  //use strtod
}

#define MAKE_NAME_VAR(var, name) extern const char Name_ ## var [] = name
#define MAKE_PROPERTY(Type, var, name, value)  Type var = value; MAKE_NAME_VAR(var, name)
#define MAKE_SET_CMD(Type, var, min, max) cmdSet<Name_ ## var, Type, var, min, max>
#define CMD_ENTRY(Type, var, min, max)    {Name_ ## var, MAKE_SET_CMD(Type, var, min, max)}

MAKE_PROPERTY(int, gSpeed, "speed", 0);
//int gSpeed = 0;
//extern const char Name_gSpeed[] = "speed";

SerialCommand::Entry CommandsList[] = {
  {"speed",  cmdSet<Name_gSpeed, int, gSpeed, 1, 10>},
  {"speed",  MAKE_SET_CMD(int, gSpeed, 1, 10)},
  CMD_ENTRY(int, gSpeed, 1, 10),
  {NULL, NULL}
}
