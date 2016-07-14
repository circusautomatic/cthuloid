# script to modify track spot settings in all cue files in scenes/ to make them more amenable to manual control during show

from trackspot import *
import os, ast

spots = [
      TrackSpot(None, 161, 'w', 's', 'a', 'd', 'e', 'q'),
      TrackSpot(None, 170, '8', '5', '6', '4', '9', '7'),
      TrackSpot(None, 193, 'g', 'b', 'v', 'n', 'h', 'f')]

def sanitizeSpots(dmx):
  changed = False
  for spot in spots:
    #if dmx[spot.intensity] == 0 and (dmx[spot.strobe] > 0 or dmx[spot.speed] > 0):
    #  print('file "' + filename + '" has weirdness on spot', spot.firstChannel+1)

    if dmx[spot.intensity] > 0 and (dmx[spot.strobe] != 255 or dmx[spot.speed] != 255):
      print('file "' + filename + '" has weirdness on spot', spot.firstChannel+1)
      changed = True
      dmx[spot.strobe] = 255
      dmx[spot.speed] = 255
      dmx[spot.intensity] = 0

  return changed

def turnOffSideSpots(dmx):
  for spot in spots[0:2]:
    dmx[spot.strobe] = 255
    dmx[spot.speed] = 255
    dmx[spot.intensity] = 0
  
  return True

for filename in os.listdir('scenes'):
#  if not os.path.isfile(filename): continue

  json = dmx = None

  with open('scenes/' + filename, 'r') as f:
#    try:
      text = f.read()
      #print(text)

      json = ast.literal_eval(text)
      dmx = None
      if isinstance(json, list): dmx = json
      elif isinstance(json, dict): dmx = json['DMX']
      else: raise BaseException('parse error')

#  changed = sanitizeSpots(dmx)
  changed = turnOffSideSpots(dmx)

  if changed: 
    with open('scenes/' + filename, 'w') as f:
      if dmx == json:
        f.write(str(dmx))
      else:
        f.write(str(json))
        f.write('\n') 

 #   except BaseException as e:
  #    print('Error reading file: "' + filename + '":', e)

      

