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
from lightarm import Arms

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
      try:
        if DMX and 'DMX' in data and data['DMX']:
          self.targetDMX = data['DMX']
          if not isinstance(self.targetDMX, list) or not isinstance(sum(self.targetDMX), int):
            raise BaseException('error in DMX portion of cue file')
      except: pass

      self.limbs = None
      try: self.limbs = Prinboo.limbs and data.get('Limbs')
      except: pass

      self.armData = None
      try: self.armData = Arms and data.get('LightArms')
      except: pass

  def run(self, immediate=False):
      # load the file again in case it has changed since the cuesheet was loading
      self.load()

      if self.targetDMX:
        DMX.setAndSend(0, self.targetDMX)

      if self.limbs: #TODO figure out if we have a pose or an animation
        Prinboo.limbs.setAngle(self.limbs)

      if self.armData:
        Arms.load(self.armData)

class WaitForPreviousThread(threading.Thread):
  def __init__(self, prevThread, runner):
    threading.Thread.__init__(self)
    self.prevThread = prevThread
    self.runner = runner
    self.shouldExit = False
    self.start()

  def exit(self):
    self.shouldExit = True

  def run(self, immediate=False):
    if self.prevThread:
      while self.prevThread.isAlive():
        time.sleep(.01)
    self.runner()

class Stepper:
  def __init__(self): pass
  def step(self): pass
  def finish(self): pass

class CueFade(CueLoad):
  """Fades from current scene to new scene.

  Launches a thread to do the fading for DMX and other lights. Cancels a previous fade.

  usage:
  fade <optional time in seconds> <filename>
  """

  _LightsThread = None

  def __init__(self, line):
    Cue.__init__(self, line)    # ignore CueLoad's constructor so we can parse differently

    tokens = line.split()
    if len(tokens) < 2:
      raise BaseException('usage: fade <optional time in seconds> <filename>')

    try:
      tok = tokens[1]
      self.duration = float(tok)
      self.filename = restAfterWord(tok, line)
    except:
      self.duration = 5.0
      self.filename = restAfterWord(tokens[0], line)

    # load the file to syntax check it, so we can report an error at beginning
    # instead of during a run through
    self.load()

  def run(self, immediate=False):
    if self._LightsThread:
      self._LightsThread.exit()

    # load the file again in case it has changed since the cuesheet was loading
    self.load()

    # create a new thread that will call us
    self._LightsThread = WaitForPreviousThread(self._LightsThread, self) 

  # called by the thread created in run()
  def __call__(self):
    timestep = .05
    printPeriodPeriod = .25
    printPeriodTimestepCount = printPeriodPeriod / timestep
    startTime = time.time()
    endTime = startTime + self.duration
    nextTime = startTime + timestep
    nextPrintTime = startTime + printPeriodPeriod

    print('                 fading for', self.duration, 'seconds..', end='', flush=True)

#    try:
#      if self.armData: Arms.load(self.armData)
#    except:
#      pass
#
    steppers = []

    if self.targetDMX:
      steppers.append(DmxFader(self.duration, timestep, self.targetDMX))

    if self.armData:
      steppers.append(PwmFader(self.duration, timestep, self.armData))
    
    while 1:
      for s in steppers: s.step()
      now = time.time()

      # print a duration every so often
      if now >= nextPrintTime:
        print('.', end='', flush=True)
        nextPrintTime += printPeriodPeriod

      if now > endTime: break
      nextTime += timestep
      time.sleep(nextTime - time.time())

    print('DONE')
    # TODO exceptions having to do with the fade math


class DmxFader:
  def __init__(self, duration, timestep, targetDMX):
    self.target = targetDMX
    self.current = DMX.get()
    self.vel = [0] * len(self.current)

    # calculate delta for each timestep
    # -1 means don't change
    for i in range(len(target)):
      if target[i] >= 0:
        self.vel[i] = (self.target[i] - self.current[i]) * (timestep / duration)

  def step(self):
    # calculate new channel values and transmit
    for i in range(len(self.current)): self.current[i] += vel[i]
    channels = [round(x) for x in self.current]
    DMX.setAndSend(0, channels)

  def finish(self):
    # make sure we arrive at the target numbers, as rounding error may creep in
    DMX.setAndSend(0, self.target)

#except:
#  raise BaseException('Error talking to OLA DMX server')

class PwmFader:
  def __init__(self, duration, timestep, armData):
    self.armData = armData
    self.target = []
    self.current = []
    self.vel = []

    # map each address to an index
    for address, arm in self.armData.items():
      i = Arms.arms.index(Arms.findArm(address))
      self.target.append(arm.get('channels', []))

    for i in range(Arms.num()):
      self.current.append(Arms.getChannels(i))

    # calculate delta for each timestep
    # -1 means don't change
    for i in range(len(self.target)):
      self.vel.append([])
      for j in range(len(self.target[i])):
        if self.target[i][j] >= 0:
          self.vel[i].append((self.target[i][j] - self.current[i][j]) * (timestep / duration))
        else: self.vel[i].append(0)

  def step(self):
      # calculate new channel values and transmit
      for i in range(len(self.current)):
        self.current[i] = [a+b for a,b in zip(self.current[i], self.vel[i])]
        Arms.setChannels(i, self.current[i])

  def finish(self):
    # make sure we arrive at the target numbers, as rounding error may creep in
    Arms.load(self.armData)


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

      # Signal the previous thread to exit, and hand it to the next threadV
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
  text = "{\n 'version': 0"
  
  #try:
  text += ",\n  'LightArms': " + str(Arms)
  #except: pass

  try: 
    text += ",\n  'DMX': " + str(DMX.get())
  except: pass
  
  try:
    text += ",\n  'Limbs': " + str(Prinboo.limbs)
  except: pass
    
  text += "\n}\n"
  #text = "{\n 'version': 0,\n 'DMX': " + dmx + ",\n 'LightArm': {\n  'Servos': " + str(ucServos) + ",\n  'LEDs': " + str(ucLEDs) + "\n }\n}"
  #text = "{'version': 0, 'DMX': " + dmx + ", 'LightArm': {'Servos': " + str(ucServos) + ", 'LEDs': " + str(ucLEDs) + "}}"

  print(text)
  try:
    with openCueFile(filename, 'w') as f:
      f.write(text)
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
