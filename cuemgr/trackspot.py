# A 7-channel knockoff stage light
# the following args are letters for keyboard control: up, down, left, right, brighter, darker
class TrackSpot:
  def __init__(self, dmx, firstChannel, up, down, left, right, brighter, darker):

    # channel function names starting with firstChannel
    self.channelNames = ['X position', 'Y position', 'Color', 'Pattern', 'Strobe', 'Intensity', 'Movement speed']

    self.colorKey = """\
0   white
30  blue
60 yellow
90 purple
120 red
150 magenta
190 deep purple
220 grin
250 pink"""

    self.dmx = dmx

    # channel numbers (0-based)
    self.firstChannel = firstChannel - 1    # convert from 1-based to 0-based index
    self.x         = self.firstChannel
    self.y         = self.firstChannel + 1
    self.color     = self.firstChannel + 2 
    self.pattern   = self.firstChannel + 3
    self.strobe    = self.firstChannel + 4
    self.intensity = self.firstChannel + 5
    self.speed     = self.firstChannel + 6

    self.up = up
    self.down = down
    self.left = left
    self.right = right
    self.brighter = brighter
    self.darker = darker

  def onKey(self, ch):
    inc = 5
    if ch == self.left:       self.set(self.x,  inc)
    elif ch == self.right:    self.set(self.x, -inc)
    elif ch == self.up:       self.set(self.y,  inc)
    elif ch == self.down:     self.set(self.y, -inc)
    elif ch == self.brighter: self.set(self.intensity,  inc)
    elif ch == self.darker:   self.set(self.intensity, -inc)

  def set(self, channel, inc):
    v = self.dmx.get(channel)
    u = min(255, max(0, v + inc))
    print(1+channel, '=', v, '->', u)
    self.dmx.setAndSend(channel, u)


