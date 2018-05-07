"""Wrapper for the Open Lighting Architecture python client"""

from ola.ClientWrapper import ClientWrapper
import time, threading
from console import *

class DmxWrapper:
    """Wrapper for a DMX over USB using the Open Lighting Architecture python cilent.

    DMX Channels go from 0-511 and have value 0-255.
    OLA can't individually address DMX channels, so this class only invokes the DMX subsystem if there has been a change.
    To use, call set() on individual channels and then call send().

    TODO: make this handle multiple universes (can only send to universe 1 at the moment).
    """

    _singleton = None
    def __new__(cls):
        if not cls._singleton:
          print("Making DMX singleton")
          cls._singleton = object.__new__(cls)
        return cls._singleton

    def __init__(self):
        self.MaxChannels = 512
        self.MinValue = 0
        self.MaxValue = 255

    def initialize(self, configDict):
        config = configDict.get('DMX', {})
        self.universes = config.get('universes', [1])
        self.data = bytearray(self.MaxChannels)

        self.dataChanged = True
        self.client = None
        try:
            self.wrapper = ClientWrapper()
            self.client = self.wrapper.Client()
            self.send()
        except:
            print("Error: couldn't connect to OLA server")
            getchMsg()

    def exit(self):
      pass

    def fitRange(self, x):
      return max(self.MinValue, min(self.MaxValue, round(x)))

    def get(self, index=None, universe=None):
        if index is not None: return self.data[index]
        else: return list(self.data)

    # sends to OLA if there has been a change
    def send(self, universe=None):
        if not self.client: return
        if not self.dataChanged: return
        self.dataChanged = False
        self.client.SendDmx(universe or self.universes[0], self.data)

    # pass a start channel and any number of channel values
    # values are integers 0-255; -1 is no-op
    # you must call send to transmit the changes
    # can say set([values]), set(index, value) or set(index, [values])
    def set(self, channel, values=None, universe=None):
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
    def setFraction(self, channel, values=None, universe=None):
        if values is None:
          values = channel
          channel = 0

        if isinstance(values, int) or isintance(values, float): values = [values]
        intValues = tuple(round(255*v) for v in values)
        self.set(channel, intValues, universe)

    # sets all channels to 0 and transmits
    def off(self, universe=None):
        for i in range(len(self.data)):
            self.data[i] = 0
        self.dataChanged = True
        self.send(universe)

    # convenience to set and transmit a list of values starting at channel 0
    def setAndSend(self, channel, values=None, universe=None):
        self.set(channel, values)
        self.send(universe)

#singleton
DMX = DmxWrapper()

