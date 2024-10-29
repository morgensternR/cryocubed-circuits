from sys import stdin, stdout, exit
import time
import select
import gc
import ujson
import machine
from high_power_heater_v2 import High_power_heater_board
import AW9523B as aw
import gp8403 as gp
i2c = I2C(1, scl=machine.Pin(23), sda=machine.Pin(22), freq=40000)

#LED Driver Control Output Switches.
#switch = aw.AW9523B(I2C_address = 91, i2c = i2c)
switch.reset()
switch.led_mode(True)
#Inits 5 x Dacs with same I2C Bus
#dac1 = gp.GP8403(addr = 94, i2c = i2c)
#dac2 = gp.GP8403(addr = 92, i2c = i2c)
#dac3 = gp.GP8403(addr = 88, i2c = i2c)
#dac4 = gp.GP8403(addr = 93, i2c = i2c)
#dac5 = gp.GP8403(addr = 95, i2c = i2c)
#dac_list = [dac1,dac2,dac3,dac4,dac5]

#Sets output range to 10V for all dacs
#for dac in dac_list:
#    dac.begin()
#    dac.set_dac_out_range(mode = 'OUTPUT_RANGE_10V')
#    dac.set_dac_out_voltage(0, 0)
#    dac.set_dac_out_voltage(0, 1)
    #time.sleep(1)
#Function for controling the output switches for the DACs
    #1 = Single dac enable
    #2 = Single dac disable
    #3 = All dac enable
    #4 = All dac disable
def dac_switch(dac_num, channel_num, enable= 3):
    if enable == 1:
        switch.current_dim(dac_switch_dic[dac_num][channel_num], 253)
    elif enable == 0:
        switch.current_dim(dac_switch_dic[dac_num][channel_num], 0)
    elif enable == 3:
        for dac in dac_switch_dic:
            for channel in dac_switch_dic[dac]:
                switch.current_dim(dac_switch_dic[dac][channel], 253)
    elif enable == 4:
        for dac in dac_switch_dic:
            for channel in dac_switch_dic[dac]:
                switch.current_dim(dac_switch_dic[dac][channel], 0)
    return


#Each Dac has 2 Channels. 5 Dacs * 2 Channels = 10 Outputs
dac_switch_dic = {
    1: {
        1: 'P1_0',
        2: 'P1_1'
        },
   2:{
        1: 'P0_6',
        2: 'P0_7'
        },
    3:{
        1: 'P0_4',
        2: 'P0_5'
        },
    4:{
        1: 'P0_2',
        2: 'P0_3'
        },
    5:{
        1: 'P0_0',
        2: 'P0_1'
        }
    }

#Import Json file
config = ujson.load(open('heater_config.json', 'r'))
#Funciton Builds heater dict
def build_heaters(config):
    heater_dict = {}
    hp_heater_list = []
    lph_dict = []
    for i in range(len(config['heaters'])):
        name = config['heaters'][i]
        heater_dict[name] = {
                "qtpy pinout" : config['qtpy pinout'][i],
                'machine number': config['machine number'][i],
                'address' : config['address'][i],
            }            
        if heater_dict[name]['machine number'] >= 0:
            heater_object = High_power_heater_board(out_pin = heater_dict[name]['qtpy pinout'][0],
                                        enable_pin = heater_dict[name]['qtpy pinout'][1],
                                        machine_number = heater_dict[name]['machine number'],
                                        addr = heater_dict[name]['address'], name = name)
            
            heater_dict[name]['heater object'] = heater_object
            hp_heater_list.append(heater_object)
            
        else:
            heater_object = gp.GP8403(addr = config['address'][i], i2c = i2c)
            heater_object.begin()
            heater_object.set_dac_out_range(mode = 'OUTPUT_RANGE_10V')
            heater_object.set_dac_out_voltage(0, 0)
            heater_object.set_dac_out_voltage(0, 1)
            
            switch_object = aw.AW9523B(I2C_address = 91, i2c = i2c)
            switch.reset()
            switch.led_mode(True)
            
            heater_dict[name]['heater object'] = heater_object
            heater_dict[name]['switch object'] = switch_object
            heater_dict[name]['switch addr'] =config['switch addr'][i]


        
    return heater_dict, hp_heater_list, lph_list

