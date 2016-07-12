import bpy, socket, math, ast, threading, queue
from enum import Enum

ARM_NAME_PREFIX = 'arm.'
LIGHT_NAME_PREFIX = 'light.'
LIGHT_PWM_MAX = 65535
LIGHT_LUM_MAX = 1.0

ConnState = Enum('ConnState', 'none connecting connected')
class Connection:
  def __init__(self, socket, state=ConnState.none):
    self.socket = socket
    self.state = state

# map from IP address to Connection
sockets = {}
# ip addresses to be connected to and added to sockets dict
sockets_queue = queue.Queue()

# connect to address and store socket in persistent global map
def connect_socket(ip, port = 1337):
  server_address = (ip, port)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(1.0)
  
  print('connecting to', server_address)
  sockets[ip].state = ConnState.connecting
  try:
    sock.connect(server_address)
    print('connected to', server_address)
    sock.sendall(b'speed 50\n')
    sockets[ip].socket = sock
    sockets[ip].state = ConnState.connected
    return sock

  except socket.timeout:
    print('error: connection timed out on', ip)

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

# find the LAMP attached to this arm  
def getLamp(arm):
  for child in arm.children:
    if child.type == 'LAMP':
      return child

# returns robot arm LED intensity in integer units
def pwmFromLuminosity(lum):
    pwm = int(round(abs(lum) / LIGHT_LUM_MAX * LIGHT_PWM_MAX))
    return pwm

def luminosityFromPWM(pwm):
    lum = pwm * LIGHT_LUM_MAX / LIGHT_PWM_MAX
    return lum

# returns a list of arm angles, starting from the base
# units are dynamixel units [200, 824]
def getAngles(arm):
    
  def dynamixel_from_degrees(angle):
    return int(round((angle - 90) * 600.0/180 + 512))
    
  # convert to degrees because they are easier to debug
  rad_to_deg = 180.0/math.pi
  up = arm.pose.bones['base']
  fo = arm.pose.bones['forearm']

  up_q = up.matrix.to_quaternion()
  fo_q = fo.matrix.to_quaternion()
  fo_q.rotate(up_q.inverted())
  
  # TODO get local orientation somehow instead of adding 180 and 90
  up_a = up.matrix.to_euler().x * rad_to_deg + 180
  fo_a = fo_q.to_euler().z * rad_to_deg + 90
  #up_a = 0 if up_a < 0 else up_a
  #print(fo_q.to_euler(), fo_a)

  # convert to dynamixel units
  angles = [dynamixel_from_degrees(a) for a in [up_a, fo_a]]
  #print(angles)
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

def robot_anim_handler(scene):
  # TODO alter serial protocol to use negative IDs
  baseID = 1
  
  # find light arm objects
  for o in bpy.data.objects:
    if o.name.startswith(ARM_NAME_PREFIX):
      ip = o.name[len(ARM_NAME_PREFIX):]
      pwm = pwmFromLuminosity(getLamp(o).data.energy)
      angles = getAngles(o)

      # assemble command string
      s = 's'
      for i in range(len(angles)):
        s += ' ' + str(i+baseID) + ':' + str(angles[i])

      s += '\npwm ' + str(pwm) + '\n'

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

def saveToFile(filepath):
  with open(filepath, 'w') as f:
    arms = {}
    
    for arm in bpy.data.objects:
      if not arm.name.startswith(ARM_NAME_PREFIX): continue
      
      ip = arm.name[len(ARM_NAME_PREFIX):]
      angles = getAngles(arm)
      light = pwmFromLuminosity(getLamp(arm).data.energy)
      
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
      getLamp(arm).data.energy = luminosityFromPWM(pwm)
  
      angles = data['angles']
      # TODO_set angles
  
###################################################################################
#    Menu in toolprops region
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

