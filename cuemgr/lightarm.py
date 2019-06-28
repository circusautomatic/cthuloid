"""Interface for communicating with spotlight robots via network sockets.

A spotlight robot:
- has two servos and an Channel.
- has an ethernet port and separate IP address
- listens on port 1337
- speaks a human-readable protocol.

"""
#raise BaseError('Not using Lightarms at the moment')
import socket, os, errno, select, threading, time, random, signal, sys, struct
from console import * 

class NetworkArm:
  """Abstracts one spotlight robot over ethernet.

  This class is collected by class LightArms and its socket is waited on by class SocketsThread.
  """

  #NumServos = 2
  #self.numServos = 12#3

  # this class doesn't limit the Channel values
  MinChannelValue = 0
  MaxChannelValue = 65534

  def fitServoRange(v): return max(212, min(812, v))
  def fitChannelRange(v): return max(0, min(NetworkArm.MaxChannelValue, v))

  def __init__(self, id=None, address=None, port=1337, numChannels=1, numServos=0, inversions=None):
    '''
    pass either id or addr
    id is the last byte of the IP address
    addr is the whole IP address as a string
    inverted is a list of numServos booleans

    '''
    print('NetworkArm: ', address, numChannels)
    self.numChannels = numChannels
    self.numServos = numServos

    self.address = address
    if self.address == None: self.address = '10.0.0.' + str(id)
    self.port = port
    self.socket = None

    self.inverted = inversions or [False] * self.numServos
    self.angles = [512] * self.numServos
    self.relaxed = False

    # Channels
    self.channels = [0] * self.numChannels
    #self.channels = [int(self.MaxChannelValue/2)] * self.numChannels

    self.createSocket()
    #for i in range(1, self.numServos+1):
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

  # input range is 0-999
  # output range is 0-65534
  def toHighFreq(self, pwm):
    #return int(10535 + pwm / 999 * 55000)
    #return int(pwm / 999 * 65534)
    return int(pwm)

  def getChannels(self): return list(self.channels)
  def getChannel(self, channel): return self.channels[channel]

  # argument is PWM value 0-999
  def setChannel(self, channel, value):
    self.channels[channel] = value
    self.sendPWM()

  def setChannels(self, channels):
    if len(channels) != len(self.channels):
      print("Number of channels doesn't match on address: ", self.address)
      getchMsg()
    for i in range(min(self.numChannels, len(channels))):
      self.channels[i] = channels[i]
    self.sendPWM()

  def sendPWM(self):
    cmd = 'pwm '
    for i in self.channels:
      cmd += str(self.toHighFreq(i)) + ' '
    #print(cmd)
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

    for i in range(self.numServos):
      dim = (i-1) % len(self.angles)
      angle = self.invert(i, self.angles[i])
      cmd += ' ' + str(i+1) + ':' + str(angle)

    self.send(cmd)

  # appends newline
  def send(self, string):
    #print(self.address, ':', string)
    try:
      self.socket.send((string + '\r\n').encode())
    except (BrokenPipeError, BlockingIOError, OSError) as e:
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
        #s.send(b'speed 50\n')
        self.arms.findArm(s).sendPosition()
        self.arms.findArm(s).sendPWM()

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
        print('received:', data)
        arm = self.arms.findArm(s)
        arm.updateAngles(data)


class LightArms:
  """Abstracts control of a network of spotlight robots.

  It uses an instance of SocketsThread for non-blocking network communication. Calling exit()
  is necessary to terminate the thread.

  self.arms is a list of class NetworkArm, each with an IP address.

  """

  MaxChannels = 12 # max displayed

  _singleton = None

  def __new__(cls):
    if not cls._singleton:
      print('making Arms singleton')
      cls._singleton = object.__new__(cls)
    return cls._singleton
    
  def __init__(self):
    self.arms = []
    self.thread = SocketsThread(self)

  def initialize(self, configDict):
    for args in configDict.get('LightArms', {}):
      self.arms.append(NetworkArm(**args))

  def exit(self):
    for arm in self.arms: arm.exit()
    self.thread.exit()

  def fitServoRange(self, x): return NetworkArm.fitServoRange(x)
  def fitChannelRange(self, x): return NetworkArm.fitChannelRange(x)
  def num(self): return len(self.arms)

  def findArm(self, socketOrIP):
    for arm in self.arms:
      if isinstance(socketOrIP, str):
        if socketOrIP == arm.address: return arm
      else:
        if socketOrIP == arm.socket: return arm
    return None

  def getChannels(self, index):
    route = self.arms[index]
    return route.getChannels()
 
  def getChannel(self, index, channel):
    route = self.arms[index]
    return route.getChannel(channel)

  def setChannels(self, index, values):
    route = self.arms[index]
    route.setChannels(values)

  def setChannel(self, index, channel, value):
    route = self.arms[index]
    route.setChannel(channel, value)

  def getAngle(self, index, dim):
    arm = self.arms[index]
    angle = arm.getAngle(dim)
    return angle

  def setAngle(self, index, dim, angle):
    arm = self.arms[index]
    arm.setAngle(dim, angle)
    return

#    if isinstance(indexOrDict, int):
#      indexOrDict = {indexOrDict:angle}
#    elif isinstance(indexOrDict, list):
#      d = {}
#      for i in indexOrDict: d[i] = angle
#      indexOrDict = d
#
#    if isinstance(indexOrDict, dict):
#      # split a dict into multiple dicts based on each ID's route
#      dicts = {}
#      for index,angle in indexOrDict.items():
#        servo = self.servos[index]
#        if servo.invert: angle = Servo.inverse(angle)
#        route = servo.route
#        if route not in dicts: dicts[route] = {}
#        dicts[route][servo.id] = angle
#      for route in dicts:
#        route.setAngle(dicts[route])

  def relax(self, index):
    self.arms[index].relax()

  def __str__(self):
    d = {}
    for arm in self.arms:
      led = []
      for channel in range(arm.numChannels):
        led.append(arm.getChannel(channel))
      d[arm.address] = {'channels':led}

      if arm.numServos > 0:
        angles = []
        for i in range(arm.numServos):
          angles.append(arm.getAngle(i))
        d[arm.address]['servos'] = angles

    return str(d)

  def load(self, armData):
    for address, d in armData.items():
      arm = self.findArm(address)
      if arm is None:
        print("Address not found:", self.address)
        getchMsg()
        continue

      channels = d['channels'] 
      if len(channels) != arm.numChannels:
        print("Number of channels doesn't match for address:", arm.address)
        getchMsg()
        continue

      arm.setChannels(channels)

      angles = d.get('servos', [])
      if len(angles) != arm.numServos:
        print("Number of servos doesn't match for address:", arm.address)
        getchMsg()
        continue

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
