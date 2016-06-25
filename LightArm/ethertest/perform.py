import socket, os, errno, select, threading, time, random
import signal, sys
from console import getch

addresses = ["10.0.0.71", "10.0.0.72", "10.0.0.74"]
port = 1337
timeout = 100
socketThreads = [] 

gShouldExit = False

def sendPWM(sock, pwm):
  cmd = 'pwm ' + str(pwm) + '\n'
  #print(cmd)
  #self.socket.send(cmd)
  sock.sendall(bytes(cmd, 'UTF-8'))

PWMlow = 5
PWMhigh = 200

def calcStepSize(x):
  if x < 32: return 1
  elif x < 64: return 2
  elif x < 128: return 3
  else: return 4

class SocketThread (threading.Thread):
  def __init__(self, socket, address, dimming):
    self.dimming = dimming
    self.address = address
    self.socket = socket
    #self.shouldExit = False
    #try:
      # don't bother doing any other initialization if we can't open the port
      #self.lock = threading.Lock()
    threading.Thread.__init__(self)
    self.start()
    #except:
    #  pass

  def run(self):
    PWM_fade_interval = .03

    try:
      if self.dimming:
        print('fading off  ', self.address)
        pwm = PWMhigh
        while pwm > PWMlow and not gShouldExit: 
          sendPWM(self.socket, pwm)
          time.sleep(PWM_fade_interval)
          interval = calcStepSize(pwm)
          pwm -= interval
      else:
        print('fading on ', self.address)
        pwm = PWMlow
        while pwm < PWMhigh and not gShouldExit: 
          sendPWM(self.socket, pwm)
          time.sleep(PWM_fade_interval)
          interval = calcStepSize(pwm)
          pwm += interval
 
      print('finished ', self.address)
    except:
      print('failed ', self.address)

"""def signal_handler(signal, frame):
  print('\nexiting...')
  gShouldExit = True
  #for t in socketThreads: t.shouldExit = True
  sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
"""
sockets = []
on = []  # list of bools

for address in addresses:
  print('connecting to', address)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(2.0)
  #sock.setblocking(0)
  #try:
  sock.connect((address, port))
  print('connected to ', address)
  sendPWM(sock, PWMlow)
  #except:
  #  print('error on ', address)
  sockets.append(sock)
  on.append(False)

# 'on' list contains the opposite of the bool we send to SocketThread, so call SocketThread first and then flip
def toggleFade(index):
    SocketThread(sockets[index], addresses[index], on[index])
    on[index] = not on[index]
  
print('Type 1, 2, or 3 to fade a light up or down:')
while True:
  c = getch()
  print(c)
  if c == '\x1b': sys.exit()
  if c == '1': toggleFade(0)
  if c == '2': toggleFade(1); toggleFade(2)
#while not gShouldExit:
#    time.sleep(.2)
    
#  i = random.randint(0, len(sockets)-1)
#  #for i in range(0, len(sockets)):
#  try:
#    sockets[i].send('r' + str(i))
#  except socket.error:
#    print 'error writing to socket' # and recreate connection periodically

