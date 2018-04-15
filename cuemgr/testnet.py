#!/usr/bin/env python

import socket


TCP_IP = '10.0.0.159'
TCP_PORT = 1337
BUFFER_SIZE = 1024
MESSAGE = "pwm 25000 25000 25000 \r \n"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)

s.close()
