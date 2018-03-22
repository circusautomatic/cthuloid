import serial, struct, threading, time

# Creates a thread that handles reading lines from serial without blocking the calling
# thread. Override handleLine, which will be called from this object's thread.
class SerialThread (threading.Thread):
    def __init__(self, path, baud=38400, timeout=50, delim='\r\n'):
        self.readPeriod = .01   # seconds
        self.delim = str.encode(delim)
        self.uc = None
        self.shouldExit = False
        try:
            # don't bother doing any other initialization if we can't open the port
            self.uc = serial.Serial(path, baud)
            self.lock = threading.Lock()
            threading.Thread.__init__(self)
            self.start()
        except:
            pass

        if self.uc and self.uc.isOpen():
            print('opened', self.uc.name)
        else:
            print('Error:', path, 'not opened')
            self.exit() # thread shouldn't have started, but just in case

    def valid(self):
        return self.uc and not self.shouldExit

    def exit(self):
        self.shouldExit = True

    def write(self, data):
        if not self.valid(): return
        self.lock.acquire()
        self.uc.write(data)
        self.lock.release()

    # override this
    def handleLine(self, line):
        print('override me!', line)

    def run(self):
        b = bytearray()

        while self.valid():
            #print('run')
            time.sleep(self.readPeriod)
            self.lock.acquire()
            num = self.uc.inWaiting()
            if num:
                b += self.uc.read(num)
                #print(len(b))
            self.lock.release()

            #TODO find all newlines
            ixNewline = b.find(self.delim)
            while ixNewline != -1:
                v = b[:ixNewline].decode("utf-8")
                self.handleLine(v)
                b = b[ixNewline+1:]
                ixNewline = b.find(self.delim)

        if self.uc:
            self.uc.close()
            self.uc = None
