import socket, os, errno, select, threading, time, random
import signal, sys

addresses = ["10.0.0.71", "10.0.0.73", "10.0.0.74", "10.0.0.72"]
port = 1337
timeout = 100
socketThreads = [] 

gShouldExit = False

class SocketThread (threading.Thread):
  def __init__(self, socket):
    self.socket = socket
    #self.shouldExit = False
    try:
      # don't bother doing any other initialization if we can't open the port
      self.lock = threading.Lock()
      threading.Thread.__init__(self)
      self.start()
    except:
      pass

  def run(self):
    lower = 200 + 250
    upper = 824 - 250
    maxWait = 4 

    while not gShouldExit:
      time.sleep(random.random() * maxWait)
      x = int(random.uniform(lower, upper))
      y = int(random.uniform(lower, upper))

      cmd = 'speed 40\npwm 200\ns 1:' + str(x) + ' 2:' + str(y) + '\n'
      print cmd
      self.socket.send(cmd)


def signal_handler(signal, frame):
  print('\nexiting...')
  gShouldExit = True
  #for t in socketThreads: t.shouldExit = True
  #sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


for address in addresses:
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  #sock.setblocking(0)
  sock.connect((address, port))
  
  thread = SocketThread(sock)
  socketThreads.append(thread)


while not gShouldExit:
    time.sleep(.2)
#  i = random.randint(0, len(sockets)-1)
#  #for i in range(0, len(sockets)):
#  try:
#    sockets[i].send('r' + str(i))
#  except socket.error:
#    print 'error writing to socket' # and recreate connection periodically

