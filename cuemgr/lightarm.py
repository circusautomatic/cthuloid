"""Interface for communicating with spotlight robots via network sockets.

Each spotlight robot:
- has two servos and an LED.
- has an ethernet port and separate IP address
- listens on port 1337
- speaks a human-readable protocol.

"""

import socket, os, errno, select, threading, time, random, signal, sys, struct

#######################################################################
# dynamixel servos
#class Servos(SerialThread):
#    def __init__(self, path):
#        SerialThread.__init__(self, path)
#        self.mode = None
#        self.numLinesToFollow = 0
#        self.anglesDict = {}
#
#        # LEDs
#        self.MinValue = 0
#        self.MaxValue = 255
#        self.NumChannels = NumArrays
#        self.values = [self.MinValue] * self.NumChannels
#
#        #self.NumServos = 4 * NumArrays
#        #for i in range(1, self.NumServos+1):
#        #    self.set(i, 512)
#
#    def getLED(self, channel): return self.values[channel]
#
#    # arguments are PWM values 0-255
#    def setLED(self, channel, values):
#      if isinstance(values, int): values = [values]
#    
#      for v in values:
#        self.values[channel] = v
#        channel += 1
#
#      cmd = 'pwm'
#      for v in self.values: cmd += ' ' + str(v)
#      cmd += '\n'
#
#      self.write(str.encode(cmd))
#
#    def getAngle(self, id): return self.anglesDict[id]
#
#    def setAngle(self, idOrDict, angle=None):
#      if isinstance(idOrDict, int):
#        self.anglesDict[idOrDict] = angle
#      elif isinstance(idOrDict, dict):
#        for id,angle in idOrDict.items(): self.anglesDict[id] = angle
#      elif isinstance(idOrDict, list): 
#        for id in idOrDict: self.anglesDict[id] = angle
#      else: raise TypeError('bad argument to Servos.setAngle')
#
#      self.setServoPos()
#
#    def __str__(self): return str({'LEDs':self.values, 'Servos':self.anglesDict})
#
#    # argument is a dictionary of id:angle
#    # angles are 0-1023; center is 512; safe angle range is 200-824
#    def setServoPos(self, binary=False):
#        print(self.anglesDict)
#        if not self.valid(): return
#
#        # send a text command which says to expect a block of binary
#        # then send the angles as an array of 16-bit ints in order
#        # angle is set to 0 for missing IDs
#        if binary:
#            maxID = 0  # IDs start at 1, so numAngles = highest ID
#            for id,angle in anglesDict.items(): 
#                maxID = max(maxID, id)
#
#            cmd = 'B ' + str(maxID) + '\n'
#            #print(cmd)
#            self.write(str.encode(cmd))
#
#            buf = bytearray()
#            for id in range(1, maxID+1):
#                angle = 0
#                if id in anglesDict: angle = anglesDict[id]
#                
#                # 16-bit little endian
#                buf += struct.pack('<H', angle)
#            
#            print(buf)
#            ucServos.write(buf)
#
#        # text protocol of id:angle pairs
#        else:
#            cmd = 's'
#            for id,angle in self.anglesDict.items():
#                cmd += ' ' + str(id) + ':' + str(angle)
#
#            cmd += '\n'
#            #print(cmd)
#            self.write(str.encode(cmd))
#
#    def handleLine(self, line): pass
#        # read the positions of all servos, which is spread over multiple lines
#        # expect the next some number of lines to be servo info
##        if line.startswith('Servo Readings:'):
##            self.numLinesToFollow = int(line[15:])
##            self.mode = 'r'
##            self.anglesDict = {}
##            print('expecting', self.numLinesToFollow, 'servo readings')
##
##        # information about a single servo, on a single line
##        elif self.mode == 'r':
##            id, pos = None, None
##            for pair in line.split():
##                kv = pair.split(':')
##                key = kv[0]
##                if   key == 'ID':  id = int(kv[1])
##                elif key == 'pos': pos = int(kv[1])
##            self.anglesDict[id] = pos
##            self.numLinesToFollow -= 1
##            
##            # done, reset mode
##            if self.numLinesToFollow == 0:
##                print(self.anglesDict)
##                self.mode = None
##                
##        #else: print(line)
#
#    # takes one or a list of IDs
#    # relaxes all if IDs is None
#    def moveAllServos(self, pos, binary=False):
#        anglesDict = {}
#        for i in range(numServos):
#            anglesDict[i+1] = pos
#        self.setServoPos(binary)
#
#    def readServos(self):
#        self.write(b'r\n')

