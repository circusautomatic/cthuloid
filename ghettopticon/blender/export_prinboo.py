from math import pi
import bpy, sys, time, datetime, struct

from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    sys.path.append("/usr/local/lib/python3.4/dist-packages/")
elif _platform == "darwin":
    sys.path.append("/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/")

import serial

sc = bpy.context.scene
original_frame = sc.frame_current

hrig = bpy.data.objects["h_rig"]

foL = hrig.pose.bones["forearm.L"] 
upL = hrig.pose.bones["upperarm.L"]
handL = hrig.pose.bones["hand.L"]

foR = hrig.pose.bones["forearm.R"] 
upR = hrig.pose.bones["upperarm.R"]
handR = hrig.pose.bones["hand.R"]

skull = hrig.pose.bones["skull"]
neck = hrig.pose.bones["neck"]
face = hrig.pose.bones["face"]

rad_to_deg = 180.0/pi

frame_locs = []
sc.frame_set(sc.frame_start)
while sc.frame_current <= sc.frame_end:
    bpy.context.scene.update()
    
    
    upL_q = upL.matrix.to_quaternion()
    foL_q = foL.matrix.to_quaternion()
    foL_q.rotate(upL.matrix)
    handL_q = handL.matrix.to_quaternion()
    handL_q.rotate(foL.matrix)

    upL_a = upL_q.to_euler().x * rad_to_deg + 90
    foL_a = foL_q.to_euler().x * rad_to_deg
    handL_a = handL_q.to_euler().y * rad_to_deg + 90
    

    upR_q = upR.matrix.to_quaternion()
    foR_q = foR.matrix.to_quaternion()
    foR_q.rotate(upR.matrix)
    handR_q = handR.matrix.to_quaternion()
    handR_q.rotate(foR.matrix) 

    upR_a = upR_q.to_euler().x * rad_to_deg + 90
    foR_a = foR_q.to_euler().x * rad_to_deg
    handR_a = handR_q.to_euler().y * rad_to_deg + 90
    
    upR_a = 180 - upR_a
    
    neck_q = neck.matrix.to_quaternion()
    skull_q = skull.matrix.to_quaternion()
    skull_q.rotate(neck.matrix)
    face_q = face.matrix.to_quaternion()
    face_q.rotate(skull.matrix)
    
    neck_a = 180 + neck_q.to_euler().z * rad_to_deg
    skull_a = 180 + skull_q.to_euler().x * rad_to_deg
    face_a = 90 + face_q.to_euler().y * rad_to_deg

    upL_a = 0 if upL_a < 0 else upL_a
    upL_a = 180 if upL_a > 180 else upL_a
    foL_a = 0 if foL_a < 0 else foL_a
    foL_a = 180 if foL_a > 180 else foL_a
    handL_a = 0 if handL_a < 0 else handL_a
    handL_a = 180 if handL_a > 180 else handL_a
    upR_a = 0 if upR_a < 0 else upR_a
    upR_a = 180 if upR_a > 180 else upR_a
    foR_a = 0 if foR_a < 0 else foR_a
    foR_a = 180 if foR_a > 180 else foR_a
    handR_a = 0 if handR_a < 0 else handR_a
    handR_a = 180 if handR_a > 180 else handR_a
    neck_a = 0 if neck_a < 0 else neck_a
    neck_a = 180 if neck_a > 180 else neck_a
    skull_a = 0 if skull_a < 0 else skull_a
    skull_a = 180 if skull_a > 180 else skull_a
    face_a = 0 if face_a < 0 else face_a
    face_a = 180 if face_a > 180 else face_a
    
    frame_locs.append((sc.frame_current, upL_a, foL_a, handL_a, upR_a, foR_a, handR_a, neck_a, skull_a, face_a))

    sc.frame_set(sc.frame_current + 1)
sc.frame_current = original_frame

filename = 'prinboo_' + str(datetime.datetime.now()).split('.')[0].replace(' ', '_').replace(':', '-') + '.json'

with open(filename, 'w') as out:
    out.write("{\n  'limbs':[\n")
    out.write( '\n'.join(["[%d, %d, %d, %d, %d, %d, %d, %d, %d],"%(upL,foL,handL,upR,foR,handR,neck,skull,face) for f,upL,foL,handL,upR,foR,handR,neck,skull,face in frame_locs]) )
    out.write("\n]}\n")

#arduino = serial.Serial('/dev/ttyACM0',9600,timeout=1)
#for (f, upl, fol, upr, for, neck, skull, face) in frame_locs:
#    arduino.write(struct.pack('>B', 255))
#    arduino.write(struct.pack('>B', int(upl)))
#    arduino.write(struct.pack('>B', int(fol)))
#    arduino.write(struct.pack('>B', int(upr)))
#    arduino.write(struct.pack('>B', int(for)))
#    arduino.write(struct.pack('>B', int(neck)))
#    arduino.write(struct.pack('>B', int(skull)))
#    arduino.write(struct.pack('>B', int(face)))
#    time.sleep(2)
    