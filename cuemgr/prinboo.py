import socket, os, errno, ast, paramiko, time
from socketsthread import *

class Motors(SocketOwner):
  """ Serial connection to arduino controlling Prinboo wheelchair motors"""

  def __init__(self, address):
    SocketOwner.__init__(self, address, 1339)
    self.speed = 0  # denotes number of L/Rs we will send to the arduino 
    self.STOP = ' '
    self.direction = self.STOP

  def readForWriting(self):
    self.sendSpeed()
    

  def sendSpeed(self):
    s = self.STOP # initial character must reset the uc's internal counter to zero
    
    if self.direction != self.STOP:
      # append a number of l and r's
      for i in range(self.speed): s += self.direction
    self.write(s)

  def incSpeed(self):
    self.speed += 1
    self.sendSpeed()

  def decSpeed(self): 
    self.speed -= 1
    self.sendSpeed()

  def stop(self):
    self.direction = self.STOP 
    self.sendSpeed()

  def turnLeft(self):
    self.direction = 'L' 
    self.sendSpeed()

  def turnRight(self):
    self.direction = 'R' 
    self.sendSpeed()

  def forward(self):
    self.direction = 'LR' 
    self.sendSpeed()

  def backward(self):
    self.direction = 'lr' 
    self.sendSpeed()
    

class LimbServos(LinedSocketOwner):
    """ Serial connection to arduino controlling Prinboo limb and head servos"""

    def __init__(self, address):
        LinedSocketOwner.__init__(self, address, 1338)
        self.anglesDict = {}

    def readyForWriting(self):
        super().readyForWriting()
        self.readServos() # request current servo angles
        self.socket.send(b'r\n')

    #def dataReceived(self, data): pass

    def getAngle(self, id): return self.anglesDict[id]

    def setAngle(self, idOrDict, angle=None, sendUpdate=True):
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

      if sendUpdate: self.sendServoPos()

    def __str__(self): return str(self.anglesDict)

    # argument is a dictionary of id:angle
    # angles are 0-1023; center is 512; safe angle range is 200-824
    def sendServoPos(self):
        #print(self.anglesDict)
        #if not self.valid(): return

        # text protocol of id:angle pairs
        cmd = 's'
        for id,angle in self.anglesDict.items():
            cmd += ' ' + str(id) + ':' + str(angle)

        cmd += '\n'
        #print(cmd)
        self.write(cmd)

    def handleLine(self, line): 
        # read the positions of all servos, which is given in a json/python dict format
        preamble ='Servo Readings:' 
        if line.startswith(preamble):
            readings_text = line[len(preamble):].strip() 
            readings = ast.literal_eval(readings_text)
            #print(readings_text)
            if not isinstance(readings, dict): 
                print('error reading servos')
                return
            self.setAngle(readings, sendUpdate=False)
            
        #else: print(line)

    def readServos(self):
        self.write('r\n')

class Screen:
    '''Play videos on Prinboo's raspi via SSH connection.
    '''
    def __init__(self, address): 
      ssh = paramiko.SSHClient()
      self.ssh = ssh
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      ssh.connect(address, username='pi', password='raspberry')
      # start playing immediately
      self.play('~/cthuloid/ghettopticon/blender/prinboo-talking.mp4')

    def play(self, filename): 
      # remove special characters and append it to the video player name
      special = '$\\#!|<>;'
      for c in special: filename.replace(c, ' ')

      # play video file continuously and hang onto stdin so we can control playback
      filename = 'omxplayer --loop --orientation 180 ' + filename
      self.stdin, stdout, stderr = self.ssh.exec_command(filename)

    def togglePlayback(self):
      self.stdin.write('i')
      time.sleep(.2)
      self.stdin.write(' ')

    def exit(self):
      self.stdin.write('q')
      #ssh.close()

class Prinboo:
  def __init__(self, address):
    self.limbs = LimbServos(address)
    self.motors = Motors(address)
    self.screen = Screen(address)
    self.thread = SocketsThread((self.limbs, self.motors), self.motors)
    self.thread.start()

    # keep only one of these threads running at a time
    self.limbsThread = None

  def exit(self):
    self.screen.exit()
    self.thread.exit()
    if self.limbsThread: self.limbsThread.exit()

if __name__ == '__main__':
  addr = 'localhost'
  #p = Prinboo(addr, '')
  s = Screen(addr)
  s.play('vlc ~/circusautomatic/cthuloid/ghettopticon/blender/prinboo0001-1000.mp4')


