import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice
import time
class PCA8550:
        def __init__(self, i2c_device=None, addr=0b1001110):
            self.addr = addr
            if i2c_device == None:
                self.i2c = I2CDevice(busio.I2C(board.SCL, board.SDA), self.addr)
            else:
                self.i2c = i2c_device
            with self.i2c:
                self.present_register = bytearray(1)
                self.i2c.readinto(self.present_register)
            
        def disable_output(self, pin):
            #check if pin is [1,2,3,4]
            if isinstance(pin,int):
                if pin in [1,2,3,4]:
                    data = bytearray(1)
                    data[0] = self.present_register[0] & ~(1<<(pin-1))
                    self._send_data(data)
                    #self.i2c.write(self.addr, data)
                    #self.present_register = data[0]
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
                #self.i2c.write(self.addr, data)
                #self.present_register = data[0]
            else:
                print('Pin does not exist')
        def disable_all(self):
            data = bytearray(1)
            data[0] = self.present_register[0] & 0
            print(data)
            self._send_data(data)
            #self.i2c.write(self.addr, data)
            #self.present_register = data[0]
            
        def enable_all(self):
            data = bytearray(1)
            data[0] = self.present_register[0] | 0b00001111
            self._send_data(data)
            #self.i2c.write(self.addr, data)
            #self.present_register = data[0]
        def _send_data(self,data):
            with self.i2c:
                self.i2c.write(data)
                
                #self.i2c.write_then_readinto(data, self.present_register)
                time.sleep(1)
                self.i2c.readinto(self.present_register)

x = PCA8550()