class TCA9548A:
    def __init__(self, i2c, addr=112):
        self.i2c = i2c
        self.addr = addr

    def read_reg(self):
        data = bytearray(1)
        self.i2c.readfrom_into(self.addr, data)
        return data
    
    def write_reg(self, adc_int, enable = True):
        #Assume to reset to default disable state before reading. Dont require more than 1 to be enabled
        self.i2c.writeto(self.addr, bytes([0x00]))
        
        data = (2**adc_int)*int(enable) #0 to disbale, 1 to enable
        self.i2c.writeto(self.addr, bytes([data]))
