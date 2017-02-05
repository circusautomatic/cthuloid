"""
Defines types of cues (sets of hardware parameters), and provides for loading and saving them.

We unfortunately use the word 'cue' in two different ways:
1. A cue is a text file containing hardware parameters in json.
   Note that cues may also be grouped together into a sequence, which is itself treated as a cue.
2. A cue is an instruction to transition to a new set of parameters, either by
    setting them instantaneously or by incrementally fading from the previous parameters.


"""

import sys, os, threading, ast, time
from console import *
from dmx import DmxChannels
from lightarm import Arms

#Arms = LightArms()
DMX = DmxChannels()

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
    #try:
      data = loadCueFile(self.filename)
    
      self.targetDMX = None
#      if 'DMX' in data:
#        self.targetDMX = data['DMX']
#        if not isinstance(self.targetDMX, list) or not isinstance(sum(self.targetDMX), int):
#          raise BaseException('error in DMX portion')

      # Light Arms - may be absent
      try:
        self.armData = data['LightArm']
      except:
        self.armData = None
      #except BaseException as e:
    #  raise BaseException('Error loading file: ' + str(e))

  def run(self, immediate=False):
      # load the file again in case it has changed since the cuesheet was loading
      self.load()

      if self.targetDMX:
        DMX.setAndSend(0, self.targetDMX)

      # Light Arms - may be absent
      #try:
      if self.armData: Arms.load(self.armData)
      #except:
      #  pass

    
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

  def run(self, immediate=False):
    #try:
      # load the file again in case it has changed since the cuesheet was loading
      self.load()

      timestep = .05
      printPeriodPeriod = .25
      printPeriodTimestepCount = printPeriodPeriod / timestep

      # Light Arms
      # TODO fade light arms!
      #try:
        #  if self.armData: Arms.load(self.armData)
      #except:
        #  # pass

      # DMX
      #if self.targetDMX:
      if self.armData:
        #target = self.targetDMX
        #current = DMX.get()
        target = [0] * Arms.num()
        current = [0] * Arms.num()
        vel = [0] * Arms.num()
        
        # map each address to an index
        for address, data in self.armData.items():
          try:
            i = Arms.arms.index(Arms.findArm(address))
            target[i] = data['intensity']
          except ValueError as e:
            pass

        for i in range(Arms.num()):
          current[i] = Arms.getLED(i)

        # calculate delta for each timestep
        # -1 means don't change
        for i in range(len(target)):
          if target[i] >= 0:
            vel[i] = (target[i] - current[i]) * (timestep / self.period)

        print('                 fading for', self.period, 'seconds..', end='', flush=True)
        startTime = time.time()
        endTime = startTime + self.period
        nextTime = startTime + timestep
        nextPrintTime = startTime + printPeriodPeriod

        while 1:
          # calculate new channel values and transmit
          for i in range(len(current)): current[i] += vel[i]
          #channels = [round(x) for x in current] 
          #DMX.setAndSend(0, channels)
          for i in range(Arms.num()):
            Arms.setLED(i, current[i])

          now = time.time()

          # print a period every so often
          if now >= nextPrintTime:
            print('.', end='', flush=True)
            nextPrintTime += printPeriodPeriod

          if now > endTime: break
          nextTime += timestep
          time.sleep(nextTime - time.time())

        # make sure we arrive at the target numbers, as rounding error may creep in
        #DMX.setAndSend(0, target)
        Arms.load(self.armData)
        #for i in range(Arms.num()):
        #  Arms.setLED(i, target[i])
        
        print('DONE')
    #except:
    #  raise BaseException('Error talking to OLA DMX server')
    # TODO other exceptions having to do with the fade math


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
  arms = str(Arms)
  text = "{\n 'version': 0,\n 'DMX': " + dmx + ",\n 'LightArm': " + arms + "\n}"
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

