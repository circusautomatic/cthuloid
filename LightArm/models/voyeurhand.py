import bpy, socket, math

# Create a TCP/IP socket
server_address = ('10.0.0.77', 1337)
#server_address = ('127.0.0.1', 10001)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2.0)

def handler(scene):
  pwmScale 
  pwm = 10
  baseID = 1
  angles = []
  
  pwm = bpy.data.objects['Point'].data.energy
  pwm = int(round(abs(pwm) / 100.0 * 255))

  rad_to_deg = 180.0/math.pi
  up = bpy.data.objects['arm.004'].pose.bones['base']
  fo = bpy.data.objects['arm.004'].pose.bones['forearm.001']

  up_q = up.matrix.to_quaternion()
  fo_q = fo.matrix.to_quaternion()
  fo_q.rotate(up.matrix)
  up_a = up_q.to_euler().x * rad_to_deg + 180
  fo_a = (fo_q.to_euler().z * rad_to_deg + 90) % 180
  #up_a = 0 if up_a < 0 else up_a
  angles = [up_a, fo_a]
  #print(angles)

  '''upperarm = bpy.data.objects['arm.004'].pose.bones["base"]
  forearm = bpy.data.objects['arm.004'].pose.bones["forearm.001"]
  
  upperarm_angles = upperarm.matrix.to_euler()
  forearm_angles = (upperarm.matrix.inverted() * forearm.matrix).to_euler()
  print('upperarm angles:', upperarm_angles)
  print('forearm angles: ', forearm_angles)
  
  return

  #get angles and light intensity
  pwm = 200
  angles = [0, 0]
  
  arm = bpy.data.objects[0]
  
  # print euler angles to terminal
  print(bpy.data.objects['Cube.002'].rotation_euler)
  print(bpy.data.objects['Cube.001'].rotation_euler)
  return
  
  #angles[0] = arm.pose.bones[0].rotation_quaternion.to_euler()[0]
  #angles[1] = arm.pose.bones[1].rotation_quaternion.to_euler()[1]
  
  angles = [x * 600/math.pi + 512 for x in angles]
'''
  s = 's '
  for i in range(len(angles)):
    angle = (angles[i] - 90) * 600.0/180 + 512
    s += str(i+baseID) + ':' + str(int(round(angle))) + ' '

  s += '\npwm ' + str(pwm) + '\n'
  print(s)
  
  #try:
  sock.sendall(bytes(s, 'UTF-8'))
  #print(s.replace('\n', '/'))
  #except :
  #  print('socket error sending')
  #  bpy.app.handlers.frame_change_post.remove(handler)

try:
    print('connecting to', server_address)
    sock.connect(server_address)
    sock.sendall(b'speed 50\n')

    bpy.app.handlers.frame_change_post.clear()
    bpy.app.handlers.frame_change_post.append(handler)

    print('connected?')
except socket.timeout:
    print('error: connected timed out')

