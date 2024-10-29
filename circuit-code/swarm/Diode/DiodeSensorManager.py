import mcp3421 as mcp
import tca9548a as mux
from machine import I2C, Pin, SoftI2C
import time as time
from sys import stdin, stdout, exit
import select
import gc
from USBDevice import USBDevice

class DiodeSensorManager(USBDevice):
    def __init__(self,config:dict) -> None:
        super().__init__()
        self.config = config
        self.sensor_dict = self.build_sensors(config)

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
                    self.sensor_dict[key]['mux'].write_reg(self.sensor_dict[key]['mux port address'])
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
#if __name__ == "__main__":
    #Import Json file