heater_dict, hp_heaters, lph_list = build_heaters(config)

hph_i_limit =50
def heater_state_check():
    global hph_i_limit
    for heater in hp_heaters:
        if heater.i > hph_i_limit:
            heater.reset()
            #writeUSB(f'Heater [{hex(heater.addr)}, {heater.name}] exceeded 50mA')
            #Commented this out to not have read errors. Could be usful to see when heater boards power cycle. 

    
# heaters = [heater]
#lph = BH2221(out=20, clk_ld=5)
#lph_list=['4SWITCHA', '3SWITCHA', '4SWITCHB', '3SWITCHB', 'STILL']

def readUSB():
    global ONCE, CONTINUOUS, last, hph_i_limit
    gc.collect()
    # Does the USB really come in on stdin?
    # Or is this just for testing?
    while stdin in select.select([stdin], [], [], 0)[0]:
        #print('Got USB serial message')
        gc.collect()

        cmd = stdin.readline()
        #print(type(cmd), repr(cmd))
        cmd = cmd.strip().upper()
        if len(cmd)>0:
            do_command(cmd)

def writeUSB(msg):
    # Same question as stdin on readUSB
    print(ujson.dumps(msg))
commands = {
    'HPH_I?' : get_i,
    'HPH_MON?' : get_mon,
    'HPH_EN?' : get_en,
    'HPH_I' : set_i,
    'HPH_EN': set_en,
    
    
    
    
    }



def get_i(params):
    if params[0].isdigit(): = {
    1: {
        1: 'P1_0',
        2: 'P1_1'
        },
   2:{
        1: 'P0_6',
        2: 'P0_7'
        },
    3:{
        1: 'P0_4',
        2: 'P0_5'
        },
    4:{
        1: 'P0_2',
        2: 'P0_3'
        },
    5:{
        1: 'P0_0',
        2: 'P0_1'
        }
    }
        index = int(params[0]) - 1 #1-10 give respective diode board, 0 gives index -1 which means all boards, does not exceed max length
        if len(heaters) > index >= 0:
            result = {}
            key = heaters[index]
            result = {key: heater_dict[key]['heater_object'].dac}
            return result
        elif index == -1:
            result = {}
                for name in heater_dict:                
                    try:
                        result[name] = heater_dict[name]['heater_object'].dac
                    except:
                        pass
            return result
        else:  #  handle all other numbers
            result = 'invalid hph number'
            return {'error':result}
    else:
        key = params[0]
        if key in heater_dict:
            try:
                result = {key: heater_dict[key]['heater_object'].dac}
            except:
                result = 'invalid'
            return result
        else:
            result = 'invalid name for hph'
        return {'error':result}

def get_mon(params):
    if params[0].isdigit():
        index = int(params[0]) - 1 #1-10 give respective diode board, 0 gives index -1 which means all boards, does not exceed max length
        if len(heaters) > index >= 0:
            result = {}
            key = heaters[index]
            result = {key: {'v': heater_dict[key]['heater_object'].v, 'i':heater_dict[key]['heater_object'].i}}
            return result
        elif index == -1:
            result = {}
                for name in heater_dict:                
                    try:
                        result[key] = {'v': heater_dict[key]['heater_object'].v, 'i':heater_dict[key]['heater_object'].i}
                    except:
                        pass
            return result
        else:  #  handle all other numbers
            result = 'invalid hph number'
            return {'error':result}
    else:
        key = params[0]
        if key in heater_dict:
            try:
                result = {key: {'v': heater_dict[key]['heater_object'].v, 'i':heater_dict[key]['heater_object'].i}}
            except:
                result = 'invlaid'
            return result
        else:
            result = 'invalid name for hph'
            return {'error':result}
    
