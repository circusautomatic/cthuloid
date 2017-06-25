"""Blender plugin for controlling LightArm (spotlight robots) and static LEDs.

This script registers an Animation Handler routine so that Blender can act as a robot simulation environment.
The routine only runs when Blender is in animation mode (Alt-A). On request, it opens a socket connection to
each robot in the scene. IP address is derived from the name of the robot model in Blender, so model names must 
follow a specific format, or the handler will ignore them. Because displaying errors in Blender is currently 
messy, errors are printed to the console, so you must launch Blender from a terminal to see them.

A LightArm's name must be of the form 'arm.<address>', ex: 'arm.10.0.0.2'
A static LED's name must be of the form 'light.<address>'
Gimbal lights are an experimental alternate spotlight robot.

"""

import bpy, socket, math, ast, threading, queue
from enum import Enum
from mathutils import *

ARM_NAME_PREFIX = 'arm.'
GIMBAL_NAME_PREFIX = 'garm.'
SERVO_SPEED = 200
SERVO_COMPLIANCE = 63
LIGHT_NAME_PREFIX = 'light.'
LIGHT_PWM_MAX = 65535
LIGHT_LUM_MAX = 1.0

################################################################################
# network functionality

ROBOT_PORT = 1337

ConnState = Enum('ConnState', 'none connecting connected')
class Connection:
  def __init__(self, socket, state=ConnState.none):
    self.socket = socket
    self.state = state

# map from IP address to Connection object
sockets = {}
# ip addresses to be connected to and added to sockets dict
sockets_queue = queue.Queue()

# connect to address and store socket in persistent global map
def connect_socket(ip, port = ROBOT_PORT):
  server_address = (ip, port)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(1.0)
  
  print('connecting to', server_address)
  sockets[ip].state = ConnState.connecting
  try:
    sock.connect(server_address)
    print('connected to', server_address)
    sock.sendall(b'speed %d\ncompliance %d\n' % (SERVO_SPEED, SERVO_COMPLIANCE))
    sockets[ip].socket = sock
    sockets[ip].state = ConnState.connected
    return sock

  except socket.timeout:
    print('error: connection timed out on', ip)
  except OSError:
    print('error: network error reaching', ip)

# A singleton thread to manage non-blocking socket connections
class SocketThread(threading.Thread):
  def __init__(self, name):
    self.shouldExit = False
    threading.Thread.__init__(self, name=name, daemon=True)
    self.start()

  def run(self):
    while True:
      if self.shouldExit: return
  
      ip = sockets_queue.get()
      if sockets[ip].state != ConnState.connected:
        connect_socket(ip)
      else:
        print('skipping', ip)
      sockets_queue.task_done()
      
socket_thread = SocketThread('st')

################################################################################
# helpers

# find the LAMP attached to this arm  
def findLamp(arm):
  for child in arm.children:
    if child.type == 'LAMP':
      return child

# returns robot arm LED intensity in integer units
def pwmFromLuminosity(lum):
    pwm = int(round(abs(lum) / LIGHT_LUM_MAX * LIGHT_PWM_MAX))
    return pwm

# returns luminosity in Blender units, range [0.0-1.0]
def luminosityFromPWM(pwm):
    lum = pwm * LIGHT_LUM_MAX / LIGHT_PWM_MAX
    return lum

# converts to dynamixel angle units 
# expects [-135, +135], returns approximately [50, 1000]
def dynamixel_from_degrees(angle):
#  return int(round(angle * 600.0/180 + 512))
  while angle < -135: angle += 360
  while angle > 135:  angle -= 360
  return int(round(angle * 1024.0/300 + 512))

# calculates servo angles for LightArm robot
# returns a list of arm angles, starting from the base
# units are dynamixel units [200, 824]
def getArmAngles(arm):    
  # convert to degrees because they are easier to debug
  rad_to_deg = 180.0/math.pi
  up = arm.pose.bones['base']
  fo = arm.pose.bones['forearm']

  up_q = up.matrix.to_quaternion()
  fo_q = fo.matrix.to_quaternion()
  
  # find the orientation of the forearm relative to the upper arm
  fo_q.rotate(up_q.inverted())
  #print(up_q, fo_q)
  
  # one joint angle is [0,180], the other is [-90,90]
  # convert both to [-90, 90]

  print(up.matrix.to_quaternion())
  #up_a = up.matrix.to_euler().x * rad_to_deg    # up.x in [0,180]
  #fo_a = (fo_q.to_euler().z + 90) * rad_to_deg  # fo.z in [-90,90]
  
  up_a = up.matrix.to_euler().x * rad_to_deg - 90
  fo_a = fo_q.to_euler().z * rad_to_deg
  #print(up_a, fo_a)

  # convert to dynamixel units
  angles = [dynamixel_from_degrees(a) for a in [up_a, fo_a]]
  return angles

  '''upperarm_angles = upperarm.matrix.to_euler()
  forearm_angles = (upperarm.matrix.inverted() * forearm.matrix).to_euler()
  print('upperarm angles:', upperarm_angles)
  print('forearm angles: ', forearm_angles)
  s
  #angles[0] = arm.pose.bones[0].rotation_quaternion.to_euler()[0]
  #angles[1] = arm.pose.bones[1].rotation_quaternion.to_euler()[1]
  
  angles = [x * 600/math.pi + 512 for x in angles]
'''

