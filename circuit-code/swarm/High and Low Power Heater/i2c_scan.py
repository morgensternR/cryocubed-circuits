import machine
from machine import Pin
#i2c = machine.I2C(1, scl=machine.Pin(23), sda=machine.Pin(22))
i2c = machine.I2C(1, scl=Pin(7), sda=Pin(6), freq = 10000)
print('Scan i2c bus...')
devices = i2c.scan()

if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))

  for device in devices:  
    print("Decimal address: ",device," | Hexa address: ",hex(device))