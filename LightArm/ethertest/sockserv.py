import SocketServer, thread, signal

class S(SocketServer.BaseRequestHandler):
  def handle(self):
    while 1:
      self.data = self.request.recv(1024)
      if not self.data:
        break
      #print self.request.getsockname(), 'connected'
      #print self.client_address, ' connected'
      # self.request is the TCP socket connected to the client
      print self.client_address, ':', self.data.strip()
      # just send back the same data, but upper-cased
      self.request.sendall(self.data.upper())

starting_port = 20001
num_sockets = 4

print 'Starting listening to', num_sockets, 'at starting port', starting_port, '...'

def socket_serve(name, port):
  s = SocketServer.TCPServer(('', port), S)
  s.serve_forever()

for port in range(starting_port, starting_port + num_sockets):
  thread.start_new_thread(socket_serve, ('Thread Port ' + str(port), port))

print 'finished\n'
signal.pause()
