import socket, os, errno, select, threading, time, random
import signal, sys

starting_port = 10001
num_sockets = 2
timeout = 100
sockets = [] 

for port in range(starting_port, starting_port + num_sockets): 
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.setblocking(0)
  err = sock.connect_ex(('localhost', port))
  #if err != errno.EINPROGRESS:
  #  pass
  print errno.errorcode[err], os.strerror(err)
  sockets.append(sock)

class SocketsThread (threading.Thread):
  def __init__(self, sockets):
    self.sockets = sockets
    self.shouldExit = False
    try:
      # don't bother doing any other initialization if we can't open the port
      self.lock = threading.Lock()
      threading.Thread.__init__(self)
      self.start()
    except:
      pass

  def run(self):
    readers, writers, errors = [], list(sockets), []
    while not self.shouldExit:
      print '\nselecting...'
      r, w, e = select.select(readers, writers, errors, 1)
      if r: print 'readers:', r
      if w: print 'writers:', w

      for s in w:
        s.send('r')
        writers.remove(s)
        readers.append(s)

      for s in r:
        data = s.recv(1024)
        if not data:
          print 'closed'
          exit()
        print 'received:', data 

      for s in e:
        print 'error:', s

S = SocketsThread(sockets)

def signal_handler(signal, frame):
  print('\nexiting...')
  S.shouldExit = True
  #sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

while not S.shouldExit:
  time.sleep(1)
  i = random.randint(0, len(sockets)-1)
  #for i in range(0, len(sockets)):
  #try:
  sockets[i].send('r' + str(i))
  #except socket.error:
    #print 'error writing to socket' # and recreate connection periodically

