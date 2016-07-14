import sys, os, threading, ast, time
from console import *
from lightarm import Arms
from dmx import DmxChannels

#Arms = LightArms()
DMX = DmxChannels()

def openCueFile(filenameOnly, mode='r'):
  return open('scenes/' + filenameOnly, mode)

def restAfterWord(word, line):
  return line[line.find(word) + len(word):].strip()

def frange(start, end=None, inc=None):
    "A range function, that does accept float increments..."

    if end == None:
        end = start + 0.0
        start = 0.0
    else: start += 0.0 # force it to be a float

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

# return a dictionary of DMX, LED channels, and Servo angles
def loadCueFile(filenameOnly):
  with openCueFile(filenameOnly) as f:
    text = f.read()

    # test for file version
    if text[0] == '[':
      # just a list of dmx channel values
      dmx = ast.literal_eval(text)
      return {'DMX':dmx}

    json = ast.literal_eval(text)
    #print(json)
    return json

    # TODO check version
    #if json['version'] == 0:

########################################################
# cue commands

class Cue:
  def __init__(self, line):
    self.line = line

  def load(self):
    pass

  def run(self, immediate=False):
    print('empty cue')

class CueSequence(Cue):
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
      if 'DMX' in data:
        self.targetDMX = data['DMX']
        if not isinstance(self.targetDMX, list) or not isinstance(sum(self.targetDMX), int):
          raise BaseException('error in DMX portion')

      # Light Arms - may be absent
      try:
        self.armData = data['LightArm']
      except:
        self.leds = self.servos = None
      #except BaseException as e:
    #  raise BaseException('Error loading file: ' + str(e))

  def run(self, immediate=False):
      # load the file again in case it has changed since the cuesheet was loading
      self.load()

      if self.targetDMX:
        DMX.setAndSend(0, self.targetDMX)

      # Light Arms - may be absent
      try:
        if self.armData: Arms.load(self.armData)
      except:
        pass

    
  # fade from current scene to new scene
  # usage:
  # fade <optional time in seconds> <filename>
class CueFade(CueLoad):
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
        nextPrintTime = startTime + printPeriodPeriod

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


# instantiate a class and run it
def cmdCue(line, CueClass):
  try:
    cue = CueClass(line)
    cue.run()
  except BaseException as e:
    print(e)

# save current OLA scene
def cmdSave(tokens, line):
  if len(tokens) < 2:
    raise BaseException('no filename')

  filename = restAfterWord(tokens[0], line)
  dmx = str(DMX.get())
  arms = str(Arms)
  text = "{\n 'version': 0,\n 'DMX': " + dmx + ",\n 'LightArm': " + arms + "\n}"
  #text = "{\n 'version': 0,\n 'DMX': " + dmx + ",\n 'LightArm': {\n  'Servos': " + str(ucServos) + ",\n  'LEDs': " + str(ucLEDs) + "\n }\n}"
  #text = "{'version': 0, 'DMX': " + dmx + ", 'LightArm': {'Servos': " + str(ucServos) + ", 'LEDs': " + str(ucLEDs) + "}}"
  
  print(text)
  try:
    with openCueFile(filename, 'w') as f:
      f.write(text)
      f.write('\n')
  except:
    raise BaseException('Error saving file')

