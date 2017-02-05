# pwm fade over network socket

import socket, math, time

# Create a TCP/IP socket
server_addresses = [('10.0.2.3', 1337), ('10.0.2.4', 1337), ('10.0.2.6', 1337)]
#server_address = ('127.0.0.1', 10001)
sockets = []

try:
  for server_address in server_addresses:
    print('connecting to', server_address)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    sock.connect(server_address)
    sockets.append(sock)

  print('connected?')
  maxpwm = 65535
  minpwm = 3000
  inc = -100
  i = maxpwm
  while True:
    for sock in sockets:
      s = 'pwm 65535\ncircle 1 5\n'#'pwm ' + str(abs(i)) + '\n'
      print(s)
      sock.sendall(bytes(s, 'UTF-8'))

      '''i += inc
      if i <= minpwm or i >= maxpwm: inc *= -1)
      time.sleep(.05)'''
      time.sleep(2)

except socket.timeout:
    print('error: connected timed out')

