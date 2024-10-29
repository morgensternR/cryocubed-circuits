import mcp3421 as mcp
import tca9548a as mux
from machine import I2C, Pin, SoftI2C
import time as time
from sys import stdin, stdout, exit
import select
import gc
import ujson
from abc import ABC, abstractmethod


#Move this class to a different file
class USBDevice(ABC):
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
    @abstractmethod
    def commands(self):
        '''This should be the mapping of command strings to methods'''
        pass

    def do_command(self, input_line):
        if self._in_failure_mode:
            self.writeUSB("failure")
            return

        try:
            items = input_line.split()
            cmd = items[:1]
            params = items[1:]
        
            if cmd:
                command = self.commands.get(cmd.upper(), lambda _: 'not understood')
                self.writeUSB(command(params))
        except:
            self.writeUSB("bad command")

    def run(self):
        while True:
            self.readUSB()



class DiodeSensorManager(USBDevice):
    def __init__(self,config:dict) -> None:
        super().__init__()
        self.config = config
        try:
            self.sensor_dict = self.build_sensors(config)
        except:
            self.sensor_dict = None
            self.set_failure_mode()

    @property
    def commands(self):
        return {
            "V?":self.get_adc
        }

    def get_adc(self, params:list[str]):

        if params[0].isdigit():
            index = int(params[0]) - 1 #1-10 give respective diode board, 0 gives index -1 which means all boards, does not exceed max length
            
            if len(self.sensor_dict) > index >= 0:
                result = {}
                key = self.config['sensors'][index]
                
                if self.sensor_dict[key]['mux'] != None:
                    self.sensor_dict[key]['mux'].write_reg(index)
                result = {key: self.sensor_dict[key]['adc'].read_adc_v()}
                return result
            
            elif index == -1:
                result = {}
                for name in self.sensor_dict:
                    if self.sensor_dict[name]['mux'] != None:
                        self.sensor_dict[name]['mux'].write_reg(self.sensor_dict[name]['mux port address'])
                    
                    result[name] = self.sensor_dict[name]['adc'].read_adc_v()
                return result
            
            else:  #  handle all other numbers
                result = 'invalid sensor number for V?'
                return {'error':result}
            
        else:
            key = params[0]
            if key in self.sensor_dict:

                if self.sensor_dict[key]['mux'] != None:

                    self.sensor_dict[key]['mux'].write_reg(self.sensor_dict[key]['mux port address'])
                    
                result = {key: self.sensor_dict[key]['adc'].read_adc_v()}
                return result
            else:
                result = 'invalid name of the channel for V?'
            return {'error':result}
                    
            
    #Funciton Builds Sensor dict
    @staticmethod
    def build_sensors(config):
        sensors = {}
        for i in range(len(config['sensors'])):
            name = config['sensors'][i]
            sensors[name] = {
                    'mux port address' : config['mux port address'][i],
                    'slope correction 16bit': config['slope correction 16bit'][i],
                    'offset correction' : config['offset correction'][i],
                    'i2c port' : config['i2c'][i],
                    'i2c interface' : config['i2c interface'][i]
                }
            try:#Assumes hardware i2c, if fails assumes software i2c
                sensors[name]['i2c'] = I2C(1, scl=Pin(sensors[name]['i2c port'][0]), sda=Pin(sensors[name]['i2c port'][1]))
            except:
                sensors[name]['i2c'] = SoftI2C(scl = Pin(sensors[name]['i2c port'][0]), sda = Pin(sensors[name]['i2c port'][1]))
                
            if sensors[name]['mux port address'] != None:
                sensors[name]['mux'] = mux.TCA9548A(sensors[name]['i2c'])
                sensors[name]['mux'].write_reg(sensors[name]['mux port address'])
            else:
                sensors[name]['mux'] = None
                
            sensors[name]['adc'] = mcp.MCP3421(i2c = sensors[name]['i2c'], slope = sensors[name]['slope correction 16bit'],
                                offset = sensors[name]['offset correction'])
                  
        return sensors


# Does the MicroPython stuff use __main__?
# If not then we should move the DiodeSensorManager to another file
if __name__ == "__main__":
    #Import Json file
    config = ujson.load(open('diode_config.json', 'r'))
    mgr = DiodeSensorManager(config)
    mgr.run()
