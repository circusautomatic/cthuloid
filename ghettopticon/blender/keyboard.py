import bge
import math
from math import *
import mathutils
import serial
import struct

def keydown(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_ACTIVE

ob = bge.logic.getCurrentController().owner

#####################################################################################
# simple way to keep a global dict of all microcontrollers,
# and to identify microcontrollers by their vender and product ID
UCs = {}
bge.logic.globalDict['UCs'] = UCs

import serial.tools.list_ports
baud = 9600
ucNamesToBoardIDs = {
    'chair':    'USB VID:PID=2341:0042',
    'servos':   'USB VID:PID=2A03:0043',
}
"""
for p in serial.tools.list_ports.comports():
    print(p)
    devPath = p[0]

    # find each serial device named in ucNamesToBoardIDs, open it, and save it in UCs under its assigned name
    for name, boardID in ucNamesToBoardIDs.items():
        if p[2].startswith(boardID):
            s = serial.Serial(devPath, baud)
            if s and s.isOpen():
                print(name, 'opened on path:', s.name)
                UCs[name] = s
            else:
                print('ERROR: ', name, 'failed to open on path:', devPath)
"""

s = serial.Serial('/dev/ttyACM0', baud)
if s and s.isOpen(): print('opened', s.name)
else: print('error opening servos')
UCs['servos'] = s

def getUC(name):
    UCs = bge.logic.globalDict['UCs']
    if name not in UCs: return None
    return UCs[name]


# arguments are letter, integer (signed byte)
def sendChairCmd(cmd, val=0):
    #print(cmd)
    ucChair = getUC('chair')
    if not ucChair: return
    ucChair.write(struct.pack('>B', ord(cmd)))
    ucChair.write(struct.pack('>b', val))
    ucChair.write(struct.pack('>B', ord('\n')))
                
                
Inc = .01
Servos = {}
v = 1.1071487665176392

class Servo:
    """
    - id is the servo ID for the uC
    - name is the blender bone name
    Angles are stored in blender space, in radians.
    Servos accept degrees.
    TODO clarify types of transformations between blender and servo space.
    """
    def __init__(self, id, name, axis, initial, min, max, servoNegate=False, servoFlip=False):
        self.id = id
        self.name = name
        self.axis = axis
        self.pos = initial
        self.min = min
        self.max = max
        self.servoNegate = servoNegate
        self.servoFlip = servoFlip
    
    def new(id, name, axis, initial, min, max, servoNegate=False, servoFlip=False):
        s = Servo(id, name, axis, initial, min, max, servoNegate, servoFlip)
        Servos[name] = s
    
    def increment(self, inc, updateBlender=True):
        self.move(self.pos + inc, updateBlender)
        
    def move(self, pos, updateBlender=True):
        pos = min(pos, self.max)
        pos = max(pos, self.min)
        
        #changed = self.pos != pos
        self.pos = pos
        #print(self.name, self.pos)
        #if changed: self.arduinoWrite()
        self.arduinoWrite()
        
        if not updateBlender: return
        
        axis = self.axis
        if   (axis == 'x'): v = mathutils.Vector((pos, 0, 0))
        elif (axis == 'y'): v = mathutils.Vector((0, pos, 0))
        elif (axis == 'z'): v = mathutils.Vector((0, 0, pos))
        
        ob.channels[self.name].joint_rotation = v
        ob.update()
        return pos

    def arduinoWrite(self):
        
        radians = self.pos
        if self.name == 'shoulder.L': radians += pi/2 - v
        if self.name == 'shoulder.R': radians += -(pi/2 - v)
        
        degrees = int(radians * 180/pi)
        #print(self.name, ': ', degrees, ' degrees in blender space', sep='')
        
        if self.servoNegate: degrees = -degrees
        if self.servoFlip: degrees = 180 - degrees
        
        #print(self.name, ':', degrees, ' degrees in Servo space', sep='')
        
        arduino = getUC('servos')
        if not arduino: 
            print('ERROR servos arduino no found')
            return
        arduino.write(struct.pack('>B', self.id))
        arduino.write(struct.pack('>B', degrees))
        arduino.write(struct.pack('>B', ord('\n')))

def incrementBone(name, inc):
    servo = Servos[name]
    servo.increment(inc)

##############################################################################
# servo joint definitions

#left arm fully extended = 180
#right arm fully extended = 0

#Left Arm
Servo.new(0,    'shoulder.L',      'y',    .4*pi,   0,      pi,      servoFlip=True)
Servo.new(1,    'upperarm.L',      'x',    0,      0,      pi)#,     servoNegate=True)
Servo.new(2,    'forearm.L',       'x',    0,      0,      pi,     servoFlip=True)
Servo.new(3,    'hand.L',          'y',    0,      0,      pi)#,     servoFlip=True)

#Right Arm
Servo.new(4,    'shoulder.R',      'y',    -.4*pi,  -pi,    0,      servoNegate=True)
Servo.new(5,    'upperarm.R',      'x',    0,      -pi,    0,      servoFlip=True, servoNegate=True)
Servo.new(6,    'forearm.R',       'x',    0,      0,      pi)
Servo.new(7,    'hand.R',          'y',    0,      0,      pi)#,     servoFlip=True)

#Head
Servo.new(8,    'neck',            'y',    0,      -pi,     0,      servoNegate=True)
Servo.new(9,    'nod',             'z',    0,      0,       pi)
Servo.new(10,   'face',            'y',    0,      0,       pi)

# set initial positions in blender space
for name, servo in Servos.items(): servo.increment(0)

def voyeur(cont):
    #print('----------voyeur------------')
    ob = cont.owner
    
    for name, servo in Servos.items():
        angle = getattr(ob.channels[servo.name].joint_rotation, servo.axis)
        #print(name, '\t', angle)
        servo.move(angle, False)

def k():
#Left Arm
    if keydown(bge.events.ONEKEY): angle = incrementBone('shoulder.L', Inc)
    if keydown(bge.events.TWOKEY): angle = incrementBone('shoulder.L', -Inc)

    if keydown(bge.events.QKEY): angle = incrementBone('upperarm.L', Inc)
    if keydown(bge.events.WKEY): angle = incrementBone('upperarm.L', -Inc)
        
    if keydown(bge.events.AKEY): angle = incrementBone('forearm.L', Inc)
    if keydown(bge.events.SKEY): angle = incrementBone('forearm.L', -Inc)

    if keydown(bge.events.ZKEY): angle = incrementBone('hand.L', Inc)
    if keydown(bge.events.XKEY): angle = incrementBone('hand.L', -Inc)
#Right Arm
    if keydown(bge.events.NINEKEY): angle = incrementBone('shoulder.R', Inc)
    if keydown(bge.events.ZEROKEY): angle = incrementBone('shoulder.R', -Inc)

    if keydown(bge.events.IKEY): angle = incrementBone('upperarm.R', Inc)
    if keydown(bge.events.OKEY): angle = incrementBone('upperarm.R', -Inc)
        
    if keydown(bge.events.JKEY): angle = incrementBone('forearm.R', Inc)
    if keydown(bge.events.KKEY): angle = incrementBone('forearm.R', -Inc)

    if keydown(bge.events.NKEY): angle = incrementBone('hand.R', Inc)
    if keydown(bge.events.MKEY): angle = incrementBone('hand.R', -Inc)
#Head
    if keydown(bge.events.THREEKEY): angle = incrementBone('neck', -Inc)
    if keydown(bge.events.FOURKEY): angle = incrementBone('neck', Inc)

    if keydown(bge.events.FIVEKEY): angle = incrementBone('nod', Inc)
    if keydown(bge.events.SIXKEY): angle = incrementBone('nod', -Inc)
        
    if keydown(bge.events.SEVENKEY): angle = incrementBone('face', Inc)
    if keydown(bge.events.EIGHTKEY): angle = incrementBone('face', -Inc)

