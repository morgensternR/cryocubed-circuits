from machine import I2C, Pin, SoftI2C
import time
class PCA8550:
        def __init__(self, i2c_device=None, addr=0x4e):
            self.addr = addr
            if i2c_device == None:
                #self.i2c = SoftI2C(scl=machine.Pin(23), sda=machine.Pin(22))
                self.i2c = I2C(1, scl=Pin(23), sda=machine.Pin(22), freq = 10000)
            else:
                self.i2c = i2c_device
            self.present_register = bytearray(2)
            self.state = bytearray([self.present_register[0]+self.present_register[1]])
            
        def disable_output(self, pin):
            #check if pin is [1,2,3,4]
            if isinstance(pin,int):
                if pin in [1,2,3,4]:
                    self._read_data
                    data = bytearray(1)
                    data[0] = self.present_register[0] & ~(1<<(pin-1))
                    self._send_data(data)
                else:
                    print('incorrect Pin or chose Pin 0, its 1,2,3,4')
            else:
                print('Error, not a an int')
                
        def enable_output(self, pin):
            if pin in [1,2,3,4]:
                data = bytearray(1)
                data[0] = self.present_register[0] | (1<<(pin-1))
                #print(data, bin(data[0]))
                self._send_data(data)
            else:
                print('Pin does not exist')
        def disable_all(self):
            data = bytearray(1)
            data[0] = self.present_register[0] & 0
            self._send_data(data)

            
        def enable_all(self):
            data = bytearray(1)
            data[0] = self.present_register[0] | 0b00001111
            self._send_data(data)

        
        def _write_data(self,data):
            self.i2c.writeto(self.addr, bytes(data))
        def _read_data(self,data):
            self.i2c.readfrom_into(self.addr, self.present_register)
                        
        def _send_data(self,data):
            self._write_data(data)
            time.sleep(1)
            self._read_data(data)
            self.state = bytearray([self.present_register[0]+self.present_register[1]])

#Testing            
#i2c = I2C(1, scl=Pin(7), sda=Pin(6),  freq = 100000)
#i2c = SoftI2C(scl=machine.Pin(23), sda=machine.Pin(22))
#x = PCA8550(i2c_device = i2c)


