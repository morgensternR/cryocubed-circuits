from sys import stdin, stdout, exit
import select
import gc
import ujson

#Move this class to a different file
class USBDevice():
    def __init__(self) -> None:
        super().__init__()
        # If something goes really wrong then we can send
        # an error message back, rather than having the program crash
        # Current example usage is if the diode_config.json is invalid
        self._in_failure_mode = False

    def set_failure_mode(self):
        self._in_failure_mode = True

    def readUSB(self):
        gc.collect()
        while stdin in select.select([stdin], [], [], 0)[0]:
            #print('Got USB serial message')
            gc.collect()
            cmd = stdin.readline()
            #print(type(cmd), repr(cmd))
            cmd = cmd.strip().upper()
            if len(cmd)>0:
                self.do_command(cmd)

    def writeUSB(self, msg):
        print(ujson.dumps(msg))
    
    @property
    def commands(self):
        pass

    def do_command(self, input_line):
        if self._in_failure_mode:
            self.writeUSB("failure")
            return

        #try:
        items = input_line.split()
        cmd = items[:1]
        params = items[1:]
    
        if cmd:
            command = self.commands.get(cmd[0].upper(), lambda _: 'not understood')
            self.writeUSB(command(params))
        #except:
            #self.writeUSB("bad command")

    def run(self):
        while True:
            self.readUSB()
