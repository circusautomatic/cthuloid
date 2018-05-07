"""A console-based cueing program designed for running threatrical productions.

See readme for an overview. 

The program automatically loads 'cuesheet.txt'. Cues are assumed to be in the folder 'scenes'.
See cue.py and cueengine.py for more information on cues and cuesheets.
See lightarm.py for info on spotlight robots.
See dmx.py for DMX using Open Lighting Architecture bindings for the local web server.

This file contains definitions of the 3 program views and and a keyboard input loop.

TODO:
  - move to curses
  - display all keyboard controls

"""



import sys, os, os.path, threading, ast, time, signal
from console import * 
from cue import *
from cueengine import CueEngine
from trackspot import TrackSpot
from config import config

CuesFilename = 'cuesheet.txt'   #initial cuesheet automatically loaded

CueMgr = CueEngine()

#try:
#  from prinboo import Prinboo
#except ImportError:
Prinboo = None
#  print('No Prinboo')

try:
  from pivideo import Video
except ImportError:
  Video = None
  print('No Video')

try: from lightarm import Arms
except ImportError:
  Arms = None
  print('No LightArms')

try: from dmx import DMX
except KeyError:
  DMX = None
  print('No DMX')

# call initialize outside of try-except to show errors to user
if Arms: Arms.initialize(config)
if DMX: DMX.initialize(config)
if Video: Video.initialize(config)

print("\n\n")

# these functions define the min and max values for robot spotlight parameters
#def fitServoRange(v): return max(212, min(812, v))
#def fitChannelRange(v): return max(0, min(MaxPWM, v))

def restAfterWord(word, line):
  return line[line.find(word) + len(word):].strip()

class LinearStateMachine:
  """A faux iterator on an ordered list that can move forward or backward and clamps at the ends.
     There is probably a more Pythonic way to do this.""" 
  def __init__(self, states):
    self.modes = states
    self.current = len(states)-1    #index into states

  def __call__(self): return self.modes[self.current]
  def prev(self): self.current = max(0, min(len(self.modes)-1, self.current - 1))
  def next(self): self.current = max(0, min(len(self.modes)-1, self.current + 1))
    
class View:
  """Abstract base class for a program view"""
  def __init__(self):
    self.lineInputKey = 'c'
    #print(self.__class__)
  def onFocus(self): pass
  def display(self): pass
  def handleChar(self): pass


class LightArmView(View):
  """View that controls spotlight robots"""
  def __init__(self):
    super().__init__()

    self.VerticalGroups = int(Arms.MaxChannels / 3)
    print(self.VerticalGroups)
    self.PageWidth = min(Arms.num(), 32)
    self.mode = 1   # index into self.Modes
    self.ixCursor = 0
    self.iyCursor = 0

    self.inc = LinearStateMachine([1, 5, 20])

  # map names to servo vector indices
  ServoDims = {'x':1, 'y':0}

  # do we modify one arm or a group 
  Modes = ['individual', 'group']

  def toggleMode(self):
    self.mode = (self.mode + 1 ) % len(self.Modes)
  def inSingleMode(self):
    return self.mode == 0

  def numArms(self): return Arms.num()

  # returns a list of the selected arms' indices
  def selected(self):
    if self.inSingleMode():
      return [self.ixCursor]
    else:
      return range(self.group(), self.PageWidth)

  # returns a list of selected servo IDs, two for every arm index
