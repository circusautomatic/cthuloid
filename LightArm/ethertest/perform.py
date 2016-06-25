import socket, os, errno, select, threading, time, random
import signal, sys
from console import getch

addresses = ["10.0.0.71", "10.0.0.72", "10.0.0.74"]
port = 1337
timeout = 100
socketThreads = [] 

gShouldExit = False

class SocketThread (threading.Thread):
  def __init__(self, socket, dimming):
    self.dimming = dimming
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
    print('running ', socket)
    lower = 5
    upper = 200 
    wait = .05

    def sendAndWait(pwm):
        cmd = 'pwm ' + str(pwm) + '\n'
        print(cmd)
        #self.socket.send(cmd)
        sock.sendall(bytes(cmd, 'UTF-8'))
        time.sleep(wait)

    if self.dimming:
      pwm = upper
      while pwm > lower and not gShouldExit: 
        sendAndWait(pwm)
        interval = int(round(pwm * .9 + 1))
        pwm -= interval
    else:
      pwm = lower

    print('finished ', socket)


"""def signal_handler(signal, frame):
  print('\nexiting...')
  gShouldExit = True
  #for t in socketThreads: t.shouldExit = True
  sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
"""
sockets = []

for address in addresses:
  print('connecting to', address)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(2.0)
  #sock.setblocking(0)
  sock.connect((address, port))
  print('connected to  ', address)
  sockets.append(sock)  

  
print('Type 1, 2, or 3 to fade a light up or down:')
while True:
  c = getch()
  if c == '\x1b': sys.exit()
  if c == '1': SocketThread(sockets[0], True)
#while not gShouldExit:
#    time.sleep(.2)
    
#  i = random.randint(0, len(sockets)-1)
#  #for i in range(0, len(sockets)):
#  try:
#    sockets[i].send('r' + str(i))
#  except socket.error:
#    print 'error writing to socket' # and recreate connection periodically

