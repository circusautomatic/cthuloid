"""
Defines types of cues (sets of hardware parameters), and provides for loading and saving them.

We unfortunately use the word 'cue' in two different ways:
1. A cue is a text file containing hardware parameters in json. Note that cues may also be grouped together
   into a sequence, which is itself treated as a cue.
2. A cue is an instruction to transition to a new set of hardware parameters, either by setting them
   instantaneously or by incrementally fading from the previous parameters. An instruction is a one-word
   command followed by the name of the file that holds the hardware parameters



"""

import sys, os, threading, ast, time, subprocess, random
from console import *

try:
  import prinboo
  Prinboo = prinboo.Prinboo('92.168.42.152')
except ImportError:
  Prinboo = None
  print('No Prinboo')

try:
  import lightarm
  Arms = lightarm.LightArms()
except:
  Arms = None
  print('No LightArms')

try:
  import dmx
  DMX = dmx.DmxChannels()
except ImportError:
  DMX = None
  print('No DMX')

#########################################################################################################
# helpers

def openCueFile(filenameOnly, mode='r'):
  return open('scenes/' + filenameOnly, mode)

def restAfterWord(word, line):
  return line[line.find(word) + len(word):].strip()

def frange(start, end=None, inc=None):
    "A range function which does accept float increments..."

    if end == None:
        end = start + 0.0
        start = 0.0
    else: start = float(start)

    if inc == None:
        inc = 1.0

    count = int((end - start) / inc)
    if start + count * inc != end:
        # need to adjust the count.
        # AFAIKT, it always comes up one short.
        count += 1

    L = [None,] * count
    for i in range(count):
        L[i] = start + i * inc

    return L

def loadCueFile(filenameOnly):
  """return a dictionary of DMX, LED channels, and Servo angles"""
  with openCueFile(filenameOnly) as f:
    text = f.read()

    json = ast.literal_eval(text)
    #print(json)
    return json

    # TODO check version
    #if json['version'] == 0:

##############################################################################################
# cue commands

class Cue:
  """Base class. Initialization, loading, and running may happen at different times."""
  def __init__(self, line):
    self.line = line
  def load(self):
    pass
  def run(self, immediate=False):
    print('empty cue')


class CueSequence(Cue):
  """A list of cues that waits for the previous cue to finish before executing the next"""
  def __init__(self, line):
    Cue.__init__(self, line)
    self.cues = []
  def add(self, cue):
    self.cues.append(cue)
  def run(self, immediate=False):
    for cue in self.cues:
      print ('-', cue.line.strip())
      cue.run()


# load scene from local file
class CueLoad(Cue):
  """Loads a cue from file and executes, broken into multiple steps"""

  def __init__(self, line):
    Cue.__init__(self, line)

    tokens = line.split()
    if len(tokens) < 2:
      raise BaseException('no filename')

    self.filename = restAfterWord(tokens[0], line)

    # load the file to syntax check it, so we can report an error at beginning
    # instead of during a run through
    self.load()

  def load(self):
      data = loadCueFile(self.filename)

      self.targetDMX = None
      if DMX and 'DMX' in data and data['DMX']:
        self.targetDMX = data['DMX']
        if not isinstance(self.targetDMX, list) or not isinstance(sum(self.targetDMX), int):
          raise BaseException('error in DMX portion of cue file')

      self.limbs = Prinboo.limbs and data.get('Limbs')
      self.armData = Arms and data.get('LightArm')

  def run(self, immediate=False):
      # load the file again in case it has changed since the cuesheet was loading
      self.load()

      if self.targetDMX:
        DMX.setAndSend(0, self.targetDMX)

      if self.limbs: #TODO figure out if we have a pose or an animation
        Prinboo.limbs.setAngle(self.limbs)

      if self.armData:
        Arms.load(self.armData)

