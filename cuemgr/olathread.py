import time, threading
from console import *
from ola.ClientWrapper import ClientWrapper

"""class OlaThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.universe = 1
    self.lastDataSent = [0] * 512   # set from both send() and receive callback, so may need synchronization
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

