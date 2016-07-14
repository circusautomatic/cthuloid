import glob
import platform
import serial
import serial.tools.list_ports
import time

if platform.system() == 'Darwin':
	portSearch = '/dev/tty.usbmodem'
	portSearch = portSearch + "*"
	ports = glob.glob(portSearch)
elif platform.system() == 'Linux':
	portSearch = '/dev/ttyACM'
	ports = [portTuple[0] for portTuple in serial.tools.list_ports.grep(portSearch)]

arduino = serial.Serial(ports[0],9600)
#arduino = serial.Serial('/dev/ttyACM0',9600)
#arduino = serial.Serial('/dev/tty.usbmodem14131',9600)
     
import struct

time.sleep(2)

values = [255, 180, 180, 180, 180, 180, 180, 180, 180, 180]
for i in values:
	arduino.write(struct.pack('>B', i))

time.sleep(1)

values = [255, 0, 0, 0, 0, 0, 0, 0, 0, 0]
for i in values:
	arduino.write(struct.pack('>B', i)) 