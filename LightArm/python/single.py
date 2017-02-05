import socket, time, errno

def st():
  global s
  return s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)

def ss(port, blocking=0):
  global s
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setblocking(blocking)
  s.connect_ex(('10.0.0.69', port))
  #time.sleep(1)
  #s.send(b'abc')

while True:
  ss(1337)
