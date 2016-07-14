from math import pi
import bpy
import sys
import time
import struct

sys.path.append("/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/")
import serial

sc = bpy.context.scene
original_frame = sc.frame_current

arma = bpy.data.objects["arm_rig"]
fo = arma.pose.bones["forearm"]
up = arma.pose.bones["upperarm"]

rad_to_deg = 180.0/pi

frame_locs = []
sc.frame_set(sc.frame_start)
while sc.frame_current <= sc.frame_end:
    bpy.context.scene.update()
    
    up_q = up.matrix.to_quaternion()
    fo_q = fo.matrix.to_quaternion()
    fo_q.rotate(up.matrix)

    up_a = up_q.to_euler().x * rad_to_deg + 90
    fo_a = fo_q.to_euler().x * rad_to_deg
    
    up_a = 0 if up_a < 0 else up_a
    
    frame_locs.append((sc.frame_current, up_a, fo_a))

    sc.frame_set(sc.frame_current + 1)
sc.frame_current = original_frame

out = bpy.data.texts["out"]
out.clear()
out.write( '\n'.join(["%i:{%.4f, %.4f}"%(f,up,fo) for f,up,fo in frame_locs]) )

arduino = serial.Serial('/dev/tty.usbmodem14131',9600,timeout=1)
for (f, up, fo) in frame_locs:
    arduino.write(struct.pack('>B', 255))
    arduino.write(struct.pack('>B', int(up)))
    arduino.write(struct.pack('>B', int(fo)))
    #time.sleep(0.5)