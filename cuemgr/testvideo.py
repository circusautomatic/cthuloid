import paramiko
address = '192.168.1.115'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(address, username='pi', password='raspberry')

filename = 'omxplayer --loop --orientation 180 ' + '~/cthuloid/ghettopticon/blender/prinboo-talking.mp4'

stdin, stdout, stderr = ssh.exec_command(filename)

