from machine import I2C, Pin, SoftI2C
import time as time
from sys import stdin, stdout, exit
import select
import gc
import ujson

from USBDevice import USBDevice
import AW9523B as aw
import gp8403 as gp
from high_power_heater_v2 import High_power_heater_board

class HeaterManager(USBDevice):
    def __init__(self,config:dict) -> None:
        super().__init__()
        self.config = config
        self.lph_switch_dic  = {
        1:{1: 'P1_0',
           2: 'P1_1'},
        2:{1: 'P0_6',
           2: 'P0_7'},
        3:{1: 'P0_4',
           2: 'P0_5'},
        4:{1: 'P0_2',
           2: 'P0_3'},
        5:{1: 'P0_0',
           2: 'P0_1'}
            }
        self.command_dict = {
            
            
            
            }
        
        self.hp_heater_dict, self.lp_heater_dict, self.heater_dict = self.build_heaters(config)

        '''
        try:
            self.hp_heater_dict, self.lp_heater_dict, self.heater_dict = self.build_heaters(config)
        except:
            self.heater_dict = None
            self.hp_heater_dict = None
            self.lp_heater_dict = None
            self.set_failure_mode()
        '''
    @property
    def commands(self):
        return {
            'HPH_I?'   : self.get_i,
            'HPH_MON?' : self.get_mon,
            'HPH_EN?'  : self.get_en,
            'HPH_I'    : self.set_i,
            'HPH_EN'   : self.set_en,
            'LPH_I?'   : self.get_lph_i,
            'LPH_EN?'  : self.get_lph_en,
            'LPH_I'    : self.set_lph_i,
            'LPH_EN'   : self.set_lph_en
            }
    #Funciton Builds Sensor dict
    
    @staticmethod
    def build_heaters(self):
        hp_heater_dict = {}
        lp_heater_dict = {}        
        heater_dict = {}
        for i in range(len(config['heaters'])):
            name = config['heaters'][i]
            heater_dict[name] = {
                         'qtpy pinout'   : config['qtpy pinout'][i],
                         'machine number': config['machine number'][i],
                         'i2c address'   : config['i2c address'][i],
                         'switch addr'   : config['switch addr'][i],
                         'lph ch'        : config['lph channel'][i]
                     }
            if heater_dict[name]['machine number'] >= 0:
                
                hp_heater_dict[name] = {
                        "qtpy pinout"   : config['qtpy pinout'][i],
                        'machine number': config['machine number'][i],
                        'i2c address'   : config['i2c address'][i],
                    }
                try:
                    hp_heater_dict[name]['i2c'] = I2C(1, scl=Pin(config['i2c'][i][0]), sda=Pin(config['i2c'][i][1]))
                except:
                    hp_heater_dict[name]['i2c'] = SoftI2C(scl = Pin(config['i2c'][i][0]), sda = Pin(config['i2c'][i][1]))
                    
                heater_object = High_power_heater_board(out_pin = heater_dict[name]['qtpy pinout'][0],
                                            enable_pin = heater_dict[name]['qtpy pinout'][1],
                                            machine_number = heater_dict[name]['machine number'],
                                            addr = heater_dict[name]['i2c address'], name = name,
                                            i2c = hp_heater_dict[name]['i2c'])
                
                hp_heater_dict[name]['heater object'] = heater_object
                
            else:
                lp_heater_dict[name] = {
                         "qtpy pinout"   : config['qtpy pinout'][i],
                         'machine number': config['machine number'][i],
                         'i2c address'   : config['i2c address'][i],
                         'switch addr'   : config['switch addr'][i],
                         'lph ch'        : config['lph channel'][i]
                     }
                try:
                    lp_heater_dict[name]['i2c'] = I2C(1, scl=Pin(config['i2c'][i][0]), sda=Pin(config['i2c'][i][1]))
                except:
                    lp_heater_dict[name]['i2c'] = SoftI2C(scl = Pin(config['i2c'][i][0]), sda = Pin(config['i2c'][i][1]))
                lp_heater_dict[name]['i2c']    
                heater_object = gp.GP8403(addr = config['i2c address'][i], i2c = lp_heater_dict[name]['i2c'])
                #heater_object.begin()
                #heater_object.set_dac_out_range(mode = 'OUTPUT_RANGE_10V')
                #heater_object.set_dac_out_voltage(0, 0)
                #heater_object.set_dac_out_voltage(0, 1)
                lp_heater_dict[name]['heater object'] = heater_object
                switch_object = aw.AW9523B(I2C_address = 91, i2c = lp_heater_dict[name]['i2c'] )
                #switch_object.reset()
                #switch_object.led_mode(True)
                lp_heater_dict[name]['switch object'] = switch_object    


    
            
        return hp_heater_dict, lp_heater_dict, heater_dict


    def get_key(self, input_param):
        try:
            if isinstance(input_param, int) or input_param.isdigit():
                index = int(input_param) - 1 
                if len(self.heater_dict) > index >= 0:
                        result = {}
                        key = list(self.heater_dict.keys())[index]
                        return key
                elif index == -1:
                    key_list = []
                    for name in self.heater_dict:                
                       key_list.append(name) 
                    return key_list
                else:  #  handle all other numbers
                    result = 'invalid heater number'
                    return {'error':result}
            elif isinstance(input_param, str):
                key = input_param
                if key in self.heater_dict:
                    return key
                else:
                    result = 'invalid name for heater'
                    return {'error':result}
        except:
            return {'error': 'Invalid Key'}
        
    def key_result(self, key, function, param = None):
        #If dict, it's an error emssage
        if isinstance(key, dict):
            return key
        elif isinstance(key, list):
            result = {}
            for name in key:
                result[name] = self.command_dict[function]
            return result
        elif isinstance(key, str):
            result = {key: self.command_dict[function]}
            return result
        #Anythign else is an error
        else:
            print('Somehow got a key I cant handle')
            
    def get_lph_i(self,params):
        key = self.get_key(params[0])
        return self.key_result(key, self.lp_heater_dict[key]['heater_object'].get_dac_out_voltage(self.lp_heater_dict[key]['lph ch']))
        
    def set_lph_i(self,params):
        key = self.get_key(params[0])
        return self.key_result(key, self.lp_heater_dict[key]['heater_object'].get_dac_out_voltage(self.lp_heater_dict[key]['lph ch']))
  
        #TODO FIX ME
    def get_lph_en(self, params):
        key = self.get_ke(params[0])
        
        return self.key_result(key, self.lp_heater_dict[key]['heater_object'].get_dac_out_voltage(self.lp_heater_dict[key]['lph ch']))
    def set_lph_en(self, params):
        key = self.get_ke(params[0])
        return self.key_result(key, self.lp_heater_dict[key]['heater_object'].get_dac_out_voltage(self.lp_heater_dict[key]['lph ch']))

    #Get High Power Heater set DAC Value
    def get_i(self, params):
        key = self.get_key(params[0])
        return self.key_result(key, self.hp_heater_dict[key]['heater_object'].dac)

    #Get High Power Heater measured Voltage and Current (There's a changing 5V offset due to a diode which is why at 0 DAC there's around a 5V offset)        
    def get_mon(self, params):
        key = self.get_key(params[0])
        return self.key_result(key, {'v': self.hp_heater_dict[key]['heater_object'].v, 'i':self.hp_heater_dict[key]['heater_object'].i})
        
    #Get High Power Heater Enabled/Disabled States (Disabled = Heater not short / ON. Enabled = Heater Shorted / OFF)        
    def get_en(self, params):
        key = self.get_key(params[0])
        return self.key_result(key, self.hp_heater_dict[key]['heater_object'].enabled )
     
    #Set High Power Heater DAC Value
    def set_i(self, params):
        if len(params) > 1:
            key = self.get_key(params[0])
            dac_value = int(float(params[1]))
            self.get_key(params)
            if isinstance(key, dict):
                return key
            #if Key is a list, It's a list of keys in which I run a For loop for the specific Dict
            elif isinstance(key, list):
                result = {}
                for name in key:
                    result[name] = self.hp_heater_dict[name]['heater_object'].dac = dac_value
                return result
            #if Key is a string, it's a single key retreived by either a int or a key string
            elif isinstance(key, str):
                hp_heater_dict[key]['heater object'].dac = dac_value
                result = {key: self.hp_heater_dict[key]['heater_object'].dac}
                return result
            #Anythign else is an error
            else:
                print('Somehow got a key I cant handle')       
                
        else:
            result = 'bad command'
            return {'error':result}
    #Set High Power Heater Enabled or Disabled
    def set_en(self, params):
        if len(params) > 1:
            key = self.get_key(params[0])
            en_value = int(float(params[1]))
            if isinstance(key, dict):
                return key
            #if Key is a list, It's a list of keys in which I run a For loop for the specific Dict
            elif isinstance(key, list):
                result = {}
                for name in key:
                    if en_value == 0:
                        result[name] = self.hp_heater_dict[name]['heater_object'].disable()
                    else:
                        result[name] = self.hp_heater_dict[name]['heater_object'].enable()
                return result
            #if Key is a string, it's a single key retreived by either a int or a key string
            elif isinstance(key, str):
                if en_value == 0:
                    #self.hp_heater_dict[name]['heater_object'].disable()
                    result = {key: self.hp_heater_dict[key]['heater_object'].disabled()}
                else:
                    #self.hp_heater_dict[name]['heater_object'].enabled()
                    result = {key: self.hp_heater_dict[key]['heater_object'].enabled()}
                return result
            #Anythign else is an error
            else:
                print('Somehow got a key I cant handle')       
        else:
            result = 'bad command'
            return {'error':result}
        
        
        
        
    def dac_switch(self,key, enable= 3):
        if enable == 1:
            self.lp_heater_dict[key]['switch object'].current_dim(self.lp_heater_dict[key]['switch addr'], 253)
            self._store_dac_en(enable, self.lp_heater_dict[key]['lph ch'])
        elif enable == 0:
            self.lp_heater_dict[key]['switch object'].current_dim(self.lp_heater_dict[key]['switch addr'], 0)
            self._store_dac_en(enable, self.lp_heater_dict[key]['lph ch'])
            
        '''
        elif enable == 3:
            for dac in dac_switch_dic:
                for channel in dac_switch_dic[dac]:
                    switch.current_dim(dac_switch_dic[dac][channel], 253)
            
        elif enable == 4:
            for dac in dac_switch_dic:
                for channel in dac_switch_dic[dac]:
                    switch.current_dim(dac_switch_dic[dac][channel], 0)
        '''
        return
    
    def _store_dac_en(self,enable, channel_num):
        en_state = bool(enable)
        if channel_num == 0:
            self.lp_heater_dict[key]['heater object'].en_ch1 = en_state
        if channel_dum == 1:
            self.lp_heater_dict[key]['heater object'].en_ch2 = en_state
        if channel_dum == 2:
            self.lp_heater_dict[key]['heater object'].en_ch1 = en_state
            self.lp_heater_dict[key]['heater object'].en_ch1 = en_state









if __name__ == "__main__":
    #Import Json file
    config = ujson.load(open('heater_config.json', 'r'))
    mgr = HeaterManager(config)
    mgr.run()