from ola.ClientWrapper import ClientWrapper
import threading


class OlaThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.data = None
        
    def run(self):
        def onData(data):
            # TODO check on status before assigning data
            self.data = data
            #print(data)

        self.wrapper = ClientWrapper()
        self.client = self.wrapper.Client()
        universe = 1
        self.client.RegisterUniverse(universe, self.client.REGISTER, onData)
        print('running thread')
        self.wrapper.Run()

    def exit(self):
        try: self.wrapper.Terminate()
        except: self.wrapper.Stop()

    def getData(self):
        # return or print?
        print(self.data)

o = OlaThread()
o.start()
