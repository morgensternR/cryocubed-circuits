from sys import stdin, stdout, exit
import select
import gc
import ujson
import time

#Move this class to a different file
class USBDevice():
    def __init__(self, sanity_check_frequency=None) -> None:
        '''sanity_check_frequency: int - Number of miliseconds between sanity checks'''
        # If something goes really wrong then we can send
        # an error message back, rather than having the program crash
        # Current example usage is if the diode_config.json is invalid
        self._in_failure_mode = False
        self._buffer = ""
        self._last_sanity = time.ticks_ms()
        self._last_msg_time = time.ticks_ms()
        self.sanity_check_frequency = sanity_check_frequency

    def set_failure_mode(self):
        self._in_failure_mode = True

    def _should_run_sanity_check(self):
        if not self.sanity_check_frequency:
            return False
        if time.ticks_ms() - self._last_sanity > self.sanity_check_frequency:
            return True

    def _sanity_check(self):
        try:
            self.do_sanity_check()
        except Exception as e:
            print(f"USBDevice ERROR: {e}")
        self._last_sanity = time.ticks_ms()

    def readUSB(self):
        gc.collect()
        cmd = ""
        while stdin in select.select([stdin], [], [], .1)[0]:            
            if self._should_run_sanity_check():
                break

            #print('Got USB serial message')
            char = stdin.read(1)
            if char not in ['\r','\n']:
                self._buffer += char
                continue

            #print(type(cmd), repr(cmd))
            
            cmd = self._buffer.strip().upper()
            self._buffer = ""
            break
        
        return cmd

    def writeUSB(self, msg):
        print(ujson.dumps(msg))
    
    def do_command(self, input_line):
        if self._in_failure_mode:
            self.writeUSB("failure")
            return
        #uncomment after debugging
        try:
            items = input_line.split()
            cmd = items[:1]
            params = items[1:]
            #print('USB:', 'cmd =', cmd, '/', 'Params =', params)
            if cmd:
                self._last_msg_time = time.ticks_ms()
                if len(params) > 0:
                    command = self._all_commands.get(cmd[0].upper(), lambda _: 'not understood')
                    self.writeUSB(command(params))
                else:
                    self.writeUSB("Commands Require an input param")
        except:
            self.writeUSB("bad command")
    
    def run(self):
        while True:
            try:
                if self._should_run_sanity_check():
                    self._sanity_check()

                cmd = self.readUSB()
                if cmd:
                    self.do_command(cmd)

            except:
                # Make sure that we don't crash from an unhandled exception.
                # It would be nice to be be able to report this error somehow
                
                # Add a sleep here. This will allow us to interrupt execution
                # from the IDE, otherwise we get into a loop where we won't be
                # able to exit
                time.sleep_ms(500)
                pass


    def on_ping(self,params):
        return {"ping":"pong"}

    @property
    def _all_commands(self):
        base_commands = {"PING?":self.on_ping,"PING":self.on_ping}
        base_commands.update(self.commands)
        return base_commands


    # These methods should be overwritten by the subclasses

    @property
    def commands(self):
        '''Returns a dictionary mapping command name to function'''
        return {}

    def do_sanity_check(self):
        '''Any perodic sanity checks that should be run'''
        pass

            