class CueFade(CueLoad):
  """Fades from current scene to new scene.

  Blocks during run() for the duration of the fade.
  TODO: fix that fading can only be done for either DMX or LightArms.

  usage:
  fade <optional time in seconds> <filename>
  """

  def __init__(self, line):
    Cue.__init__(self, line)    # ignore CueLoad's constructor so we can parse differently

    tokens = line.split()
    if len(tokens) < 2:
      raise BaseException('usage: fade <optional time in seconds> <filename>')

    try:
      tok = tokens[1]
      self.period = float(tok)
      self.filename = restAfterWord(tok, line)
    except:
      self.period = 5.0
      self.filename = restAfterWord(tokens[0], line)

    # load the file to syntax check it, so we can report an error at beginning
    # instead of during a run through
    self.load()

  # TODO make this code not block
  def run(self, immediate=False):
    #try:
      # load the file again in case it has changed since the cuesheet was loading
      self.load()

      timestep = .05
      printPeriodPeriod = .25
      printPeriodTimestepCount = printPeriodPeriod / timestep

      # Light Arms - may be absent
      # TODO fade light arms!
      try:
        if self.armData: Arms.load(self.armData)
      except:
        pass

      # DMX
      if self.targetDMX:
        target = self.targetDMX
        current = DMX.get()
        vel = [0] * len(current)

        # calculate delta for each timestep
        # -1 means don't change
        for i in range(len(target)):
          if target[i] >= 0:
            vel[i] = (target[i] - current[i]) * (timestep / self.period)

        print('                 fading for', self.period, 'seconds..', end='', flush=True)
        startTime = time.time()
        endTime = startTime + self.period
        nextTime = startTime + timestep

        while 1:
          # calculate new channel values and transmit
          for i in range(len(current)): current[i] += vel[i]
          channels = [round(x) for x in current]
          DMX.setAndSend(0, channels)

          now = time.time()

          # print a period every so often
          if now >= nextPrintTime:
            print('.', end='', flush=True)
            nextPrintTime += printPeriodPeriod

          if now > endTime: break
          nexTime += timestep
          time.sleep(nextTime - time.time())

        # make sure we arrive at the target numbers, as rounding error may creep in
        DMX.setAndSend(0, target)
        print('DONE')
    #except:
    #  raise BaseException('Error talking to OLA DMX server')
    # TODO other exceptions having to do with the fade math

# blocking code for fading arm light intensities
#      if self.armData:
#        target = [0] * Arms.num()
#        current = [0] * Arms.num()
#        vel = [0] * Arms.num()
#
#        # map each address to an index
#        for address, data in self.armData.items():
#          i = Arms.arms.index(Arms.findArm(address))
#          target[i] = data.get('intensity', 0)
#
#        for i in range(Arms.num()):
#          current[i] = Arms.getLED(i)
#
#        # calculate delta for each timestep
#        # -1 means don't change
#        for i in range(len(target)):
#          if target[i] >= 0:
#            vel[i] = (target[i] - current[i]) * (timestep / self.period)
#
#        print('                 fading for', self.period, 'seconds..', end='', flush=True)
#        startTime = time.time()
#        endTime = startTime + self.period
#        nextTime = startTime + timestep
#        nextPrintTime = startTime + printPeriodPeriod
#
#        while 1:
#          # calculate new channel values and transmit
#          for i in range(len(current)):
#            current[i] += vel[i]
#            Arms.setLED(i, current[i])
#
#          now = time.time()
#
#          # print a period every so often
#          if now >= nextPrintTime:
#            print('.', end='', flush=True)
#            nextPrintTime += printPeriodPeriod
#
#          if now > endTime: break
#          nextTime += timestep
#          time.sleep(nextTime - time.time())
#
#        # make sure we arrive at the target numbers, as rounding error may creep in
#        Arms.load(self.armData)


class CuePrinboo(CueLoad):
  """Launches a thread to animate Prinboo's head and limbs with frames defined in a cuefile

  """
  framerate = 30 #per second

  def __init__(self, line):
    self.frames = None
    CueLoad.__init__(self, line)

#  def load(self):
#    self.frames = data['limbs']
#    #self.framerate = data['framerate']

  def run(self, immediate=False):
      # load the file again in case it has changed since the cuesheet was loading
      self.load()

      timestep = 1. / self.framerate
      vel = 1

      # Signal the previous thread to exit, and hand it to the next thread
      # so it can wait.
      if Prinboo.limbsThread:
        Prinboo.limbsThread.exit()
      Prinboo.limbsThread = PrinbooLimbsThread(Prinboo.limbsThread, self.limbs, vel, timestep)



class PrinbooLimbsThread(threading.Thread):
    # vel can only be integers until we save our own angles in a list
    def __init__(self, prevThread, poses, vel=1, timestep=.0333):
        self.prevThread = prevThread
        if isinstance(poses, dict): poses = [poses] # convert one frame into a list of frames
        self.poses = poses
        self.vel = 5#vel
        self.timestep = .05#timestep

        self.shouldExit = False
        threading.Thread.__init__(self)

        self.start()

    def exit(self):
        self.shouldExit = True

    def run(self):
        # wait for previous thread to finish writing to the limbs socket
        if self.prevThread:
          while self.prevThread.isAlive():
             time.sleep(.01)

        startTime = time.time()
        #endTime = startTime + self.period
        nextTime = startTime + self.timestep

        NumIds = 2

        def popRandom(li):
          i = random.randint(0, len(li)-1)
          x = li.pop(i)
          return x

        def nextPose():
            if not self.poses: return None, None, None
            pose = self.poses.pop(0)
            allIds = [id for id, target in pose.items()]
            # TODO hack to remove servos that are broken or whose motion isn't visible
            allIds.remove(5); allIds.remove(11)
            ids = []
            # pick two ids
            for i in range(NumIds): ids.append(popRandom(allIds))