#  def selectedIDs(self):
#    ids = []
#    for i in self.selected():
#      ids.append(self.xIndexToID(i))
#      ids.append(self.yIndexToID(i))
#    return ids
     
  # return starting index of group that cursor is in
  def group(self, cursor=None):
    if cursor is None: cursor = self.ixCursor
    return cursor - cursor % self.PageWidth

  # sees whether index is in cursor's group
  def inGroup(self, index, cursor=None):
    if cursor is None: cursor = self.ixCursor
    return index // self.PageWidth == cursor // self.PageWidth
 
  # retrieve angle based on arm index on screen
  # type must be 'x' or 'y'
  def getAngle(self, type, index=None):
    if index is None: index = self.ixCursor
    dim = self.ServoDims[type]
    return Arms.getAngle(index, dim)

   # add increment to the angle of a servo of the currently selected arm(s)
  def modAngle(self, type, inc):
    dim = self.ServoDims[type]
    for id in self.selected():
      try: a = Arms.getAngle(id, dim)
      except IndexError: return
      angle = Arms.fitServoRange(a)
      Arms.setAngle(id, dim, angle + inc)

  # add increment to the intensity of the currently selected arm(s)
  def modI(self, inc, channel):
    #print('ids:', self.selected())
    for id in self.selected():
      try: v = Arms.getChannel(id, channel)
      except IndexError: return
      Arms.setChannel(id, channel, Arms.fitChannelRange(v + inc))

  def handleLineInput(self, line):
    tokens = line.split()
    if len(tokens) == 0: return
    cmd = tokens[0]

  def handleChar(self, ch): 
    ch = ch.lower()
    if ch == 'x':
      self.toggleMode() 
    if ch == 'q': 
      for id in self.selected(): Arms.relax(id)
    if ch == '0':
      pass #Arms.setAngles(self.selected(), [Arms.ServoCenter] * len(self.ServoDims))
    elif ch == 'w':
      self.modAngle('y', self.inc())
    elif ch == 's':
      self.modAngle('y', -self.inc())
    elif ch == 'a':
      self.modAngle('x', self.inc())
    elif ch == 'd':
      self.modAngle('x', -self.inc())
    elif ch == 'r':
      self.modI(self.inc(), 0 + self.iyCursor*3)
    elif ch == 'f':
      self.modI(-self.inc(), 0 + self.iyCursor*3)
    elif ch == 't':
      self.modI(self.inc(), 1 + self.iyCursor*3)
    elif ch == 'g':
      self.modI(-self.inc(), 1 + self.iyCursor*3)
    elif ch == 'y':
      self.modI(self.inc(), 2 + self.iyCursor*3)
    elif ch == 'h':
      self.modI(-self.inc(), 2 + self.iyCursor*3)

    elif ch == '<' or ch == ',':
      self.inc.prev()
    elif ch == '>' or ch == '.':
      self.inc.next()

    elif ch == '\x1b':
      seq = getch() + getch()
      if seq == '[C': # left arrow
        if self.inSingleMode(): self.ixCursor += 1
        else: self.ixCursor = self.ixCursor - self.ixCursor % self.PageWidth + self.PageWidth
        self.ixCursor = min(self.numArms()-1, self.ixCursor)
      elif seq == '[D': # right arrow
        if self.inSingleMode(): self.ixCursor -= 1
        else: self.ixCursor = self.ixCursor - self.ixCursor % self.PageWidth - self.PageWidth
        self.ixCursor = max(0, self.ixCursor)
      elif seq == '[A': #pass # up arrow
        self.iyCursor = max(0, self.iyCursor - 1)
      elif seq == '[B': #pass # down arrow
        self.iyCursor = min(self.VerticalGroups - 1, self.iyCursor + 1)
      print(self.iyCursor)

  def onFocus(self):
    pass

  def display(self):
    clearScreen()
    numArms = self.PageWidth #self.numArms()

    def printHSep(firstColBlank=True):
      if firstColBlank: print('   |', end='')
      else: print('---|', end='')

      if self.inSingleMode():
        for i in range(numArms):
          if i == self.ixCursor: print('===|', end='')
          else: print('---|', end='')
      else:
        for i in range(numArms):
          if self.inGroup(i):
            if self.inGroup(i+1, i): print('====', end='')
            else: print('===|', end='')
          else: print('---|', end='')
      print('')

    def printAngle(dim, index):
      try:
        angle = self.getAngle(dim, index) 
        if angle < 1: print('XXX|', end='')
        else: print('{0:^3}|'.format(angle), end='')
      except:
        print('---|', end='')

    print('   Light Arm View')
    printHSep(False)

    print('x: |', end='')
    for i in range(numArms):
      printAngle('x', i)
    print('')

    printHSep() 
     
    print('y: |', end='')
    for i in range(numArms):
      printAngle('y', i)
    print('')

    printHSep()

    names = ''
    for i in range(self.VerticalGroups):
      if i == self.iyCursor: names += 'BGR'
      else: names += 'bgr'

    for channel in range(Arms.MaxChannels):
      print(names[channel] + ': |', end='')
      for i in range(numArms):
        try: print('{0:^3}|'.format(Arms.getChannel(i, channel)), end='')
        except: print('---|', end='')
      print('')
      printHSep(channel+1 != Arms.MaxChannels)


