import time, threading
from console import *
from ola.ClientWrapper import ClientWrapper

"""class OlaThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.universe = 1
    self.lastDataSent = [0] * 512   # set from both send() and receive callback, so may have thread issues
    self.lastDataReceived = None

  def run(self):
    def onData(data):
        # TODO check on status before assigning data
        self.lastDataReceived = data
        #print(data)

    self.wrapper = ClientWrapper()
    self.client = self.wrapper.Client()
    self.client.RegisterUniverse(self.universe, self.client.REGISTER, onData)
    print('running OLA thread...')
    self.wrapper.Run()
    # TODO catch exceptions

  def exit(self):
    self.wrapper.Stop()

  def getLastReceived(self):
    return self.lastDataReceived

  def getLastSent(self):
    return self.lastDataSent

  def send(self, data):
    self.lastDataSent = data
    self.client.SendDmx(self.universe, data)

OLA = OlaThread()
OLA.start()"""

# Holds an array of 512 DMX channels.
# Channels go from 0-511 and have value 0-255.
# OLA can't individually address DMX channels, so this class only
# invokes the DMX subsystem if there has been a change
# To use, call set() on individual channels and then call send().
class DmxChannels:
    def __init__(self):
        self.NumChannels = 512
        self.MinValue = 0
        self.MaxValue = 255
        self.data = bytearray(self.NumChannels)
        
        self.dataChanged = False
        self.client = None
        try:
            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
        except:
            print("Error: couldn't connect to OLA server")
            #getch()
            
    def exit(self):
      pass

    def get(self, index=None):
        if index is not None: return self.data[index]
        else: return list(self.data)
    
    # sends to OLA if there has been a change    
    def send(self):
        if not self.client: return
        #if not self.dataChanged: return
        self.dataChanged = False
        self.client.SendDmx(1, self.data)
        
    # pass a start channel and any number of channel values
    # values are integers 0-255; -1 is no-op
    # you must call send to transmit the changes
    # can say set([values]), set(index, value) or set(index, [values])
    def set(self, channel, values=None):
        if values is None:
          values = channel
          channel = 0

        if isinstance(values, int): values = [values]
        #print('DMX.set channel', index, '=', values)
        for v in values:
            if v != -1 and self.data[channel] != v:
                self.data[channel] = v
                self.dataChanged = True
            channel += 1
                
    # pass a start channel and any number of channel values
    # values are numbers between 0 and 1
    # you must call send to transmit the changes
    def setFraction(self, channel, values=None):
        if values is None:
          values = channel
          channel = 0

        if isinstance(values, int) or isintance(values, float): values = [values]
        intValues = tuple(round(255*v) for v in values)
        self.set(channel, intValues)

    # sets all channels to 0 and transmits
    def off(self):
        for i in range(len(self.data)):
            self.data[i] = 0
        self.dataChanged = True
        self.send()

    # convenience to set and transmit a list of values starting at channel 0
    def setAndSend(self, channel, values=None):
        self.set(channel, values)
        self.send()

if __name__ == '__main__':
  DMX = DmxChannels()

