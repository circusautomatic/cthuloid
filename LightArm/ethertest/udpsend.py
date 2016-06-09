import socket
import time

#UDP_IP = '192.168.1.70'
UDP_IP = '10.0.0.70'
UDP_PORT = 1337
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT, "\n"

def sendCmd(cmd):
  print "Sending '", cmd, "'"
  sock.sendto(cmd + "\n", (UDP_IP, UDP_PORT))
  print "Awaiting echo..."
  print sock.recvfrom(1024), "\n"

while 1:
  sendCmd("p 4")
  sendCmd("pwm 4")
  time.sleep(1)
  sendCmd("p 3")
  sendCmd("pwm 255")
  time.sleep(1)


