import bge
from bge import render
import math
from math import *
import mathutils
import serial
import struct

def keydown(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_JUST_ACTIVATED

########################################################################
ucChair = None
ucChair = serial.Serial('/dev/ttyACM0', 9600)
#ucChair = serial.Serial('COM23', 9600)

if ucChair and ucChair.isOpen():
    print('opened ', ucChair.name)
else:
    print("ucChair not opened")

# arguments are letter, integer (signed byte)
def sendChairCmd(cmd, val=0):
    #print(cmd)
    if ucChair == None: return
    ucChair.write(struct.pack('>B', ord(cmd)))
    ucChair.write(struct.pack('>b', val))
    ucChair.write(struct.pack('>B', ord('\n')))

#########################################################################

mousePos = [0, 0]
mouseSensitivity = .05
cos45 = 1/sqrt(2)


# keyboard subroutine for interactive wheelchair movement
# control left and right motors independently, as in controlling a tank
# each motor can move forward or backward
# hit spacebar to stop motors immediately
def k():
    global mousePos
    # heartbeat character sent every frame;
    # uC will stop motion if this is not received after a short amount of time
    sendChairCmd('~')

    # left motor increase/decrease speed
    if keydown(bge.events.EKEY): sendChairCmd('e')
    if keydown(bge.events.DKEY): sendChairCmd('d')
    # right motor increase/decrease speed
    if keydown(bge.events.UKEY): sendChairCmd('u')
    if keydown(bge.events.HKEY): sendChairCmd('h')
    
    # full stop
    if keydown(bge.events.SPACEKEY):
        sendChairCmd(' ')
        print('STOP')
        mousePos = [0, 0]   #reset internal mouse position so that further mouse movement starts at zero
        tmpM = [0, 0]
    
    speed = 40      # = 7 inches per second
    Lbias = .87

    if keydown(bge.events.FKEY):
       sendChairCmd('R', int(speed))
       sendChairCmd('L', int(speed * Lbias))      
    if keydown(bge.events.BKEY):
       sendChairCmd('R', int(-speed))
       sendChairCmd('L', int(-speed * Lbias))      

def 

lastPos = None
lastTime = None

def m(cont):
    global lastPos, lastTime
    ob = cont.owner
    
    if lastPos:
        deltaPos = [
            ob.localPosition.x - lastPos[0],
            ob.localPosition.y - lastPos[1]]
        
        deltaTime = ob.time - lastTime
        
        # convert units to speed
        currentDisp = sqrt(deltaPos[0]**2 + deltaPos[1]**2)
        currentSpeed = currentDisp / deltaTime
        
        
        
        speed = 7  # inches per second
        deltaPos[0] 

    lastPos = ob.localPosition
    lastTime = own.time
 

    #send new motor positions to uC
    sendChairCmd('R', int(motorPos[0]))
    sendChairCmd('L', int(motorPos[1]))