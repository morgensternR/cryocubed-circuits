import time as time
import ujson

from USBDevice import USBDevice
from LT8386 import lt8386


class WarmupHeaterManager(USBDevice):

    DEADMAN_TIMEOUT_MS = 20000

    def __init__(self, config:dict) -> None:
        super().__init__(sanity_check_frequency=1000)
        self.config = config
        self.wu_heater_dict, self.wu_heater_list = self.build_heaters(self.config)


    @property
    def commands(self):
        return {
            'I?'   : self.get_current,
            'I'    : self.set_current,
            'I_PWM?'  : self.get_current_pwm,
            'PWM?'    : self.get_pwm,
            'PWM'   : self.set_pwm,
            'EN'   : self.set_enable,
            'EN?'  : self.get_enable
            }
    #Funciton Builds Sensor dict
    
    @staticmethod
    def build_heaters(config):
        wu_dict = {}
        wu_list = []
        for i in range(len(config['heaters'])):
            name = config['heaters'][i]
            wu_list.append(name)
            wu_dict[name] = {
                         'adc pin'   : config['ismon'][i],
                         'ctrl pin': config['ctrl'][i],
                         'pwm pin'   : config['pwm'][i],
                         'switch pin' :config['switch'][i],
                         'heater_object' : lt8386(ctrl_pin = config['ctrl'][i], pwm_pin = config['pwm'][i], en_pin = config['switch'][i], ismon_pin = config['ismon'][i])
                     }   
        return wu_dict, wu_list


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
        
            

    #Gets current measurment of warmup heater in mA
    #Commands is 'I? param'
    def get_current(self,params):
        key = self.get_key(self.wu_heater_list, params[0])
        if isinstance(key, list):
            result = {}
            #wu_dict "lph ch' can only be 0 or 1 through JSON, dont need to check
            for name in key:
                result[name] = self.wu_heater_dict[name]['heater_object'].get_current()
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}
    
    #Sets ctrl pwm % decimal, see current_list files for what current to expect
    #Command is 'I param param'
    def set_current(self,params):
        key = self.get_key(self.wu_heater_list, params[0])
        if isinstance(key, list):
            if len(params) > 1:
                result = {}
                duty_percent = float(params[1])
                for name in key:
                    result[name] = self.wu_heater_dict[name]['heater_object'].set_current(duty_percent)
                return result
            else:
                return {'error': 'Must Include more than 1 param'}
        else:
            return {'error': f'Invalid Key, key = {key}'}
    #Gets CTRL PWM value
    #Command is 'I_PWM? param'
    def get_current_pwm(self,params):
        key = self.get_key(self.wu_heater_list, params[0])
        if isinstance(key, list):
            result = {}
            #wu_dict "lph ch' can only be 0 or 1 through JSON, dont need to check
            for name in key:
                result[name] = self.wu_heater_dict[name]['heater_object'].get_pwm_current_value()
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}
    #Gets WU switch Enable State, The actual output depends on the jumpers soldered on the board. short or open.etc
    #Command is 'EN? param'
    def get_enable(self, params):
        key = self.get_key(self.wu_heater_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                result[name] = self.wu_heater_dict[name]['heater_object'].get_enable()
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}

    #Sets Warmup heater enable/disable state, The actual output depends on the jumpers soldered on the board. short or open.etc
    #Command is 'EN param param'
    def set_enable(self, params):
        key = self.get_key(self.wu_heater_list, params[0])
        result = {}
        if isinstance(key, list):
            if len(params)> 1:
                if params[1].isdigit():
                    value = int(params[1])
                    if value in [0,1]:
                        for name in key:
                            if value == 1:
                                result[name] = self.wu_heater_dict[name]['heater_object'].enable()
                            else:
                                result[name] = self.wu_heater_dict[name]['heater_object'].disable()
                    else:
                        return {'error': 'Can only set enable/disable to 0 or 1'}
                else:
                    return {'error': 'Second Param must be a digit'}
            else:
                return {'error': 'Must Include more than 1 param'}
        else:
            return {'error': f'Invalid Key, key = {key}'}
        return result

    #Sets PWM % decimal of heater output
    #Command is 'PWM param'
    def set_pwm(self, params):
        key = self.get_key(self.wu_heater_list, params[0])
        if isinstance(key, list):
            if len(params) > 1:
                result = {}
                for name in key:
                    duty_percent = float(params[1])
                    result[name] = self.wu_heater_dict[name]['heater_object'].set_pwm(duty_percent)
                return result
            else:
                return {'error': 'Must Include more than 1 param'}
        else:
            return {'error': f'Invalid Key, key = {key}'}
        
    #Gets value of PWM
    #command is 'PWM? param'
    def get_pwm(self, params):
        key = self.get_key(self.wu_heater_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                result[name] = self.wu_heater_dict[name]['heater_object'].get_pwm_value()
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}

    def do_sanity_check(self):
        if time.ticks_ms() - self._last_msg_time > self.DEADMAN_TIMEOUT_MS:
            self.kill_power()

    def kill_power(self):
        for name in self.wu_heater_dict:
            self.wu_heater_dict[name]['heater_object'].set_current(0)
            self.wu_heater_dict[name]['heater_object'].set_pwm(0)
            self.wu_heater_dict[name]['heater_object'].disable()
            
            
  

if __name__ == "__main__":
    #Import Json file
    config = ujson.load(open('warmup_heater_config.json', 'r'))
    mgr = WarmupHeaterManager(config)
    mgr.run()

