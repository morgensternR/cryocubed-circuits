from sys import stdin, stdout, exit
import time
import select
import gc
import ujson
import machine
from high_power_heater_v2 import High_power_heater_board
#from bh2221 import BH2221

'''
#Import Json file
config = ujson.load(open('heater_config.json', 'r'))
#Funciton Builds heater dict
def build_heaters(config):
    heater_dict = {}
    hp_heater_list = []
    lph_list = []
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
            lph_list.append(name)
        
        
    return heater_dict, hp_heater_list, lph_list

heater_dict, heaters, lph_list = build_heaters(config)

'''

heaters = [
    High_power_heater_board(29, 28, machine_number=0, addr=0x40, name = '4PUMPA' ),#4pumpA
    High_power_heater_board(27, 26, machine_number=1, addr=0x45, name = '3PUMPA'), #3PumpA
    High_power_heater_board(24, 25, machine_number=2, addr=0x44, name = '4PUMPB'), #4PumpB
    High_power_heater_board(3, 4, machine_number=3, addr=0x41, name = '3PUMPB'),   #3PumpB

    ]
'''
    High_power_heater_board(27, 26, machine_number=1, addr=0x45, name = '3PUMPA'), #3PumpA
    
    High_power_heater_board(3, 4, machine_number=3, addr=0x41, name = '3PUMPB'),   #3PumpB
    '''
hph_i_limit =50
def heater_state_check():
    global hph_i_limit
    for heater in heaters:
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
    while stdin in select.select([stdin], [], [], 0)[0]:
        #print('Got USB serial message')
        gc.collect()
        cmd = stdin.readline()
        #print(type(cmd), repr(cmd))
        cmd = cmd.strip().upper()
        if len(cmd)>0:
            do_command(cmd)

def writeUSB(msg):
    print(ujson.dumps(msg))
    
def do_command(cmd):
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
        if (cmd=='Q'):
            writeUSB('Got Q')
            exit(0)
        elif (cmd=='*IDN?'):
            writeUSB('heater_control_board')
        elif (cmd=='PING'):
            writeUSB('PONG')
        elif (cmd=="I?"):
            if len(params)>0:
                channel = int(params[0])
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
        elif (cmd=="LPH?"):
            if len(params)>0:
                if int(params[0]) > 0:
                    channel = int(params[0])
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
            else:
                writeUSB('bad command')
        elif (cmd=='HPH_I_LIMIT?'):
            writeUSB(hph_i_limit)
        elif (cmd=='HPH_I_LIMIT'):
            if len(params)>0:
                hph_i_limit = int(params[0])
                print(ujson.dumps('done'))
            else:
                writeUSB('bad command')
        elif (cmd=='RESET'):
            if len(params)>0:
                channel = int(params[0])
                heaters[channel].reset()
                print(ujson.dumps('done'))
            else:
                writeUSB('bad command')
        else:
            writeUSB('not understood')

while True:
    #heater_state_check()
    readUSB()