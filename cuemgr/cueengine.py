import time, threading
from console import *
from cue import *


class Scene:
  def __init__(self, name):
    self.name = name
    self.cues = []
  def add(self, cue):
    self.cues.append(cue)


class CueEngine:
  def __init__(self):
    self.scenes = [Scene('Beginning Blackout')]
    self.scenes[0].add(CueLoad('load off'))
    self.reset()

  def reset(self):
    self.ixScene = 0  # current scene
    self.ixCue = -1   # cue we just ran
  
  def thisScene(self): return self.scenes[self.ixScene]
  def thisCue(self):   return self.thisScene().cues[self.ixCue]

  def add(self, scene):
    self.scenes.append(scene)

  def getLoc(self):
    #return (self.ixScene, self.ixCue)
    return None

  def printLocStr(self, printThisCue=True):
    s ='(' + self.thisScene().name + ')'
    if printThisCue and len(self.thisScene().cues): 
      s += ' - '
      if self.ixCue >= 0: s+= self.thisCue().line.strip()
      else: s += self.thisScene().cues[1 + self.ixCue].line.strip()
    print(s)

  def onLastCue(self):
    return 1+self.ixCue >= len(self.thisScene().cues)
  def onLastScene(self):
    return 1+self.ixScene >= len(self.scenes)
  def onFirstScene(self):
    return self.ixScene <= 0

  def nextCue(self):
    if self.onLastCue():
      if self.onLastScene():
        print('At End')
        return
      self.ixScene += 1
      self.ixCue = 0
      print('--------------------------------------------------------------')
      #print(self.getLoc(), 'Scene:', self.thisScene().name)
    else:
      self.ixCue += 1

    self.printLocStr()
    #print(self.getLoc(), 'next cue:', self.thisCue().line.strip())
    self.thisCue().run()

  def prevCue(self):
    if self.ixCue <= 0:
      if self.onFirstScene():
        print('At Beginning')
        return
      self.ixScene -= 1
      self.ixCue = len(self.thisScene().cues) - 1
      print('--------------------------------------------------------------')
      #print(self.getLoc(), 'Scene:', self.thisScene().name)
    else:
      self.ixCue -= 1

    self.printLocStr()
    #print(self.getLoc(), 'previous cue:', self.thisCue().line.strip())
    self.thisCue().run(True)

  def nextScene(self): 
    if self.onLastScene():
      print('At End')
      return
    self.ixScene += 1
    self.ixCue = -1
    #print(self.getLoc(), 'next Scene:', self.thisScene().name)
    self.printLocStr(False)

  def prevScene(self):
    if self.onFirstScene():
      print('At Beginning')
      return
    self.ixScene -= 1
    self.ixCue = -1
    #print(self.getLoc(), 'previous Scene:', self.thisScene().name)
    self.printLocStr(False)

  def loadCueSheet(self, filename):
    try:  # parse the cues file
      with open(filename) as f:
        lineNum = 0
        curScene = None
        indentStack = []  # stack of tuples of (node, indent_len)

        def pushIndent(node, indentLen): indentStack.append((node, indentLen))
        def popIndent(): indentStack.pop()
        def topIndent(): return indentStack[-1]
        def topIndentLen(): return indentStack[-1][1]

        seenTab, seenSpace = False, False
        pushIndent(self, -1)

        line = f.readline()
        while line:
          lineNum += 1
          tokens = line.split()
          
          try:
            # skip empty lines and lines where the first token is #
            if len(tokens) and not tokens[0].startswith('#'): 
              cmd = tokens[0]
              indent = line[:line.find(cmd)]
              indentLen = len(indent)
              thisNode = None

              #test for mixed indentation characters
              if indent.find(' ') >= 0: seenSpace = True
              if indent.find('\t') >= 0: seenTab = True
              if seenSpace and seenTab:
                raise TabError('The cue file mixes spaces and tabs.  Please use one or the other')
              
              # remove cmds with <= indent, because their block/revelance is over
              pops = 0
              while indentLen < topIndentLen():
                popIndent()
                pops += 1
              
              # did we pop to an previously unused indent? Handle this case:
              # s
              #   s
              #  s
              if pops > 0 and indentLen > topIndentLen():
                raise IndentationError('Indentation level does not match a previous block')

              if indentLen == topIndentLen():
                popIndent()

              if cmd == 'scene':
                thisNode = Scene(restAfterWord(cmd, line))
              elif cmd == 'seq':
                thisNode = CueSequence(line)
              elif cmd == 'load':
                thisNode = CueLoad(line)
              elif cmd == 'fade':
                thisNode = CueFade(line)
              else:
                print('Error unrecognized command on line', lineNum)
                print('Text:', line)
                return

              if thisNode:
                topIndent()[0].add(thisNode)
                pushIndent(thisNode, indentLen)
         
          except BaseException as e:
            print('Error:', e)
            print('Line Number:', lineNum)
            print('Text:', line)
            return

          line = f.readline()
      self.reset()
    except BaseException as e:
      print('Error:', e)
      getchMsg()

if __name__ == '__main__':
  CueMgr = CueEngine()
  CueMgr.loadCueSheet('cuesheet.txt')

