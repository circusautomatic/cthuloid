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
ucChair = serial.Serial('/dev/ttyACM3', 9600)
#ucChair = serial.Serial('COM23', 9600)

if ucChair and ucChair.isOpen():
    print('opened ', ucChair.name)
else:
    print("ucChair not opened")

# arguments are letter, integer (signed byte)
def sendChairCmd(cmd, val=0):
    if ucChair == None: return
    if cmd != '~' :print(cmd)
    ucChair.write(struct.pack('>B', ord(cmd)))
    #ucChair.write(struct.pack('>b', val))
    #ucChair.write(struct.pack('>B', ord('\n')))

#########################################################################

mousePos = [0, 0]
mouseSensitivity = .05
cos45 = 1/sqrt(2)

centerY = render.getWindowHeight()//2
centerX = render.getWindowWidth()//2

# move mouse cursor to center
render.setMousePosition(centerX, centerY)

# keyboard subroutine for interactive wheelchair movement
# control left and right motors independently, as in controlling a tank
# each motor can move forward or backward
# hit spacebar to stop motors immediately
def k(cont):
    global mousePos
    # heartbeat character sent every frame;
    # uC will stop motion if this is not received after a short amount of time
    sendChairCmd('~')

    # left motor increase/decrease speed
    if keydown(bge.events.UKEY): sendChairCmd('L')
    if keydown(bge.events.HKEY): sendChairCmd('l')
    # right motor increase/decrease speed
    if keydown(bge.events.EKEY): sendChairCmd('R')
    if keydown(bge.events.DKEY): sendChairCmd('r')
    
    # full stop
    if keydown(bge.events.SPACEKEY):
        sendChairCmd(' ')
        print('STOP')
        mousePos = [0, 0]   #reset internal mouse position so that further mouse movement starts at zero
        #tmpM = [0, 0]
    
    """speed = 40      # = 7 inches per second
    Lbias = .87

    if keydown(bge.events.FKEY):
       sendChairCmd('R', int(speed))
       sendChairCmd('L', int(speed * Lbias))      
    if keydown(bge.events.BKEY):
       sendChairCmd('R', int(-speed))
       sendChairCmd('L', int(-speed * Lbias))"""

# mouse tracking subroutine for interactive wheelchair movement
# This routine maps mouse position to wheelchair velocity, which was the simplest way I could think of
#  to control the chair. I believe mapping the mouse position to the chair position would require
#  mathematical integration plus some planning, as the chair can only move forward and back.
#
# Moving the mouse forward from the starting location increases forward speed.
# Moving backward from starting location increases backward speed.
# Moving left or right of the starting location makes the char spin in place (?)
# All other mouse positions are interpolations of the above, ex: forward-right makes a left turn
#  (can invert this easily).
# 
# Use spacebar to stop. 
# TODO test mouse after hitting spacebar
def m(cont):
    global mousePos, mouseSensitivity
    ob = cont.owner
    mouse = cont.sensors["Mouse"]
    
    # calculate the amount mouse cursor moved from the center since last frame
    mouseDelta = [
        (mouse.position[0] - centerX) * mouseSensitivity,
        (centerY - mouse.position[1]) * mouseSensitivity]

    # move mouse cursor back to center
    render.setMousePosition(centerX, centerY)

    # update our secret internal mouse position
    mousePos[0] += mouseDelta[0]
    mousePos[1] += mouseDelta[1]

    # move cube onscreen
    ob.localPosition.x = mousePos[0]
    ob.localPosition.y = mousePos[1]

    # rotate 45 degrees to convert to motor impulses
    motorPos = [
        -mousePos[0]*cos45 + mousePos[1]*cos45,
        (mousePos[0]*cos45 + mousePos[1]*cos45),
    ]

    print(mousePos)

    # send new motor positions to uC
    # NO LONGER SUPPORTED
    #sendChairCmd('R', int(motorPos[0]))
    #sendChairCmd('L', int(motorPos[1]))