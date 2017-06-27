import socket, select, threading, os, errno

class SocketOwner:
  '''Derive from this class to use with SocketsThread for multiple socket IO.
  '''

  def readyForWriting(self): print('socket connected: ', self.address, ':', self.port) 
  def dataReceived(self, data): print('data received: ', data)
  def socketClosed(self): print('socket closed: ', self.address, ':', self.port)

  def __init__(self, address, port):
    self.address = address
    self.port = port
    self.socket = None
    self.error = None

    self.createSocket()

  def createSocket(self):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setblocking(0)
    self.error = self.socket.connect_ex((self.address, self.port))
    if self.error != errno.EINPROGRESS:
      print('error creating connection to', self.address, ':', errno.errorcode[err], os.strerror(err))
      return False
    return True

  def write(self, s):
    if isinstance(s, str): s = str.encode(s)
    # TODO check if socket is reconnecting or has an error
    return self.socket.sendall(s)


class LinedSocketOwner(SocketOwner):
  ''' SocketOwner which assembles received data into delimited lines.
  '''

  def __init__(self, address, port, delim='\n'):
    self.buffer = ''#bytearray()
    self.delim = delim

    SocketOwner.__init__(self, address, port)

  def handleLine(self, line): self.print('line received: ', line)

  def dataReceived(self, data):
    self.buffer += data.decode("utf-8")
            
    ixNewline = self.buffer.find(self.delim)
    while ixNewline != -1:
      v = self.buffer[:ixNewline]
      self.handleLine(v)
      self.buffer = self.buffer[ixNewline+1:]
      ixNewline = self.buffer.find(self.delim)
                


class SocketsThread (threading.Thread):
  """Single thread waits on and handles IO for multiple sockets. Designed for use with SocketOwner.
  
  Maintains a map of sockets to owner. To use, call addSocket() for every socket, THEN call start(). You should not add or remove sockets once start is called.

  The thread will continue running until exit() is called.

  TODO: This class is not thread-safe. Given that python's implementation of socket is a wrapper of posix sockets, it is unclear whether synchronization is required to read and write the socket from different threads. But updating other parts of your program from callbacks here calls for synchronization (if python actually had true parallelism).
  TODO: If the connection is reset, the owner's createSocket method is called again to attempt to reconnect. Writing directly to the socket during this process will probably result in an error or lost data.
  """
  def __init__(self, owners = None, heartBeatOwner = None):
    self.sockets = {}
    self.shouldExit = False
    #self.lock = threading.Lock()
    threading.Thread.__init__(self)

    for o in owners: self.addSocket(o.socket, o)
    self.heartBeatOwner = heartBeatOwner

  def exit(self):
    self.shouldExit = True

  def addSocket(self, socket, owner):
    self.sockets[socket] = owner

  def run(self):
    readers, writers, errors = [], [], []
    for s in self.sockets:
      if self.sockets[s].error != errno.EINPROGRESS:
        print('socket failed to connect')
        continue
      print('adding socket:', s.getsockname())
      writers.append(s)
      errors.append(s)

    while not self.shouldExit:
      r, w, e = select.select(readers, writers, errors, .1)
      #if r or w: print('select readers/writers:', len(r), ',', len(w))

      # TODO hack to send heartbeat to Prinboo's motors every .1 seconds
      if self.heartBeatOwner and not self.heartBeatOwner.socket in e:
          self.heartBeatOwner.write('~') #send heartbeat

      for s in e:
        print('error:', s.getsockname())

      for s in w:
        o = self.sockets[s]
        print('ready for writing:', o.port)
        self.sockets[s].readyForWriting()
        writers.remove(s)
        readers.append(s)

      for s in r:
        data = None
        try:
          data = s.recv(2048)
        except ConnectionRefusedError:
          print('refused: ', s.getsockname())
          r.remove(s)
          continue
        except OSError as e:
          print(e, s.getsockname())
          r.remove(s)
          continue
        except ConnectionResetError:
          self.sockets[s].createSocket() #reconnect
          continue
        if not data:
          print('closed: ', s.getsockname())
          r.remove(s)
          self.sockets[s].socketClosed()
          continue
        #print('received:', data)
        self.sockets[s].dataReceived(data)

if __name__ == '__main__':
    o = LinedSocketOwner('10.10.10.120', 1338)
    t = SocketsThread()
    t.addSocket(o.socket, o)
    t.start()