def get_en(params):
    if params[0].isdigit():
        index = int(params[0]) - 1 #1-10 give respective diode board, 0 gives index -1 which means all boards, does not exceed max length
        if len(heaters) > index >= 0:
            result = {}
            key = heaters[index]
            result = {key: heater_dict[key]['heater_object'].enabled}
            return result
        elif index == -1:
            result = {}
                for name in heater_dict:                
                    try:
                        result[name] = heater_dict[name]['heater_object'].enabled
                    except:
                        pass
            return result
        else:  #  handle all other numbers
            result = 'invalid hph number'
            return {'error':result}
        
    else:
        key = params[0] = {
    1: {
        1: 'P1_0',
        2: 'P1_1'
        },
   2:{
        1: 'P0_6',
        2: 'P0_7'
        },
    3:{
        1: 'P0_4',
        2: 'P0_5'
        },
    4:{
        1: 'P0_2',
        2: 'P0_3'
        },
    5:{
        1: 'P0_0',
        2: 'P0_1'
        }
    }
        if key in heater_dict:
            try:   
                result = {key: heater_dict[key]['heater_object'].enabled}
            except:
                result = 'invalid'
            return result
        else:
            result = 'invalid name for hph'
        return {'error':result}
    
def set_i(params):
    if len(params) > 1:
        dac_value = int(float(params[1]))
        if channel.isdigit():
            channel = int(params[0])
            index = int(channel) - 1
            if len(heaters) > index >= 0:
                result = {} = {
    1: {
        1: 'P1_0',
        2: 'P1_1'
        },
   2:{
        1: 'P0_6',
        2: 'P0_7'
        },
    3:{
        1: 'P0_4',
        2: 'P0_5'
        },
    4:{
        1: 'P0_2',
        2: 'P0_3'
        },
    5:{
        1: 'P0_0',
        2: 'P0_1'
        }
    }
                key = heaters[index]
                heater_dict[key]['heater object'].dac = dac_value
                result = {key: heater_dict[key]['heater_object'].dac}
                return result
        else:
             key = params[0]
             if key in heater_dict:
                 try:
                     heater_dict[key]['heater object'].dac = dac_value
                     result = {key: heater_dict[key]['heater_object'].dac}
                 except:
                     result = 'invalid'
                 return result
             else:
                 result = 'invalid name for hph'
             return {'error':result}  
    else:
        result = 'Bad Command'
        return result
    
def set_en(params):
    if len(params) > 1:
        en_value = int(float(params[1]))
        if channel.isdigit():
            channel = int(params[0])
            index = int(channel) - 1
            if len(heaters) > index >= 0:
                result = {}
                key = heaters[index]
                if en_value = 0:
                    heater_dict[key]['heater object'].disable()
                else:
                    heater_dict[key]['heater object'].enable()
                result = 'done'
                return result
        else:
             key = params[0]
             if key in heater_dict:
                 try:
                     if en_value = 0:
                         heater_dict[key]['heater object'].disable()
                     else:
                         heater_dict[key]['heater object'].enable()
                     result = 'done'
                 except:
                     result = 'invalid'
                 return result
             else:
                 result = 'invalid name for hph'
             return {'error':result}  
    else:
        result = 'Bad Command'
        return result
    
    
        
 = {
    1: {
        1: 'P1_0',
        2: 'P1_1'
        },
   2:{
        1: 'P0_6',
        2: 'P0_7'
        },
    3:{
        1: 'P0_4',
        2: 'P0_5'
        },
    4:{
        1: 'P0_2',
        2: 'P0_3'
        },
    5:{
        1: 'P0_0',
        2: 'P0_1'
        }
    }
