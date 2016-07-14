import bge
from bge import render
import math
from math import *
import mathutils
import serial
import struct
import threading
import time

def keypressed(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_JUST_ACTIVATED

########################################################################
import ola
from ola.ClientWrapper import ClientWrapper

# Holds an array of 512 DMX channels.
# Channels go from 0-511 and have value 0-255.
# OLA can't individually address DMX channels, so this class only
# invokes the DMX subsystem if there has been a change
# To use, call set() on individual channels and then call send().
class DmxChannels:
    def __init__(self):
        self.data = bytearray(512)
        self.dataChanged = False
        self.client = None
        try:
            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
        except:
            print("Error: couldn't connect to OLA server")
            
    def len():
        return len(self.data);

    def get():
        return list(self.data)
    
    # sends to OLA if there has been a change    
    def send(self):
        if not self.client or not self.dataChanged: return
        self.dataChanged = False
        self.client.SendDmx(1, self.data)
        
    # pass a start channel and any number of channel values
    # values are integers 0-255
    # you must call send to transmit the changes
    def set(self, channel, *values):
        #print('DMX.set channel', index, '=', values)
        for v in values:
            if self.data[channel] != v:
                self.data[channel] = v
                self.dataChanged = True
                channel += 1
                
    # pass a start channel and any number of channel values
    # values are numbers between 0 and 1
    # you must call send to transmit the changes
    def setFraction(self, channel, *values):
        intValues = tuple(int(255*v) for v in values)
        self.set(channel, *intValues)

    # sets all channels to 0 and transmits
    def off(self):
        for i in range(len(self.data)):
            self.data[i] = 0
        self.dataChanged = True
        self.send()

    # convenience to set and transmit a list of values starting at channel 0
    def setAndSend(*values):
        i = 0
        for v in values:
            self.set(i, v)
            i += 1
        self.send()

DMX = DmxChannels()

########################################################################
# serial methods

def openSerial(path, baud=38400):
    uc = None
    try:
        uc = serial.Serial(path, baud)
    except:
        pass

    if uc and uc.isOpen():
        print('opened', uc.name)
        #print(uc.readline())
        #uc.write(b'plevel silent\n')
    else:
        print('Error:', path, 'not opened')

    return uc

class SerialThread (threading.Thread):
    def __init__(self, path, baud=38400, timeout=50):
        self.uc = None
        self.shouldExit = False
        try:
            # don't bother doing any other initialization if we can't open the port
            self.uc = serial.Serial(path, baud)
            self.lock = threading.Lock()
            threading.Thread.__init__(self)
            self.start()
        except:
            pass

        if self.uc and self.uc.isOpen():
            print('opened', self.uc.name)
        else:
            print('Error:', path, 'not opened')
            
    def valid(self):
        return self.uc and not self.shouldExit
        
    def exit(self):
        self.shouldExit = True
    
    def write(self, data):
        if not self.valid(): return
        self.lock.acquire()
        self.uc.write(data)
        self.lock.release()

    # override this
    def handleLine(self, line):
        print('override me!', line)

    def run(self):
        b = bytearray()
        
        while self.valid():
            #print('run')
            time.sleep(.01)
            self.lock.acquire()
            num = self.uc.inWaiting()
            if num:
                b += self.uc.read(num)
                #print(len(b))
            self.lock.release()
            
            #TODO find all newlines
            ixNewline = b.find(b'\n')
            while ixNewline != -1:
                v = b[:ixNewline].decode("utf-8")
                self.handleLine(v)
                b = b[ixNewline+1:]
                ixNewline = b.find(b'\n')
                
        if self.uc:
            self.uc.close()
            self.uc = None

########################################################################
# LED controller
class LEDs(SerialThread):
    def __init__(self, path):
        SerialThread.__init__(self, path)        
    
    def handleLine(self, line):
        print(line)

ucLEDs = LEDs('/dev/led')

# arguments are PWM values 0-255
def setLEDs(*values):
    cmd = 'pwm'
    for v in values:
        cmd += ' ' + str(v)

    cmd += '\n'
    #print(cmd)
    ucLEDs.write(str.encode(cmd))

def setOneLEDInvFrac(intensity):
    # board takes intensity inverted
    chan1 = int(255 * (1.0 - intensity))
    setLEDs(chan1)
    
########################################################################
# dynamixel servos
class Servos(SerialThread):
    def __init__(self, path):
        SerialThread.__init__(self, path)
        self.mode = None
        self.numLinesToFollow = 0
        self.anglesDict = {}
    
    def handleLine(self, line):
        # read the positions of all servos, which is spread over multiple lines
        # expect the next some number of lines to be servo info
        if line.startswith('Servo Readings:'):
            self.numLinesToFollow = int(line[15:])
            self.mode = 'r'
            self.anglesDict = {}
            print('expecting', self.numLinesToFollow, 'servo readings')

        # information about a single servo, on a single line
        elif self.mode == 'r':
            id, pos = None, None
            for pair in line.split():
                kv = pair.split(':')
                key = kv[0]
                if   key == 'ID':  id = int(kv[1])
                elif key == 'pos': pos = int(kv[1])
            self.anglesDict[id] = pos
            self.numLinesToFollow -= 1
            
            # done, reset mode
            if self.numLinesToFollow == 0:
                print(self.anglesDict)
                self.mode = None
                
        else: print(line)

numServos = 32
ucServos = Servos('/dev/arbotix')

# argument is a dictionary of id:angle
# angles are 0-1023; center is 512; safe angle range is 200-824
def setServoPos(anglesDict, binary=False):
    if not ucServos.valid(): return

    # send a text command which says to expect a block of binary
    # then send the angles as an array of 16-bit ints in order
    # angle is set to 0 for missing IDs
    if binary:
        maxID = 0  # IDs start at 1, so numAngles = highest ID
        for id,angle in anglesDict.items(): 
            maxID = max(maxID, id)

        cmd = 'B ' + str(maxID) + '\n'
        #print(cmd)
        ucServos.write(str.encode(cmd))

        buf = bytearray()
        for id in range(1, maxID+1):
            angle = 0
            if id in anglesDict: angle = anglesDict[id]
            
            # 16-bit little endian
            buf += struct.pack('<H', angle)
        
        print(buf)
        ucServos.write(buf)

    # text protocol of id:angle pairs
    else:
        cmd = 's'
        for id,angle in anglesDict.items():
            cmd += ' ' + str(id) + ':' + str(angle)

        cmd += '\n'
        #print(cmd)
        ucServos.write(str.encode(cmd))

def moveAllServos(pos, binary=False):
    anglesDict = {}
    for i in range(numServos):
        anglesDict[i+1] = pos
    setServoPos(anglesDict, binary)

def readServos():
    ucServos.write(b'r\n')

#########################################################################
def monitorScene():
    scene = bge.logic.getCurrentScene()

    for o in scene.lights:
        if o.name.startswith('Spot'):
            #grab starting channel number from name
            channel = int(o.name[4:])
            intensity = o.energy
            rgb = o.color

            DMX.setFraction(channel, intensity, *rgb)#, 255)
            DMX.send()
            setOneLEDInvFrac(intensity)
            
        """elif o.name.startswith('LED'):
            channel = int(o.name[3:])
            intensity = o.energy
            setOneLEDInvFrac(channel, intensity)"""

    
    anglesDict = {}
    for o in scene.objects:
        if o.name.startswith('Servo'):
            id = int(o.name[5:])
            #radians = o.rotation.x
            #servoUnits = map(radians, -pi, pi, 200, 824)
            #anglesDict[id] = servoUnits
            pass

def k(cont):
    """try:
        print('reading')
        #reading = ucLEDs.readline()
        print(reading)
        print(read.decode())
    except:
        print('nothing to read')"""
    
    #ob = cont.owner
    #setOneLEDInvFrac(ob.energy)
    #d = bge.logic.getCurrentScene().lights
    #for i in d: print(i.energy)
    if keypressed(bge.events.ZKEY):
        DMX.off()
        ucLEDs.exit()
        ucServos.exit()
        bge.logic.endGame()
        return  #don't do anything else this frame!

    if keypressed(bge.events.RKEY):
        ucServos.readServos()
    if keypressed(bge.events.QKEY):
        moveAllServos(512)
        bge.logic.getCurrentScene().lights['Spot0'].energy = 0.0
        bge.logic.getCurrentScene().lights['Spot0'].color = [0, 0, 0]
    if keypressed(bge.events.WKEY):
        moveAllServos(400)
        bge.logic.getCurrentScene().lights['Spot0'].energy = 0.5
        bge.logic.getCurrentScene().lights['Spot0'].color = [0, 1.0, 0]
    if keypressed(bge.events.EKEY):
        moveAllServos(300)
        bge.logic.getCurrentScene().lights['Spot0'].energy = 1.0
        bge.logic.getCurrentScene().lights['Spot0'].color = [0, 0, 1.0]
        
    monitorScene()

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
