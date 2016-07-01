# pwm fade over network socket

import socket, math, time

# Create a TCP/IP socket
server_address = ('10.0.0.77', 1337)
#server_address = ('127.0.0.1', 10001)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2.0)

try:
  print('connecting to', server_address)
  sock.connect(server_address)

  print('connected?')
  maxpwm = 5535
  i = maxpwm
  while True:
    s = 'pwm ' + str(60000 + abs(i)) + '\n'
    print(s)
    sock.sendall(bytes(s, 'UTF-8'))

    i -= 10
    if i <= -maxpwm: i = maxpwm
    time.sleep(.05)

except socket.timeout:
    print('error: connected timed out')

