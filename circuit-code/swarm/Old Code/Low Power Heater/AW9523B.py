from machine import I2C

class AW9523B:
    def __init__(self, I2C_address, i2c = None):

        if i2c == None:
            i2c = busio.I2C(board.SCL1, board.SDA1)
        self.i2c = i2c

        self.addr = I2C_address
        self.temp = False

    def reset(self):
        self.i2c.writeto(self.addr, bytes([0x7F, 0x00]))

    def powerdown(self):
        self.i2c.writeto(self.addr, bytes([0x02]))

    def config_port(self, port, state): #inpout/output mode. Seperate from LED mode...
        if port == 0:
            address = 0x04
        elif port == 1:
            address = 0x05
        if (port != 0) and (port != 1):
            print("error choose port 0 or 1")
        self.i2c.writeto(self.addr, bytes([address,state]))
        
    def led_mode(self, on = False):
        if on == True:
            self.i2c.writeto(self.addr, bytes([0x12, 0x00]))
            self.i2c.writeto(self.addr, bytes([0x13, 0x00]))
        else:
            self.i2c.writeto(self.addr, bytes([0x12, 0xff]))
            self.i2c.writeto(self.addr, bytes([0x13, 0xff]))

    def port_mode_group(self, port, mode):
        port_address = 0x12 + 0x01*port
        self.i2c.writeto(self.addr, bytes([port_address, mode]))

    def current_dim(self, port, value):
        if isinstance(port, str) == False:
            print("Port format is 'P#_#', Check datasheet for step dimming control")
        if isinstance(value, int) == False:
            print("Select an int from 0-255")
        LED_port = self.step_reg[port]
        #print(LED_port)
        self.i2c.writeto(self.addr, bytes([LED_port, int(value)]))
    
    step_reg = {
    'P1_0':(0x20),
    'P1_1':(0x21),
    'P1_2':(0x22),
    'P1_3':(0x23),
    'P0_0':(0x24),
    'P0_1':(0x25),
    'P0_2':(0x26),
    'P0_3':(0x27),
    'P0_4':(0x28),
    'P0_5':(0x29),
    'P0_6':(0x2A),
    'P0_7':(0x2B),
    'P1_4':(0x2C),
    'P1_5':(0x2D),
    'P1_6':(0x2E),
    'P1_7':(0x2F)}
