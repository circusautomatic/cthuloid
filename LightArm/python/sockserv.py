import SocketServer, thread, signal, time, socket, random

starting_port = 1 + 1000 * random.randint(1, 9)
num_sockets = 5

class S(SocketServer.BaseRequestHandler):
  def handle(self):
    print self.request.getsockname(), 'connected to', self.client_address
    while 1:
      self.data = self.request.recv(1024)
      if not self.data:
        print self.request.getsockname(), 'disconnected from', self.client_address
        break
      # self.request is the TCP socket connected to the client
      print self.client_address, ':', self.data.strip()
      # just send back the same data, but upper-cased
      self.request.sendall(self.data.upper())
      print self.request.getsockname(), 'disconnected from', self.client_address
      return

print 'Starting listening to', num_sockets, 'at starting port', starting_port, '...'

def socket_serve(name, port):
  s = SocketServer.TCPServer(('', port), S)
  s.serve_forever()

threads = []

for port in range(starting_port, starting_port + num_sockets):
  threads.append(thread.start_new_thread(socket_serve, ('Thread Port ' + str(port), port)))

#print(threads)
#for thread in threads:
time.sleep(100) 



def sockopt(s):
  return s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)

print 'finished\n'
'''s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setblocking(0)
print s.connect_ex(('10.0.0.123', starting_port))
print 'connecting'
now = time.time()
while time.time() - now < .1:
  print time.time() - now, sockopt(s)
  time.sleep(.01)

def send_sleep(s):
  print 'sending'
  s.send(b'ba')
  print sockopt(s)
  time.sleep(2)#print s.recv(1000)
  print sockopt(s)
  print 'sending'
  s.send(b'cde')
  print sockopt(s)
  print s.recv(1000)
  print sockopt(s)

send_sleep(s)

#signal.pause()
exit(0)'''
