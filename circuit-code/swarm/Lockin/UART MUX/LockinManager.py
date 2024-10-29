from machine import Pin, UART, I2C
import time as time
from sys import stdin, stdout, exit
import select
import gc
from sn74 import SN74LV4052A
from PCA8550 import PCA8550
from USBDevice import USBDevice


class LockinManager(USBDevice):
    def __init__(self,config:dict) -> None:
        super().__init__()
        self.config = config
        #The below are hard-coded due to PCB design
        #Start Uart
        self.uart = UART(0,9600, timeout=2000)
        #Start I2C
        self.i2c = I2C(1, scl=Pin(7), sda=Pin(6))
        #Start GPIO Pins
        self.pinA = Pin(2, Pin.OUT, value = 0)
        self.pinB = Pin(3, Pin.OUT, value = 0)

            
        self.lockin_dict, self.lockin_list = self.build_lockins(config)
        try:
            self.lockin_dict, self.lockin_list = self.build_lockins(config)

        except:
            self.lockin_dict = None
            self.lockin_list = None
            self.set_failure_mode()
        #Same PCA8550 is used per UART Mux board. Requires single object since it changes enable/disable based on register stored in class
        self.power_switch = PCA8550(i2c_device = I2C(1, scl=Pin(self.config['i2c'][0][0]), sda=Pin(self.config['i2c'][0][1])))
        self.power_switch.disable_all()
        self.power_switch.enable_all()
        
    @property
    def commands(self):
        return {
            'RESET'   : self.reset,
            'ENABLE' : self.set_enable,
            'DISABLE'  : self.set_disable,
            'R?'    : self.get_reading,
            'RA?'   : self.get_running_average,
            'LAST?'   : self.get_last_reading,
            'BIAS?'  : self.get_bias,
            'BIAS'    : self.set_bias,
            }
    #Funciton Builds Sensor dict
    
    @staticmethod
    def build_lockins(config):
        lockin_dict = {}
        lockin_list = []
        for i in range(len(config['lockins'])):
            name = config['lockins'][i]
            lockin_list.append(name)
            lockin_dict[name] = {
                         'mux address'   : config['mux address'][i],
                         'power address' : config['power address'][i],
                         'wire count'    : config['wire count'][i],
                         #'power switch'  : PCA8550(i2c_device = I2C(1, scl=Pin(config['i2c'][i][0]), sda=Pin(config['i2c'][i][1]))),
                         'mux'           : SN74LV4052A(Pin(config['mux pins'][i][0], Pin.OUT, value = 0), Pin(config['mux pins'][i][1], Pin.OUT, value = 0))
                         }
                         
        
        return lockin_dict, lockin_list


    def get_key(self, input_list, input_param):
            #Correct key output will always be a list, anything else is error
            #print(input_param, type(input_param), input_list)
            try:
                if isinstance(input_param, int) or input_param.isdigit():
                    index = int(input_param) - 1
                    if len(input_list) > index >= 0:
                            key = input_list[index]
                            return list([key])
                    elif index == -1:
                        key_list = []
                        for name in input_list:
                            key_list.append(name) 
                        return key_list
                    else:  #  handle all other numbers
                        result = 'invalid heater number'
                        return {'error':result}
                elif isinstance(input_param, str):
                    key = input_param.upper()
                    if key in input_list:
                        return list([key])
                    else:
                        result = 'invalid name for heater'
                        return {'error':result}
            except:
                return {'except error': f'{input_param} is an Invalid Key'}       



    #Resets a given Lockin or all Lockins
    #Command is 'RESET param'
    #
    def reset(self, params):
        key = self.get_key(self.lockin_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                self.power_switch.disable_output(self.lockin_dict[name]['power address'])
                self.power_switch.enable_output(self.lockin_dict[name]['power address'])
                result[name] = 'Done'
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}

    #Sets Lockin enable state
    #Command is 'ENBABLE param'
    #
    def set_enable(self, params):
        key = self.get_key(self.lp_name_list, params[0])
        if isinstance(key, list):
            for name in key:
                self.power_switch.enable_output(self.lockin_dict[name]['power address'])
        else:
            return {'error': f'Invalid Key, key = {key}'}
    #Sets Lockin enable state
    #Command is 'DISABLE param'
    #
    def set_disable(self, params):
        key = self.get_key(self.lp_name_list, params[0])
        if isinstance(key, list):
            for name in key:
                self.power_switch.disable_output(self.lockin_dict[name]['power address'])
        else:
            return {'error': f'Invalid Key, key = {key}'}
    #Gets Lockin current reading. Will try 5 times to read the UART mux line. If it fails, the lockin may require resetting if there is no no hardware Errors. Also Check for 5V on UART Mux (JST 2 Pin Connector)
    #Command is 'read param'
    #    
    def get_reading(self, params):
        key = self.get_key(self.lockin_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                self.lockin_dict[name]['mux'].choose_output(self.lockin_dict[name]['mux address'])
                cmd = f'R?' + '\n'
                cmd = cmd.encode()
                self.uart.write(cmd)
                self.uart.flush()
                time.sleep(0.010)
                
                for attempt in range(10):
                #for name in key:
                    if name in result:
                        continue

                    self.lockin_dict[name]['mux'].choose_output(self.lockin_dict[name]['mux address'])
                    response = self.uart.readline()
                    if response:
                        result[name] = response
                    
            for name in key:
                if name not in result:
                    result[name] = {'error': f'Failed to read Lockin {name}'}                    
        else:
            result = {'error': f'Invalid Key, key = {key}'}
        return result

    def get_running_average(self, params):
        key = self.get_key(self.lockin_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                self.lockin_dict[name]['mux'].choose_output(self.lockin_dict[name]['mux address'])
                cmd = f'RA?' + '\n'
                cmd = cmd.encode()
                self.uart.write(cmd)
                failed_counter = 0
                while True:
                    response = self.uart.readline()
                    if response is None:  # sometimes the request to readline happens to fast... try again
                        if failed_counter == 5:
                            response = {'error': f'Failed to read Lockin {name}'}
                            break;
                        failed_counter += 1
                    else:
                        break
                result[name] = response
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}
        
    def get_last_reading(self, params):
        key = self.get_key(self.lockin_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                self.lockin_dict[name]['mux'].choose_output(self.lockin_dict[name]['mux address'])
                cmd = f'LAST?' + '\n'
                cmd = cmd.encode()
                self.uart.write(cmd)
                failed_counter = 0
                while True:
                    response = self.uart.readline()
                    if response is None:  # sometimes the request to readline happens to fast... try again
                        if failed_counter == 5:
                            response = {'error': f'Failed to read Lockin {name}'}
                            break;
                        failed_counter += 1
                    else:
                        break
                result[name] = response
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}
        
    def get_bias(self, params):
        key = self.get_key(self.lockin_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                self.lockin_dict[name]['mux'].choose_output(self.lockin_dict[name]['mux address'])
                cmd = f'BIAS?' + '\n'
                cmd = cmd.encode()
                self.uart.write(cmd)
                failed_counter = 0
                while True:
                    response = self.uart.readline()
                    if response is None:  # sometimes the request to readline happens to fast... try again
                        if failed_counter == 5:
                            response = {'error': f'Failed to read Lockin {name}'}
                            break;
                        failed_counter += 1
                    else:
                        break
                result[name] = response
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}       
    def set_bias(self, params):
            key = self.get_key(self.lockin_list, params[0])
            if isinstance(key, list):
                if len(params) > 1:
                    result = {}
                    for name in key:
                        self.lockin_dict[name]['mux'].choose_output(self.lockin_dict[name]['mux address'])
                        cmd = f'BIAS ' + params[1] + '\n'
                        cmd = cmd.encode()
                        self.uart.write(cmd)
                        failed_counter = 0
                        while True:
                            response = self.uart.readline()
                            if response is None:  # sometimes the request to readline happens to fast... try again
                                if failed_counter == 5:
                                    response = {'error': f'Failed to read Lockin {name}'}
                                    break;
                                failed_counter += 1
                            else:
                                break
                        result[name] = response
                    return result
                else:
                    return {'error': f'Must have a second param for high or low bias'}
            else:
                return {'error': f'Invalid Key, key = {key}'}
            
            

