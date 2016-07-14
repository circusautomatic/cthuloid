import sys
import time
import struct

sys.path.append("/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/")
import serial
armature = bpy.context.active_object
bones = armature.pose.bones

arduino = serial.Serial('/dev/tty.usbmodem14131',9600,timeout=1)