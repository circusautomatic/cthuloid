import socket, os, errno, ast, paramiko, time
from socketsthread import *

class Screen:
    '''Play videos on Prinboo's raspi via SSH connection.
    '''
    target = " > /var/run/omxctl\n"
    
    def __init__(self, address):
      #try:
        ssh = paramiko.SSHClient()
        self.ssh = ssh
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(address, username='pi', password='tankgirl')
        
        #cmd = '/home/pi/rach.mp4'
        #print("echo A " + cmd + " > /var/run/omxctl\n")
        #self.ssh.exec_command("echo A " + cmd + " > /var/run/omxctl\n")
        self.ssh.exec_command("/home/pi/hidetext.sh\n")
      #except paramiko.ssh_exception.NoValidConnectionsError:
      #  self.ssh = None

    def stop(self):
      self.ssh.exec_command("echo X " + self.target)

    def sendVideoCommand(self, cmd):
        filenamePrefix = '/home/pi/'
        if cmd == 'black': self.stop()
        else:
          if not cmd.startswith('/'): cmd = filenamePrefix + cmd.strip()
          self.ssh.exec_command("echo I " + cmd + self.target)

#    def play(self, filename):
#      # remove special characters and append it to the video player name
#      special = '$\\#!|<>;'
#      for c in special: filename.replace(c, ' ')
#
#      # play video file continuously and hang onto stdin so we can control playback
#      filename = 'omxplayer --loop --orientation 180 ' + filename
#      self.stdin, stdout, stderr = self.ssh.exec_command(filename)
#
#    def togglePlayback(self):
#      self.stdin.write('i')
#      time.sleep(.2)
#      self.stdin.write(' ')

    def exit(self):
      #print('closing')
      self.stop()
      self.ssh.exec_command("/home/pi/showtext.sh\n")
      self.ssh.close()

class Screens:
  _singleton = None

  def __new__(cls):
    if not cls._singleton:
      print("Making Video singleton")
      cls._singleton = object.__new__(cls)
    return cls._singleton

  def __init__(self): 
      self.screens = None
      self.VlcProcess = None
  
  def initialize(self, configDict):
    self.screens = {} #[Screen('10.0.0.19'), Screen('10.0.0.22')]

  def playVideo(self, filename, targetIp):
    if not self.screens.get(targetIp):
      self.screens[targetIp] = Screen(targetIp)

    self.screens[targetIp].sendVideoCommand(filename)

  def exit(self):
    for address,s in self.screens.items(): s.exit()

Video = Screens()

if __name__ == '__main__':
  addr = 'localhost'
  s = Screen(addr)
  #s.play('vlc ~/circusautomatic/cthuloid/ghettopticon/blender/prinboo0001-1000.mp4')
