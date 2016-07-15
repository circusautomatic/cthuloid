// EEPROM convenience functions
#include <avr/eeprom.h>

int memcpyToEEPROM(int location, const void *data, int byteCount) {
  const char *p = (const char*)data;
  unsigned char *address = (unsigned char*)location;
  for(int i = 0; i < byteCount; i++) eeprom_write_byte(address+i, p[i]);
  return byteCount;
}

int strcpyToEEPROM(int location, const char *s) {
  unsigned char *address = (unsigned char*)location;
  int i;
  for(i = 0; s[i] != '\0'; i++) eeprom_write_byte(address+i, s[i]);
  eeprom_write_byte(address+i, '\0');
  return i;
}

int memcpyFromEEPROM(int location, void *data, int byteCount) {
  char *p = (char*)data;
  unsigned char *address = (unsigned char*)location;
  for(int i = 0; i < byteCount; i++) p[i] = eeprom_read_byte(address+i);
  return byteCount;
}