class NetworkArm:
  """Abstracts one spotlight robot over ethernet.
 
  This class is collected by class LightArms and its socket is waited on by class SocketsThread.
  """
  
  NumServos = 2
  
  def __init__(self, id=None, addr=None, port=1337, inverted=None):
    '''
    pass either id or addr
    id is the last byte of the IP address
    addr is the whole IP address as a string
    inverted is a list of NumServos booleans
    
    '''
    self.address = addr
    if self.address == None: self.address = '10.0.2.' + str(id)
    self.port = port
    self.socket = None

    self.inverted = inverted or [False] * self.NumServos 
    self.angles = [512] * self.NumServos
    self.relaxed = False

    # LEDs
    self.MinValue = 0
    self.MaxValue = 999
    self.intensity = self.MaxValue

    self.createSocket()
    #for i in range(1, self.NumServos+1):
    #    self.set(i, 512)

  def createSocket(self):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setblocking(0)
    err = self.socket.connect_ex((self.address, self.port))
    if err != errno.EINPROGRESS:
      print('error creating connection to', self.address, ':', errno.errorcode[err], os.strerror(err))
      return False
    return True
   
  def exit(self): 
    self.socket.close()

  def getLED(self): return self.intensity

  # input range is 0-999
  # output range is 0-65535
  def toHighFreq(self, pwm):
    return int(10535 + pwm / 999 * 55000)

  # argument is PWM value 0-999
  def setLED(self, intensity):
    self.intensity = intensity
    pwm = str(self.toHighFreq(intensity))
    cmd = 'pwm ' + pwm
    self.send(cmd)

  def relax(self):
    if self.relaxed: cmd = 'torq'
    else: cmd = 'relax'
    self.relaxed = not self.relax
    self.send(cmd)

  def invert(self, dim, angle): 
    if self.inverted[dim]: return 1024 - angle
    else: return angle

  def getAngle(self, dim): return self.angles[dim]

  def updateAngles(self, strDict):
    pass
    #TODO: need to buffer this in case it is broken up by TCP while sending
    # then parse and update self.angles, inverting if necessary

  def setAngle(self, dim, angle): 
    self.angles[dim] = angle
    self.sendPosition()

  def setAngles(self, listOf2):
    for i in len(self.angles):
      self.angles[i] = listOf2[i]
    self.sendPosition()

  def sendPosition(self):
    # servo IDs start at 1; base Servo ID = 1, wrist Servo ID = 2
    # but we're storing angles in a zero-indexed list
    cmd = 's'

    for i in range(self.NumServos):
      dim = (i-1) % len(self.angles)
      angle = self.invert(i, self.angles[i])
      cmd += ' ' + str(i+1) + ':' + str(angle)

    self.send(cmd)

  # appends newline
  def send(self, string):
    #print(string)
    try:
      self.socket.send((string + '\n').encode())
    except (BrokenPipeError, BlockingIOError) as e:
      print(self.address, '-', str(e))


