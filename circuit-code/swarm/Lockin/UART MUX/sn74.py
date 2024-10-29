from machine import Pin
class SN74LV4052A:
    def __init__(self, pin_a = None, pin_b = None):
        if isinstance(pin_a, int):
            self.pin_a = Pin(pin_a, Pin.OUT)
            self.pin_b = Pin(pin_b, Pin.OUT)
        else:
            self.pin_a = pin_a
            self.pin_b = pin_b
        self.logic_table = {
            0: {'A' : 0 , 'B': 0},
            1: {'A' : 1 , 'B': 0},
            2: {'A' : 0 , 'B': 1},
            3: {'A' : 1 , 'B': 1}
            }

    def choose_output(self, channel):
        if isinstance(channel, int):
            if channel not in [1,2,3,4]:
                print('incorrect channel or chose channel 0, its 1,2,3,4')
            else:
                #print('A = ', self.logic_table[channel-1]['A'], 'B =', self.logic_table[channel-1]['B'])
                #print(self.pin_a.value(), self.pin_b.value())
                self.pin_a.value(self.logic_table[channel-1]['A'])
                self.pin_b.value(self.logic_table[channel-1]['B'])
                #print(self.pin_a.value(), self.pin_b.value())

        else:
            print('Channel is not an int')