# calculates servo angles for Gimbal robot 
# returns a list of arm angles, starting from the base
# units are dynamixel units [200, 824]
def getGimbalAngles(gimbal, direction):
  #TODO subtract from  gimbal base or top of first bone
  direction = direction.location - gimbal.location
  
  fo = gimbal.pose.bones['forearm']
  up = gimbal.pose.bones['base']

  fo_a = math.acos(direction.z / direction.length)
  fo_a = min(math.pi/2, fo_a)
  up_a = math.atan2(direction.y, direction.x) + math.pi/2
  #if fo_a < 0: fo_a = 0
  print(up_a, fo_a)
  
  up.rotation_mode = 'XYZ'
  up.rotation_euler = Euler((0, up_a, 0))

  fo.rotation_mode = 'XYZ'
  fo.rotation_euler = Euler((fo_a, 0, 0))

  angles = [dynamixel_from_degrees(a * 180/math.pi) for a in [up_a, fo_a]]
  #print(angles)
  return angles

def assembleLightServoString(angles, pwm):
  baseID = 1
  s = 's'
  
  for i in range(len(angles)):
    s += ' ' + str(i+baseID) + ':' + str(angles[i])

  s += '\npwm ' + str(pwm) + '\n'
  return s

##############################################################################
# animation handler

def robot_anim_handler(scene):
  iktarget = bpy.data.objects['Cube']
  
  # find light arm objects
  for o in bpy.data.objects:
    if o.name.startswith(ARM_NAME_PREFIX):
      ip = o.name[len(ARM_NAME_PREFIX):]
      pwm = pwmFromLuminosity(findLamp(o).data.energy)
      angles = getArmAngles(o)

      # assemble command string
      s = assembleLightServoString(angles, pwm)
      
    elif o.name.startswith(GIMBAL_NAME_PREFIX):
      ip = o.name[len(GIMBAL_NAME_PREFIX):]
      pwm = pwmFromLuminosity(findLamp(o).data.energy)
      angles = getGimbalAngles(o, iktarget)

      # assemble command string
      s = assembleLightServoString(angles, pwm)

    elif o.name.startswith(LIGHT_NAME_PREFIX):
      ip = o.name[len(LIGHT_NAME_PREFIX):]
      pwm = pwmFromLuminosity(o.data.energy)
      
      # assemble command string
      s = 'pwm ' + str(pwm) + '\n'
      
    else: continue
      
    print(s.replace('\n', '_'))
    conn = None
    
    # if this is the first time trying to talk to this device, create an entry
    # and 
    try:
      conn = sockets[ip]
    except KeyError:
      print('not connected; queueing', ip)
      sockets[ip] = Connection(None)
      sockets_queue.put(ip)
    
    if conn and conn.state == ConnState.connected:
      try:
        conn.socket.sendall(bytes(s, 'UTF-8'))
      except (socket.timeout, BrokenPipeError, ConnectionResetError) as e:
        print('lost connection; queueing', ip)
        conn.state = ConnState.none
        sockets_queue.put(ip)

#########################################################################################
# load and save to file, not actually used

def saveToFile(filepath):
  with open(filepath, 'w') as f:
    arms = {}
    
    for arm in bpy.data.objects:
      if not arm.name.startswith(ARM_NAME_PREFIX): continue
      
      ip = arm.name[len(ARM_NAME_PREFIX):]
      angles = getAngles(arm)
      light = pwmFromLuminosity(findLamp(arm).data.energy)
      
      dict = {'angles': angles, 'light': light}
      arms[ip] = dict
      
    text = "{'LightArms': \n  " + str(arms) + "\n}\n"
    f.write(text)
      
def loadFromFile(filepath):
  with open(filepath, 'r') as f:
    text = f.read()
    json = ast.literal_eval(text)
    arms = json['LightArms']
    
    for ip, data in arms.items():
      name = ARM_NAME_PREFIX + ip
      arm = bpy.data.objects[name]
      
      pwm = data['light']
      findLamp(arm).data.energy = luminosityFromPWM(pwm)
  
      angles = data['angles']
      # TODO_set angles
  
###################################################################################
# menu in toolprops region

class RobotPanel(bpy.types.Panel):
    bl_label = "Robot Scene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"
 
    def draw(self, context):
      self.layout.operator("circus.saver", text='Save Robot Positions')
      #self.layout.operator("circus.loader", text='Load Robot Positions')

class CircusSaver(bpy.types.Operator):
    """Export Robot Data"""
    bl_idname = "circus.saver"
    bl_label = "Save the robots"
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        saveToFile(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class CircusLoader(bpy.types.Operator):
    """Export Robot Data"""
    bl_idname = "circus.loader"
    bl_label = "Load the robots"
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        loadFromFile(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#####################################################################################
# main

def unregister():
    bpy.utils.unregister_class(RobotPanel)
          
if __name__ == "__main__":
  # re-register this handler
  bpy.app.handlers.frame_change_post.clear()
  bpy.app.handlers.frame_change_post.append(robot_anim_handler)

  # create menu
  #bpy.utils.register_module(__name__)
  bpy.utils.register_class(RobotPanel)
  bpy.utils.register_class(CircusLoader)
  bpy.utils.register_class(CircusSaver)

