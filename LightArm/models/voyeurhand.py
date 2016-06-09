import bpy, socket, math

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
#server_address = ('10.0.0.73', 1337)
server_address = ('127.0.0.1', 20002)
print('connecting to', server_address)
#sock.connect(server_address)

def handler(scene):
  rad_to_deg = 180.0/3.14159
  up = bpy.data.objects['arm.004'].pose.bones['base']
  fo = bpy.data.objects['arm.004'].pose.bones['forearm.001']

  up_q = up.matrix.to_quaternion()
  fo_q = fo.matrix.to_quaternion()
  fo_q.rotate(up.matrix)
  up_a = up_q.to_euler().x * rad_to_deg + 90
  fo_a = fo_q.to_euler().z * rad_to_deg
  #up_a = 0 if up_a < 0 else up_a
  print([up_a, fo_a])
  return

  upperarm = bpy.data.objects['arm.004'].pose.bones["base"]
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

  baseID = 1
  s = 's '
  for i in range(2):
    s += str(i+baseID) + ':' + str(angles[i]) + ' '

  #s += '\npwm ' + str(pwm) + '\n'
  print(s)
  
  try:
    sock.sendall(s)
    print(s.replace('\n', '/'))
  except:
    print('socket error sending')
    bpy.app.handlers.frame_change_post.remove(handler)


bpy.app.handlers.frame_change_post.clear()
bpy.app.handlers.frame_change_post.append(handler)