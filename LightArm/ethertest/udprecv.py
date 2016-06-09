import socket

UDP_IP = ''#192.168.1.15'#"127.0.0.1"
UDP_PORT = 1337

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

while True:
  data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
  sock.sendto('received UDP', addr) 
  print "received message from ", addr, ":", data
