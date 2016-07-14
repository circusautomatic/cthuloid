import glob
import platform
import serial
import serial.tools.list_ports
import sys
import time

if platform.system() == 'Darwin':
	portSearch = '/dev/tty.usbmodem'
	portSearch = portSearch + "*"
	ports = glob.glob(portSearch)
elif platform.system() == 'Linux':
	portSearch = '/dev/ttyACM'
	ports = [portTuple[0] for portTuple in serial.tools.list_ports.grep(portSearch)]

if len(ports) == 0:
	print "No Arduinos found"
	sys.exit()

arduino = serial.Serial(ports[0],9600)
#arduino = serial.Serial('/dev/ttyACM0',9600)
#arduino = serial.Serial('/dev/tty.usbmodem14131',9600)

import struct

fi = open('testdata', 'r')
for line in fi:
	values = line.strip().split(',')
	arduino.write(struct.pack('>B', 255))
	for i in values:
		#arduino.write(struct.pack('>B', int(i)))
		arduino.write(struct.pack('>B', int(i)))
	#time.sleep(1)