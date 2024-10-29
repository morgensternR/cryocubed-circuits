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

"""
LPH Organization
Left to Right Port is 10->9->...->1
Left to Right DAC is 5->4->...->1
Left Side of Dac is channel 0, right side is channel 1
I2C can be organized however you want

LED Switch Addr set by 0b10110[AD1][AD0]
DAC Addr set by 0b01011[A2][A1][A0]
Dac dict set up by Dac # -> Channel # -> Switch EN Addr
"""
class HeaterManager(USBDevice):
    def __init__(self,config:dict) -> None:
        super().__init__(sanity_check_frequency=1000)
        self.config = config
        self.lph_switch_dic  = {
        1:{2: 'P1_0',
           1: 'P1_1'},
        2:{4: 'P0_6',
           3: 'P0_7'},
        3:{6: 'P0_4',
           5: 'P0_5'},
        4:{8: 'P0_2',
           7: 'P0_3'},
        5:{10: 'P0_0',
           9: 'P0_1'}
            }
        
        # If we can't connect immediately to the heater boards then we should keep trying until we can
        # This fixes the issue of the heaters being on full power if the Manager board had power (via usb)
        # before the actual heater boards have power.
        
        success = False
        while not success:
            try:
                self.hp_heater_dict, self.lp_heater_dict, self.heater_dict, self.hp_name_list, self.lp_name_list = self.build_heaters(config)
                success = True
            except Exception as e:
                print(f" HEATER ERROR: {e}")
                self.hp_heater_dict = None
                self.lp_heater_dict = None
                self.heater_dict = None
                self.hp_name_list = None
                self.lp_name_list = None
                #raise
                #self.set_failure_mode()
                time.sleep(1)

        
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



    def do_sanity_check(self):
        heater_dict = self.get_i([0])
        for name,current_val in heater_dict.items():
            if current_val > 30:
                self.hp_heater_dict[name]['heater object'].reset()
                current_val = 0
            expected = self.hp_heater_dict[name].get('expected_val',0)
            if current_val != expected:
                self.hp_heater_dict[name]['heater object'].dac = expected


    @staticmethod
    def build_heaters(config):
        hp_heater_dict = {}
        hp_name_list = []
        lp_heater_dict = {}
        lp_name_list = []
        heater_dict = {}
        for i in range(len(config['heaters'])):
            name = config['heaters'][i]
            heater_dict[name] = {
                         'qtpy pinout'   : config['qtpy pinout'][i],
                         'machine number': config['machine number'][i],
                         'i2c address'   : config['i2c address'][i],
                     }
            if heater_dict[name]['machine number'] >= 0:
                hp_name_list.append(name)
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
                hp_heater_dict[name]['heater object'].reset()
            else:
                lp_name_list.append(name)
                lp_heater_dict[name] = {
                         "qtpy pinout"    : config['qtpy pinout'][i],
                         'machine number' : config['machine number'][i],
                         'i2c address'    : config['i2c address'][i],
                         'switch i2c addr': config['switch i2c address'],
                         'dac num'        : config['dac num'][i],
                         'lph ch'         : config['lph ch'][i],
                         'lph port'       : config['lph port'][i]
                     }
                try:
                    lp_heater_dict[name]['i2c'] = I2C(1, scl=Pin(config['i2c'][i][0]), sda=Pin(config['i2c'][i][1]))
                except:
                    lp_heater_dict[name]['i2c'] = SoftI2C(scl = Pin(config['i2c'][i][0]), sda = Pin(config['i2c'][i][1]))
                lp_heater_dict[name]['i2c']    
                heater_object = gp.GP8403(addr = config['i2c address'][i], i2c = lp_heater_dict[name]['i2c'])
                #heater_object.begin()
                heater_object.set_dac_out_range(mode = 'OUTPUT_RANGE_10V')
                heater_object.set_dac_out_voltage(0, 0)
                heater_object.set_dac_out_voltage(0, 1)
                lp_heater_dict[name]['heater object'] = heater_object
                
                switch_object = aw.AW9523B(I2C_address = lp_heater_dict[name]['switch i2c addr']
                                                           ,i2c = lp_heater_dict[name]['i2c'] )
                lp_heater_dict[name]['switch object'] = switch_object    


    
        switch_object.reset()
        switch_object.led_mode(True)    
        return hp_heater_dict, lp_heater_dict, heater_dict, hp_name_list, lp_name_list


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
        
            

    #Gets Low Power Heater Voltage in mV
    #Commands is 'LPH_I? param'
    #Checked
    def get_lph_i(self,params):
        key = self.get_key(self.lp_name_list, params[0])
        if isinstance(key, list):
            result = {}
            #Lp_heater_dict "lph ch' can only be 0 or 1 through JSON, dont need to check
            for name in key:
                result[name] = self.lp_heater_dict[name]['heater object'].get_dac_out_voltage(self.lp_heater_dict[name]['lph ch'])
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}
    
    #Sets Low Power Heater voltage Outlpg_put in mV
    #Command is 'LPH_I param param'
    #Checked
    def set_lph_i(self,params):
        key = self.get_key(self.lp_name_list, params[0])
        if isinstance(key, list):
            if len(params) > 1:
                result = {}
                for name in key:
                    result[name] = self.lp_heater_dict[name]['heater object'].set_dac_out_voltage(params[1],
                                                                                    self.lp_heater_dict[name]['lph ch'])
                return result
            else:
                return {'error': 'Must Include more than 1 param'}
        else:
            return {'error': f'Invalid Key, key = {key}'}

    #Gets Low power Heater Channel enable/disable state
    #Command is 'LPH_EN? param'
    #Checked
    def get_lph_en(self, params):
        key = self.get_key(self.lp_name_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                result[name] = self.lp_heater_dict[name]['heater object'].get_dac_ch_en(self.lp_heater_dict[name]['lph ch'])
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}

    #Sets Low Power Heater enable/disable state
    #Command is 'LPH_EN param param'
    #Checked
    def set_lph_en(self, params):
        key = self.get_key(self.lp_name_list, params[0])
        #print(key)
        if isinstance(key, list):
            if len(params)> 1:
                if params[1].isdigit():
                    value = int(params[1])
                    if value in [0,1]:
                        for name in key:
                            self.dac_switch(name, value)
                    else:
                        return {'error': 'Can only set enable/disable to 0 or 1'}
                else:
                    return {'error': 'Second Param must be a digit'}
            else:
                return {'error': 'Must Include more than 1 param'}
        else:
            return {'error': f'Invalid Key, key = {key}'}

    #Get High Power Heater set DAC Value
    #Command is 'HPH_I? param'
    #Checked
    def get_i(self, params):
        key = self.get_key(self.hp_name_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                result[name] = self.hp_heater_dict[name]['heater object'].dac
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}
        
    #Get High Power Heater measured Voltage and Current (There's a changing 5V offset due to a diode which is why at 0 DAC there's around a 5V offset)
    #This changes with the output. Measuring the output and then subtracting this offset with respect to the load is how you 'calibrate'
    #Command is ''HPH_MON? param'
    #Checked
    def get_mon(self, params):
        key = self.get_key(self.hp_name_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                result[name] = {'v': self.hp_heater_dict[name]['heater object'].v, 'i':self.hp_heater_dict[name]['heater object'].i}
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}

    #Get High Power Heater Enabled/Disabled States (Disabled = Heater not shorted -> ON/True. Enabled = Heater Shorted -> OFF/False)
    #Command is 'HPH_EN? param'
    #Checked
    def get_en(self, params):
        key = self.get_key(self.hp_name_list, params[0])
        if isinstance(key, list):
            result = {}
            for name in key:
                result[name] = self.hp_heater_dict[name]['heater object'].enabled
            return result
        else:
            return {'error': f'Invalid Key, key = {key}'}
        
    #Sets High Power Heater DAC Value
    #Command is 'HPH_I param param'
    #Checked
    def set_i(self, params):
        key = self.get_key(self.hp_name_list, params[0])
        if isinstance(key, list):
            if len(params) > 1:
                if params[1].isdigit():
                    dac_value = int(params[1])
                    if 30 >= dac_value >= 0:
                        result = {}
                        for name in key:
                            self.hp_heater_dict[name]['expected_val'] = dac_value
                            self.hp_heater_dict[name]['heater object'].dac = dac_value
                            result[name] = self.hp_heater_dict[name]['heater object'].dac
                        return result
                    else:
                        return {'error': 'Second param must be a digit 30 >= param >= 0'}
                else:
                    return {'error': 'Second param must be a digit'}
            else:
                return {'error': 'Must Include more than 1 param'}
        else:
            return {'error': f'Invalid Key, key = {key}'}
        
    #Sets High Power Heater Enabled/Disabled States (Disabled = Heater not shorted -> ON. Enabled = Heater Shorted -> OFF)
    #Command is 'HPH_EN param param'
    #Checked
    def set_en(self, params):
        key = self.get_key(self.hp_name_list, params[0])
        if len(params) > 1:
            if params[1].isdigit():
                params = int(params[1])
                if params in [0,1]:
                    for name in key:
                        if params == 0:    
                            self.hp_heater_dict[name]['heater object'].disable()
                        else:
                            self.hp_heater_dict[name]['heater object'].enable()
                else:
                    return {'error': 'Can only set enable/disable to 0 or 1'}
            else:
                return {'error': 'Second param must be a digit'}
        else:
            return {'error': 'Must Include more than 1 param'}
    
     
    def dac_switch(self, key, enable):
        if enable == 1:
            switch_key = self.lph_switch_dic[self.lp_heater_dict[key]['dac num']][self.lp_heater_dict[key]['lph port']]
            #print(switch_key)
            self.lp_heater_dict[key]['switch object'].current_dim(switch_key, 253)
            self._store_dac_en(key, enable, self.lp_heater_dict[key]['lph ch'])
        else:
            switch_key = self.lph_switch_dic[self.lp_heater_dict[key]['dac num']][self.lp_heater_dict[key]['lph port']]
            self.lp_heater_dict[key]['switch object'].current_dim(switch_key, 0)
            self._store_dac_en(key, enable, self.lp_heater_dict[key]['lph ch'])
    
    def _store_dac_en(self,key, enable, channel_num):
        en_state = bool(enable)
        if channel_num == 0:
            self.lp_heater_dict[key]['heater object'].en_ch1 = en_state
        if channel_num == 1:
            self.lp_heater_dict[key]['heater object'].en_ch2 = en_state
        if channel_num == 2:
            self.lp_heater_dict[key]['heater object'].en_ch1 = en_state
            self.lp_heater_dict[key]['heater object'].en_ch1 = en_state

