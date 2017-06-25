import socket, os, errno

motors = Motors()
limbs = Limbs()

class Motors(SerialThread):
""" Serial connection to arduino controlling Prinboo wheelchair motors"""

  def __init__(self, path='/dev/motors'):
    SerialThread.__init__(self, path)
    self.speed = 0  # denotes number of L/Rs we will send to the arduino 
    self.STOP = ' '
    self.direction = self.STOP
    sendSpeed()
    
  def sendSpeed(self):
    s = self.STOP # initial character must reset the uc's internal counter to zero
    
    if self.direction != self.STOP:
      # append a number of l and r's
      for i in range(self.speed): s += self.direction
    self.send(s)

  def stop(self):
    self.direction = self.STOP 
    sendSpeed()

  def turnLeft(self):
    self.speed = 'r' 
    sendSpeed()

  def turnRight(self):
    self.speed = 'r' 
    sendSpeed()

  def forward(self):
    self.speed = 'lr' 
    sendSpeed()

  def backward(self):
    self.speed = 'LR' 
    sendSpeed()
    

class LimbServos(SerialThread):
""" Serial connection to arduino controlling Prinboo limb and head servos"""

    def __init__(self, path='/dev/limbs'):
        SerialThread.__init__(self, path)
        self.anglesDict = {}

    def getAngle(self, id): return self.anglesDict[id]

    def setAngle(self, idOrDict, angle=None):
      if isinstance(idOrDict, int):
        self.anglesDict[idOrDict] = angle
      elif isinstance(idOrDict, dict) and angle == None:
        for id,a in idOrDict.items(): self.anglesDict[id] = a
      elif isinstance(idOrDict, list) and angle == None: 
        id = 1
        for a in idOrDict: 
          self.anglesDict[id] = a
          id += 1
      else: raise TypeError('bad argument to Servos.setAngle')

      self.sendServoPos()

    def __str__(self): return str(self.anglesDict)

    # argument is a dictionary of id:angle
    # angles are 0-1023; center is 512; safe angle range is 200-824
    def sendServoPos(self):
        print(self.anglesDict)
        if not self.valid(): return

        # text protocol of id:angle pairs
        cmd = 's'
        for id,angle in self.anglesDict.items():
            cmd += ' ' + str(id) + ':' + str(angle)

        cmd += '\n'
        #print(cmd)
        self.write(str.encode(cmd))

    def handleLine(self, line): 
        # read the positions of all servos, which is given in a json/python dict format
        preamble ='Servo Readings:' 
        if line.startswith(preamble):
            readingstext = line[preamble.len:] 
            readings = ast.literal_eval(readings_text)
            print(readings_text)
            if not isintance(readings, dict): 
                print('error reading servos')
                return
            self.setAngles(readings)
            
        else: print(line)

    def readServos(self):
        self.write(b'r\n')

