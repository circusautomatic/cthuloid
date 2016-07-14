import bge
import math
from math import *
import mathutils

x=0
y=0
z=0
 
def rotate():
 global x
# Get the whole bge scene
 scene = bge.logic.getCurrentScene()
# Helper vars for convenience
 source = scene.objects

# Get the whole Armature
 main_arm = source.get('arm_rig')

 ob = bge.logic.getCurrentController().owner
 print('x=', x)

 ob.channels['shoulder'].joint_rotation = mathutils.Vector([0,x,0])
 ob.channels['upperarm'].joint_rotation = mathutils.Vector([0,0,-x])
 ob.channels['forearm'].joint_rotation = mathutils.Vector([0,0,-x])
 ob.update()

 x=x+.01
