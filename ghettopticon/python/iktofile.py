from math import pi
import bpy
import sys
import time
import struct

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
out.write('\n'.join(["%.4f,%.4f"%(up,fo) for f, up,fo in frame_locs]) )