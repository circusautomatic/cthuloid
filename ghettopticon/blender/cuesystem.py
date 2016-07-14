# list of show cues
# goes in a file by itself
# TODO figure out how to split into multiple files in blender
cues = [
'scene 1',
lambda:print('1a'),
lambda:print('1b'),
'scene 2',
lambda:print('2a'),
lambda:print('2b'),
'scene 3',
lambda:print('3a'),
]

import bge

def keydown(key):
    return bge.logic.keyboard.events[key] == bge.logic.KX_INPUT_JUST_ACTIVATED

# A manager in which cues are represented by a list of callable lambdas
class CueSystem:
    # initialize with a regular list of cues, which may consist of:
    # -scene names as strings (these are for the benefit of the operator only)
    # -callable lambdas
    def __init__(self, cues):
        self.cues = cues
        self.index = 0      # points at the next cue to execute
        #self.printNextSceneName = True
        
    def thisCue(self):
        return self.cues[self.index]

    # move to the start of the next scene, without executing the first cue
    # looks for a string and sets the index there
    def nextScene(self):
        while 1+self.index < len(self.cues):
            self.index += 1
            c = self.thisCue()
            if type(c) is str:
                print(c)
                return
        print('At End')
    
    # move to the start of the previous scene, without executing the first cue
    # looks for a string and sets the index there
    def prevScene(self):
        while self.index > 0:
            self.index -= 1
            c = self.thisCue()
            if type(c) is str:
                print(c)
                return
        print('At beginning')

    # executes the next cue, pointed at by index
    def nextCue(self):
        while self.index < len(self.cues):
            c = self.thisCue()
            # skip strings, because they denote the start of a new scene
            if type(c) is str:
                print(c)
                self.index += 1
            else:
                c()
                self.index += 1
                return
        print('At End')
    
    # executes the previous cue (the before the current index)
    def prevCue(self, playCue=False):
        while self.index > 0:
            self.index -= 1
            c = self.thisCue()
            # skip strings, because they denote the start of a new scene
            if type(c) is str: pass
            else:
                if playCue: c()
                else: print('Back a cue')
                return
        print('At Beginning')

C = CueSystem(cues)

def k():
    if keydown(bge.events.RIGHTARROWKEY): C.nextCue()
    if keydown(bge.events.LEFTARROWKEY): C.prevCue()
    if keydown(bge.events.UPARROWKEY): C.prevScene()
    if keydown(bge.events.DOWNARROWKEY): C.nextScene()