# pwm fade over network socket

import socket, math, time

# Create a TCP/IP socket
#server_addresses = [('10.0.2.3', 1337), ('10.0.2.4', 1337), ('10.0.2.6', 1337)]
server_addresses = [('10.0.0.253', 1337)]
sockets = []

try:
  for server_address in server_addresses:
    print('connecting to', server_address)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    sock.connect(server_address)
    sockets.append(sock)

  print('connected?')
  interval = .033 #seconds
  maxpwm = 65535
  minpwm = 2000
  inc = 36000
  i = minpwm
  while True:
    for sock in sockets:
      s = 'pwm ' + str(abs(i)) + '\n'
#      print(s)
      sock.sendall(bytes(s, 'UTF-8'))
      if i % 1000 == 0: print(i)

      i += inc
      if i <= minpwm or i >= maxpwm: inc *= -1
      time.sleep(interval)

except socket.timeout:
    print('error: connected timed out')

