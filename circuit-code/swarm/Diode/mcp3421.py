from machine import Pin, I2C
import time
from math import ceil
from uctypes import BF_POS, BF_LEN, UINT32, BFUINT8, addressof, struct




class MCP3421:
    def __init__(self, i2c, sampling = 2, gain = 0, conversion = 1, slope = 16000, offset = 0,  addr=104):#out_port, A_port, B_port,
        self.i2c = i2c
        self.addr = addr
        
        bits_list = [12, 14, 16, 18]
        self.bits = bits_list[sampling]

        self.slope = slope
        if self.slope == 16000: #default is 16K, if bits are set other than 16, it adjusts, or make it calibrated slope
            self.slope = (2**(self.bits - 1))/2.048
        self.offset = offset
        

        self.data_size = ceil(self.bits/8)
        
        #conversion = 1 = Continous
        #conversion = 0 = one-shot
        #Sampling
        # 0  = 240 SPS 12 bits
        # 1  = 60 SPS 14 bits
        # 2  = 15 SPS 16 bits
        # 3  = 3.75 SPS 18 bits
        self.register_fields = {
                "dataready": 7<<BF_POS | 1 <<BF_LEN | BFUINT8,
                "unused"   : 5<<BF_POS | 2 <<BF_LEN | BFUINT8,
                "mode"     : 4<<BF_POS | 1 <<BF_LEN | BFUINT8,
                "sampling" : 2<<BF_POS | 2 <<BF_LEN | BFUINT8,
                "gain"     : 0<<BF_POS | 2 <<BF_LEN | BFUINT8,
            }

        self.register_buffer = bytearray(1)
        self.register = struct(addressof(self.register_buffer), self.register_fields)
        
        self.register.gain = gain
        self.register.mode = conversion
        self.register.sampling = sampling
        
        self.set_config()
        self.read_config()
        
    def set_config(self):
        #Constructs message by 'or'ing numbers together
        #register_value = (self.conversion << 4) | (self.bit_dict[self.bits] << 3) | (self.gain_dict[self.gain])
        self.i2c.writeto(self.addr, self.register_buffer)
        
    def read_config(self):
        #Adc attches config at end of data bits. Requires minumum bytes for bits + 1 for config byte
        data = bytearray(self.data_size + 1)
        
        self.i2c.readfrom_into(self.addr, data)
        self.register_buffer[0] = data[-1]
        #returns last byte in array which is config
        return self.register_buffer[0]
    
    def drdy(self):
        while (self.read_config() >> 7 ) == 1:
            pass
        
    def read_adc(self):
        data = bytearray(self.data_size)
        self.drdy() #Determines when to read depending on data Rdy Bit
        self.i2c.readfrom_into(self.addr, data)
        #Int from bytes can convert sign for multiples of bytes but not bits.Ex Can use Signed True on 8,16,24 bits (1,2,3 bytes)
        result = int.from_bytes(data[:self.data_size],'big')
        
        if result & ( 1 << ( self.bits-1 )):
            result = result - ( 1 << self.bits )
        
        return result
    
    def read_adc_v(self):
        adc_int = self.read_adc()
        result = (adc_int - self.offset)/(self.slope * (2**self.register.gain))
        return result
    
#Code below is for testing
'''

i2c = I2C(1, scl=Pin(23, Pin.PULL_UP), sda=Pin(22, Pin.PULL_UP))
dev = MCP3421(i2c, sampling = 2, conversion = 1, gain = 0)

while True:
    print(dev.read_adc_v())

'''