#            print('pose:', pose)
            return pose, allIds, ids

        pose, allIds, ids = nextPose()

        while not self.shouldExit:
              #if numInRow == 0: inc = self.vel * random.randint(1, 5)
              #numInRow = (numInRow + 1) % 5

              if not ids and not allIds:
                if not self.poses:
#                    print('exiting')
                    return
#                print('pose:', pose)
                pose, allIds, ids = nextPose()

              while len(ids) < NumIds and allIds:
                ids.append(popRandom(allIds))

              #print(ids)
              for id in ids:
                target = pose[id]
                cur = Prinboo.limbs.getAngle(id)
                diff = target - cur
                if abs(diff) >= 1:
                  inc = self.vel if diff > 0 else -self.vel
                  if abs(inc) > abs(diff): inc = diff          # don't overshoot
                  Prinboo.limbs.setAngle(id, cur + inc)
                else:
#                  print('removing id', id)
                  ids.remove(id) # might mess with for loop

              # wait an amount based on when the next movement should occur
              now = time.time()
              nextTime += self.timestep
              delta = nextTime - now
              if delta > 0: time.sleep(delta) # we might be late enough that the next step has arrived
#        print('exiting')
#    def run(self):
#        # wait for previous thread to finish writing to the limbs socket
#        if self.prevThread:
#          while self.prevThread.isAlive():
#             time.sleep(.01)
#
#        startTime = time.time()
#        #endTime = startTime + self.period
#        nextTime = startTime + self.timestep
#
#        ids = [id for id, target in self.pose.items()]
#
#        done = False
#        while not self.shouldExit and ids:
#          id = ids[random.randint(0, len(ids)-1)]
#
#          #if numInRow == 0: inc = self.vel * random.randint(1, 5)
#          #numInRow = (numInRow + 1) % 5
#
#          target = self.pose[id]
#          cur = Prinboo.limbs.getAngle(id)
#          diff = target - cur
#          if abs(diff) >= 1:
#            inc = self.vel if diff > 0 else -self.vel
#            if abs(inc) > abs(diff): inc = diff          # don't overshoot
#            Prinboo.limbs.setAngle(id, cur + inc)
#          else:
#            ids.remove(id)
#
#          now = time.time()
#          #if now > endTime: break
#          nextTime += self.timestep
#          time.sleep(nextTime - time.time())


class CueVideo(CueLoad):
  """Play a video by running a shell command"""

  player = "/usr/bin/omxplayer"

  def __init__(self, line):
    CueLoad.__init__(self, line)
  def load(self):
    pass #maybe check file exists
  def run(self, immediate=False):
    #subprocess.call([self.player, self.filename])
    Prinboo.screen.play(self.filename)

def cmdCue(line, CueClass):
  """instantiate a type of cue and run it immediately"""
  try:
    cue = CueClass(line)
    cue.run()
  except OSError as e:
    print(e)
    getchMsg()


def cmdSave(tokens, line):
  """save the current parameters in a cue file"""
  if len(tokens) < 2:
    raise BaseException('no filename')

  filename = restAfterWord(tokens[0], line)
  dmx = 'None' #str(DMX.get())
  #arms = str(Arms)
  angles = str(Prinboo.limbs)
  text = "{\n 'version': 0,\n 'DMX': " + dmx + ",\n 'Limbs': " + angles + "\n}"
  #text = "{\n 'version': 0,\n 'DMX': " + dmx + ",\n 'LightArm': {\n  'Servos': " + str(ucServos) + ",\n  'LEDs': " + str(ucLEDs) + "\n }\n}"
  #text = "{'version': 0, 'DMX': " + dmx + ", 'LightArm': {'Servos': " + str(ucServos) + ", 'LEDs': " + str(ucLEDs) + "}}"

  print(text)
  try:
    with openCueFile(filename, 'w') as f:
      f.write(text)
      f.write('\n')
  except OSError as e:
    #raise BaseException('Error saving file')
    print(e)
    getchMsg()

CueClassMap = {
  'load':CueLoad,
  'fade':CueFade,
  'limbs':CuePrinboo,
  'c':CuePrinboo,
#  'video':CueVideo,
}