class SocketsThread (threading.Thread):
  """waits on the sockets in the arms of a LightArms object"""
  def __init__(self, arms):
    self.arms = arms
    self.shouldExit = False
    try:
      # don't bother doing any other initialization if we can't open the port
      #self.lock = threading.Lock()
      threading.Thread.__init__(self)
      self.start()
    except:
      print('error starting sockets thread')

  def exit(self):
    self.shouldExit = True

  def run(self):
    readers, writers, errors = [], [], []
    for arm in self.arms.arms:
      writers.append(arm.socket)
      errors.append(arm.socket)

    while not self.shouldExit:
      r, w, e = select.select(readers, writers, errors, 1)
      #if r or w: print('select readers/writers:', len(r), ',', len(w))

      for s in e:
        print('error:', s.getsockname())

      for s in w:
        print('ready for writing:', s.getsockname())
        s.send(b'speed 50\n')
        self.arms.findArm(s).sendPosition()

        writers.remove(s)
        readers.append(s)

      for s in r:
        data = None
        try: data = s.recv(1024)
        except ConnectionRefusedError:
          print('refused')
          r.remove(s)
          continue
        except ConnectionResetError:
          self.findArm(s).createSocket() #reconnect
          continue
        if not data:
          print('closed')
          r.remove(s)
          return#continue
        #print('received:', data)
        arm = self.arms.findArm(s)
        arm.updateAngles(data)


class LightArms:
"""Abstracts control of a network of spotlight robots.

It uses an instance of SocketsThread for non-blocking network communication. Calling exit()
is necessary to terminate the thread.

self.arms is a list of class NetworkArm, each with an IP address.

"""

  def __init__(self):
    # 
    self.arms = [
      #NetworkArm(8)#, inverted=[True, False]),  # stage right side
      NetworkArm(3, inverted=[True, False]), # stage right front
      NetworkArm(6),                         # stage right back
      NetworkArm(2),                         # stage left back
      NetworkArm(4, inverted=[False, True]), # stage left front
      NetworkArm(5, inverted=[True, False]), # stage left side
      #NetworkArm(10),                        # aerial overhead
    ]
    #for i in range(5): self.arms.append(NetworkArm(addr='localhost', port=3001+i))

    self.thread = SocketsThread(self)

    # TODO command to center for now, but read position in future
    #ids = [s.id for s in self.servos if s.route == serial]
    #serial.setAngle(ids, 512)

  def exit(self):
    for arm in self.arms: arm.exit()
    self.thread.exit()

  def num(self): return len(self.arms)

  def findArm(self, socketOrIP):
    for arm in self.arms:
      if isinstance(socketOrIP, str):
        if socketOrIP == arm.address: return arm
      else:
        if socketOrIP == arm.socket: return arm
    return None

  def getLED(self, index):
    route = self.arms[index]
    return route.getLED()
  def setLED(self, index, value):
    route = self.arms[index]
    route.setLED(value)

  def getAngle(self, index, dim):
    arm = self.arms[index]
    angle = arm.getAngle(dim)
    return angle

  def setAngle(self, index, dim, angle):
    arm = self.arms[index]
    arm.setAngle(dim, angle)
    return

    if isinstance(indexOrDict, int):
      indexOrDict = {indexOrDict:angle}
    elif isinstance(indexOrDict, list):
      d = {}
      for i in indexOrDict: d[i] = angle
      indexOrDict = d
    
    if isinstance(indexOrDict, dict):
      # split a dict into multiple dicts based on each ID's route
      dicts = {}
      for index,angle in indexOrDict.items():
        servo = self.servos[index]
        if servo.invert: angle = Servo.inverse(angle)
        route = servo.route
        if route not in dicts: dicts[route] = {}
        dicts[route][servo.id] = angle
      for route in dicts:
        route.setAngle(dicts[route])

  def __str__(self):
    d = {}
    for arm in self.arms:
      led = arm.getLED()
      angles = []
      for i in range(NetworkArm.NumServos):
        angles.append(arm.getAngle(i))
      d[arm.address] = {'servos':angles, 'intensity':led}

    return str(d)

  def load(self, armData):
    for address, d in armData.items():
      arm = self.findArm(address)
      if arm is None: continue
      arm.setLED(d['intensity'])
      angles = d['servos'] 
      for i in range(len(angles)):
        arm.setAngle(i, angles[i])

#singleton
Arms = LightArms()

if __name__ == '__main__':
  def signal_handler(signal, frame):
    print('\nexiting...')
    Arms.exit()
    #sys.exit(0)
  signal.signal(signal.SIGINT, signal_handler)

