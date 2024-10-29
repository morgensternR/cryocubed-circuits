import AW9523B as aw
import gp8403 as gp
from machine import Pin, I2C
import time



i2c = I2C(1, scl=machine.Pin(23), sda=machine.Pin(22), freq=40000)

switch = aw.AW9523B(I2C_address = 91, i2c = i2c)
switch.reset()
switch.led_mode(True)

dac1 = gp.GP8403(addr = 94, i2c = i2c)
dac2 = gp.GP8403(addr = 92, i2c = i2c)
dac3 = gp.GP8403(addr = 88, i2c = i2c)
dac4 = gp.GP8403(addr = 93, i2c = i2c)
dac5 = gp.GP8403(addr = 95, i2c = i2c)
dac_list = [dac1,dac2,dac3,dac4,dac5]

for dac in dac_list:
    dac.begin()
    dac.set_dac_out_range(mode = 'OUTPUT_RANGE_10V')
    dac.set_dac_out_voltage(10000, 0)
    dac.set_dac_out_voltage(10000, 1)
    #time.sleep(1)

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
        2:'P0_3'
        },
    5:{
        1: 'P0_0',
        2:'P0_1'
        }
    }