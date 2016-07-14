from serialthread import SerialThread
from ast import literal_eval
from console import getch

class UltrasonicSensor(SerialThread):
  def __init__(self, path, baud):
    SerialThread.__init__(self, path, baud)

  def handleLine(self, line):
    MAX_FLOOR_DISTANCE = 31
    MAX_FRONT_DISTANCE = 40
    def outOfRangeFloor(cm): return cm < 1 or cm > MAX_FLOOR_DISTANCE
    def outOfRangeFront(cm): return cm > 1 and cm < MAX_FRONT_DISTANCE
    
    shouldStop = False
    try:
      print(line)
      readings = literal_eval(line)
      print(readings)
      if outOfRangeFloor(readings[0]) or outOfRangeFloor(readings[1]):
        shouldStop = True
      if outOfRangeFront(readings[2]) or outOfRangeFront(readings[3]):
        shouldStop = True
    except SyntaxError:
      print('error interpreting sensor output as a dict')

    if shouldStop:
      print('STOP!')
      ucMotor.write(b' ')
 
ucSensors = UltrasonicSensor('/dev/ttyACM0', 38400)
ucMotor = SerialThread('/dev/ttyACM1', 38400)

while True:
  c = getch()
  if c == 'q' or c == 'Q': 
    ucSensors.exit()
    ucMotor.exit()
    break
  elif c == '=' or c == '+': ucMotor.write(b'LR')
  elif c == '-': ucMotor.write(b'lr')
  elif c == ' ': ucMotor.write(b' ') # immediate stop
  