class SliderView(View):
  """View for controling DMX lights"""

  def __init__(self): 
    super().__init__()
    self.ixCursor = 0
    self.MaxChannels = DMX.MaxChannels
    self.MinValue = 0
    self.MaxValue = 255

    self.PageWidth = 16
 
  def onFocus(self):
    pass

  def display(self):
      clearScreen()
      ixCursorInPage = self.ixCursor % self.PageWidth
      ixPageStart = self.ixCursor - ixCursorInPage

      print('                           DMX View')
      for i in range(self.PageWidth): print('----', end='')
      print('')

      # channel values
      for i in range(ixPageStart, ixPageStart + self.PageWidth):
        print('{0:^4}'.format(DMX.get(i)), end='')
      print('')

      # separator and cursor
      for i in range(ixCursorInPage): print('----', end='')
      print('===-', end='')
      for i in range(self.PageWidth - ixCursorInPage - 1): print('----', end='')
      print('')
      
      # channel numbers
      for i in range(ixPageStart + 1, ixPageStart + self.PageWidth + 1):
        print('{0:^4}'.format(i), end='')
      print('')

  def handleLineInput(self, line):
    tokens = line.split()
    if len(tokens) == 0: return
    cmd = tokens[0]

    try:
      # set a channel or a range of channels (inclusive) to a value
      # channels are 1-based index, so must subtract 1 before indexing
      # usage: (can take multiple arguments)
      # set<value> <channel>
      # set<value> <channel-channel>
      if cmd.startswith('set'):
        value = int(cmd[3:])
        print(value)
        if value < self.MinValue or value > self.MaxValue:
          print('Value', value, ' out of range [0, 255]')
          return

        if len(tokens) == 1:
          v = [value] * self.MaxChannels 
          DMX.setAndSend(0, v)
          return

        # handle space-delimited arguments: index or inclusive range (index-index)
        for token in tokens[1:]:
          indices = token.split('-')

          # a single channel index
          if len(indices) == 1:
            DMX.setAndSend(int(indices[0]) - 1, value)
          # argument is a range of channel indices, inclusive, ex: 56-102
          elif len(indices) == 2:
            lower = int(indices[0]) - 1
            upper = int(indices[1])     # inclusive range, so -1 to correct to 0-based index but +1 to include it
            DMX.setAndSend(lower, [value] * (upper - lower))
          else:
            raise BaseException('too many arguments')

      else: print('Unrecognized command')

    except BaseException as e:
      print(e)

  # keyboard input
  def handleChar(self, ch):
      ixCursorInPage = self.ixCursor % self.PageWidth
      ixPageStart = self.ixCursor - ixCursorInPage

      ch = ch.lower()

      if ch == '0':
        DMX.setAndSend(self.ixCursor, self.MinValue)
      elif ch == '8':
        DMX.setAndSend(self.ixCursor, self.MaxValue//2)
      elif ch == '9':
        DMX.setAndSend(self.ixCursor, self.MaxValue)
      
      elif ch == '\x1b':
        seq = getch() + getch()
        if seq == '[A': # up arrow
          DMX.setAndSend(self.ixCursor, min(self.MaxValue, DMX.get(self.ixCursor) + 1))
        elif seq == '[B': # down arrow
          DMX.setAndSend(self.ixCursor, max(self.MinValue, DMX.get(self.ixCursor) - 1))
        elif seq == '[C': # left arrow
          self.ixCursor = min(self.MaxChannels-1, self.ixCursor + 1)
        elif seq == '[D': # right arrow
          self.ixCursor = max(0, self.ixCursor - 1)
        elif seq == '[5': # page up
          getch() # eat trailing ~
          self.ixCursor = min(self.MaxChannels-1, ixPageStart + self.PageWidth)
        elif seq == '[6': # page down
          getch() # eat trailing ~
          self.ixCursor = max(0, ixPageStart - self.PageWidth)

class PrinbooView(View):
  """View for controling Prinboo servos"""

  def __init__(self): 
    super().__init__()
    self.ixCursor = 0
    self.MaxChannels = 11 #TODO get from Prinboo.limbs, but they may not have loaded yet?
    self.MinValue = 0
    self.MaxValue = 180

    self.PageWidth = self.MaxChannels
 
  def onFocus(self):
    pass

  def display(self):
      clearScreen()
      ixCursorInPage = self.ixCursor % self.PageWidth
      ixPageStart = self.ixCursor - ixCursorInPage

      print('                         Prinboo View')
      for i in range(self.PageWidth): print('----', end='')
      print('')

      # channel values
      for i in range(ixPageStart, ixPageStart + self.PageWidth):
        try:
          angle = Prinboo.limbs.getAngle(i + 1)
        except(KeyError):
          angle = 'XXX'
        print('{0:^4}'.format(angle), end='')
      print('')

      # separator and cursor
      for i in range(ixCursorInPage): print('----', end='')
      print('===-', end='')
      for i in range(self.PageWidth - ixCursorInPage - 1): print('----', end='')
      print('')
      
      # channel numbers
      for i in range(ixPageStart + 1, ixPageStart + self.PageWidth + 1):
        print('{0:^4}'.format(i), end='')
      print('')

  def handleLineInput(self, line):
    tokens = line.split()
    if len(tokens) == 0: return
    cmd = tokens[0]

    try:
      # set a channel or a range of channels (inclusive) to a value
      # channels are 1-based index, so must subtract 1 before indexing
      # usage: (can take multiple arguments)
      # set<value> <channel>
      # set<value> <channel-channel>
      '''if cmd.startswith('set'):
        value = int(cmd[3:])
        print(value)
        if value < self.MinValue or value > self.MaxValue:
          print('Value', value, 'out of range', self.MinValue, '-', self.MaxValue)
          return

        if len(tokens) == 1:
          v = [value] * self.MaxChannels 
          #DMX.setAndSend(0, v)
          return

        # handle space-delimited arguments: index or inclusive range (index-index)
        for token in tokens[1:]:
          indices = token.split('-')

          # a single channel index
          if len(indices) == 1:
            pass#DMX.setAndSend(int(indices[0]) - 1, value)
          # argument is a range of channel indices, inclusive, ex: 56-102
          elif len(indices) == 2:
            lower = int(indices[0]) - 1
            upper = int(indices[1])     # inclusive range, so -1 to correct to 0-based index but +1 to include it
            #DMX.setAndSend(lower, [value] * (upper - lower))
          else:
            raise BaseException('too many arguments')

      else:'''
      print('Unrecognized command')

    except BaseException as e:
      print(e)

  # keyboard input
  def handleChar(self, ch):
    try:
      ixCursorInPage = self.ixCursor % self.PageWidth
      ixPageStart = self.ixCursor - ixCursorInPage
      id = self.ixCursor + 1    # IDs start at 1

      ch = ch.lower()

      if ch == '0':
        Prinboo.limbs.setAngle(id, self.MinValue)
      elif ch == '8':
        Prinboo.limbs.setAngle(id, self.MaxValue//2)
      elif ch == '9':
        Prinboo.limbs.setAngle(id, self.MaxValue)
      
      elif ch == '\x1b':
        seq = getch() + getch()
        if seq == '[A': # up arrow
          Prinboo.limbs.setAngle(id, min(self.MaxValue, Prinboo.limbs.getAngle(id) + 1))
        elif seq == '[B': # down arrow
          Prinboo.limbs.setAngle(id, max(self.MinValue, Prinboo.limbs.getAngle(id) - 1))
        elif seq == '[C': # left arrow
          self.ixCursor = min(self.MaxChannels-1, self.ixCursor + 1)
        elif seq == '[D': # right arrow
          self.ixCursor = max(0, self.ixCursor - 1)
    except(KeyError):
      pass

class CueView(View):
  """View for running cues from currently loaded cuesheet"""

  def __init__(self):
    super().__init__()

    # hack for manually adjusting track spotlights during the show, specific the Great Star Theater
    self.spots = [
      ]

    CueMgr.loadCueSheet(CuesFilename)

  def onFocus(self):
    clearScreen()
    print('z:     exit')
    print('Space: next cue')
    print('/:     previous cue')
    print('>:     next scene')
    print('<:     previous scene')
    print('----------------------')
    if CueMgr.ixCue < 0:
      print('Next Cue: ', end=''); CueMgr.printLocStr()
    else:
      print('Currently At Cue: ', end=''); CueMgr.printLocStr()
    print('----------------------')
    #print('Press Space initially to black out lights:')

  def display(self): pass

  def handleChar(self, ch):
    if ch == ' ':
      CueMgr.nextCue()
    elif ch == '/':
      CueMgr.prevCue()
    elif ch == '.' or ch == '>':
      CueMgr.nextScene()
    elif ch == ',' or ch == '<':
      CueMgr.prevScene()

#    # Prinboo live controls
#    elif ch == 'w':
#      Prinboo.screen.togglePlayback()
#    elif ch == 'a':
#      Prinboo.motors.incSpeed()
#    elif ch == 'd':
#      Prinboo.motors.decSpeed()
#    elif ch == 's':
#      Prinboo.motors.stop()
#    elif ch == '\x1b':
#      seq = getch() + getch()
#      if seq == '[A': # up arrow
#        Prinboo.motors.forward() 
#      elif seq == '[B': # down arrow
#        Prinboo.motors.backward() 
#      elif seq == '[C': # left arrow
#        Prinboo.motors.turnLeft() 
#      elif seq == '[D': # right arrow
#        Prinboo.motors.turnRight()



  def handleLineInput(self, line):
    pass

def cmdLoadCueSheet(line):
  tokens = line.split()
  filename = restAfterWord(tokens[0], line)
  CueMgr.loadCueSheet(filename)
 
def signal_handler(signal, frame):
  print('\nexiting...')
  if DMX: DMX.exit()
  if Arms: Arms.exit()
  if Prinboo: Prinboo.exit()
  if Video: Video.exit()
  exit()

def programExit(): 
  signal_handler(None, None)


if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == 'prinboo':
    views = [CueView(), LightArms()]
  else: #default is dmx mode
    views = [CueView(), LightArmView()]
    if DMX: views.append(SliderView())
  currentView = views[0]

  signal.signal(signal.SIGINT, signal_handler)
  clearScreen()
  currentView.onFocus()

  # wait for OLA client to connect?

  while 1:
    currentView.display()
    ch = getch()

    if ch == '\x03' or ch == 'z' or ch == 'Z':
      programExit()

    # change view
    elif len(ch) == 1 and ord(ch) >= ord('1') and ord(ch) < (ord('1') + len(views)): 
      currentView = views[ord(ch) - ord('1')]
      currentView.onFocus()

    # every view can have a separate key to enter a command line of text
    elif ch == currentView.lineInputKey:
      print('\nEnter command: ', end='')
      line = input()
      tokens = line.split()

      if len(tokens) == 0: continue
      cmd = tokens[0]

      # program-wide commands 
      if cmd ==   'exit': programExit()
      elif cmd == 'cuesheet': cmdLoadCueSheet(line) # handled in view
      elif cmd == 'save': cmdSave(tokens, line)
      elif cmd in CueClassMap: cmdCue(line, CueClassMap[cmd])
      else: currentView.handleLineInput(line)

    else:
      currentView.handleChar(ch)