# I like how you did the do_command in diode_assm_query
# I'd recommend doing the same thing here.  If you do that
# then you can write a base USBInterface class so you can 
# share that interface code across all your devices
def do_command(cmd):
    # We should really have a try/except wrapping this function
    # so that we don't kill everything with a bad command
    global heaters, lph
    # print('cmd', cmd)
    cmd = cmd.split()
    # print('cmd', cmd)
    if len(cmd)>1:
        params = cmd[1:]
    else:
        params = []
    cmd = cmd[0]
    if len(cmd):  # respond to command
        #Do we really want to have a quit command?
        #Will the microcontroller restart or does this just stop it?
        if (cmd=='Q'):
            writeUSB('Got Q')
            exit(0)
        # Does the board have the concept of knowing a serial number or anything?
        # It might be useful to have a command to get that
        elif (cmd=='*IDN?'):
            writeUSB('heater_control_board')
        elif (cmd=='PING'):SoftI2C(scl = Pin(sensors[name]['i2c port'][0]), sda = Pin(sensors[name]['i2c port'][1]))
            writeUSB('PONG')
            '''
        elif (cmd=="I?"):
            if len(params)>0:
                channel = int(params[0])
                # We should probably have a command that returns the number of heaters available
                if channel < len(heaters):
                    writeUSB(heaters[channel].dac)
                else:
                    writeUSB('bad command')
            else:
                writeUSB('bad command')
        elif (cmd=='MON?'):
            if len(params)>0:
                channel = int(params[0])
                if channel < len(heaters):
                    #I'm assuming that v is voltage and i is current?
                    writeUSB({heaters[channel].name: {'v': heaters[channel].v, 'i':heaters[channel].i}})
                else:
                    writeUSB('bad command')
            else:
                writeUSB('bad command')
                
        elif (cmd=="EN?"):
            if len(params)>0:
                channel = int(params[0])
                if channel < len(heaters):
                    if heaters[channel].enabled:
                        writeUSB(1)
                    else:
                        writeUSB(0)
                else:
                    writeUSB('bad command')
            else:
                writeUSB('bad command')
                
        # Should we be able to set 'v' too or just 'i'?
        elif (cmd=="I"):
            if len(params)>1:
                channel = int(params[0])
                dac_value = int(float(params[1]))
                heaters[channel].dac = dac_value
                #set(int(params[0]))
                #print(ujson.dumps('done'))
                writeUSB('done')
            else:
                writeUSB('bad command')
        elif (cmd=="EN"):
            if len(params)>1:
                channel = int(params[0])
                value = int(params[1])
                if value==0:
                    heaters[channel].disable()
                else:
                    heaters[channel].enable()
                writeUSB('done')
            else:
                writeUSB('bad command')
                '''
        #What does LPH mean?
        elif (cmd=="LPH?"):
            if len(params)>0:
                if int(params[0]) > 0:
                    channel = int(params[0])
                    #lph_list isn't defined so this will crash
                    writeUSB({lph_list[channel-1]: lph.get_channel(channel)})
                else:
                    writeUSB('bad command')
            else:
                writeUSB('bad command')
        elif (cmd=="LPH"):
            if len(params)>1:
                channel = int(params[0])
                if (channel>0) and (channel<5):
                    dac_value = int(params[1])
                    lph.set_channel(channel, dac_value)
                    writeUSB('done')
                else:
                    writeUSB('bad command')
            else:
                writeUSB('bad command')
        elif (cmd=='NAME?'): #For lph: NAME? lph 0 = cmd params[0].upper() int(params[1])
            if len(params)>0:
                if params[0].upper() == 'LPH':
                    channel = int(params[1])
                    #lph_list isn't defined so this will crash
                    if channel < len(lph_list):
                        writeUSB(lph_list[channel])
                    else:
                        writeUSB('bad command')
                else:
                    channel = int(params[0])
                    if channel < len(heaters):
                        writeUSB(heaters[channel].name)
                    else:
                        writeUSB('bad command')
            else:
                writeUSB('bad command')
        elif (cmd=="NAME"):
            if len(params)>1:
                channel = int(params[0])
                heaters[channel].name = params[1]
                #set(int(params[0]))
                print(ujson.dumps('done'))
                #We should have a: writeUSB("done")
            else:
                writeUSB('bad command')
        elif (cmd=='HPH_I_LIMIT?'):
            writeUSB(hph_i_limit)
        elif (cmd=='HPH_I_LIMIT'):
            if len(params)>0:
                hph_i_limit = int(params[0])
                print(ujson.dumps('done'))
                #We should have a: writeUSB("done")
            else:
                writeUSB('bad command')
        elif (cmd=='RESET'):
            if len(params)>0:
                channel = int(params[0])
                heaters[channel].reset()
                print(ujson.dumps('done'))
                #We should have a: writeUSB("done")
            else:
                writeUSB('bad command')
        else:
            writeUSB('not understood')

while True:
    #heater_state_check()
    readUSB()