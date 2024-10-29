from machine import Pin, I2C, ADC, PWM
class lt8386:
    def __init__(self, ctrl_pin = None, pwm_pin = None, en_pin = None, ismon_pin = None):
        
        if (ctrl_pin == None) and (pwm_pin == None) and (en_pin == None) and (ismon_pin == None):
            self.ctrl_pin = PWM(Pin(28, Pin.OUT), freq=20000, duty_u16=0)   
            self.pwm_pin = PWM(Pin(27, Pin.OUT), freq=20000, duty_u16=0) 
            self.en_pin = Pin(24, Pin.OUT)
            self.ismon_pin = ADC(Pin(29))
        else:
            self.ctrl_pin = PWM(Pin(ctrl_pin, Pin.OUT), freq=20000, duty_u16=0)  
            self.pwm_pin = PWM(Pin(pwm_pin, Pin.OUT), freq=20000, duty_u16=0)  
            self.en_pin = Pin(en_pin, Pin.OUT)
            self.ismon_pin = ADC(Pin(ismon_pin))
        self.set_current(0)
        self.set_pwm(0)
        self.disable()
    def set_current(self, duty_percent):
        #expects an input of % of 1A. so 50% of 1A would be 500mA
        if (duty_percent <= 1) and (duty_percent >= 0):
            #CTRL pin range is 12.5mV - 1.5V and should be same up to 2V
            #50% mark on current is 0.75V which is half of 1.5V which is 100% current
            #Minium is 16.6% which will be 0.25V which is at the lower range of 0 current
            v_equv = duty_percent*2
            pwm_equiv_duty = v_equv / 3.3 #pwm max is 3.2 V when 65535
            duty = pwm_equiv_duty *  (65535-1) #8191.875 from 12.5% offset and maxes LED current 10 62.5%
            self.ctrl_pin.duty_u16(int(duty))
            return {'done'}
        else:
            return {'error': 'Duty cycle percent must be 0<= i <= 1'}
    def set_pwm(self, duty_percent):
        #expects an input of % of 1A. so 50% of 1A would be 500mA
        if (duty_percent <= 1) and (duty_percent >= 0):
            duty = duty_percent *  (65535-1) #8191.875 from 12.5% offset and maxes LED current 10 62.5%
            self.pwm_pin.duty_u16(int(duty))
            return {'done'}
        else:
            return {'error': 'Duty cycle percent must be 0<= i <= 1'}
    
    def enable(self):
        self.en_pin.value(1)
        return "done"
    
    def disable(self):
        self.en_pin.value(0)
        return "done"

    def get_enable(self):
        return self.en_pin.value()
    def get_current(self):
        #Measures ismon pin which measures the voltage across the 100mOhm sense resistor. This voltage has a gain of 10.
        value = self.ismon_pin.read_u16()
        #convert to voltage
        voltage = (value/2**16) * 3.3
        #Has gain of 10
        voltage = voltage/10
        #Gives current back in mA
        current = voltage / 100e-3 * 1e3
        return current
    def get_pwm_current_value(self):
        return self.ctrl_pin.duty_u16()
    def get_pwm_value(self):
        return self.pwm_pin.duty_u16()

import time

#x = lt8386(ctrl_pin = PWM(Pin(27, Pin.OUT), freq=20000, duty_u16=0), pwm_pin = PWM(Pin(28, Pin.OUT), freq=20000, duty_u16=0), en_pin = Pin(26, Pin.OUT), ismon_pin = ADC(Pin(29)))
x  = lt8386()
'''
i_list = [0.        , 0.02040816, 0.04081633, 0.06122449, 0.08163265,
       0.10204082, 0.12244898, 0.14285714, 0.16326531, 0.18367347,
       0.20408163, 0.2244898 , 0.24489796, 0.26530612, 0.28571429,
       0.30612245, 0.32653061, 0.34693878, 0.36734694, 0.3877551 ,
       0.40816327, 0.42857143, 0.44897959, 0.46938776, 0.48979592,
       0.51020408, 0.53061224, 0.55102041, 0.57142857, 0.59183673,
       0.6122449 , 0.63265306, 0.65306122, 0.67346939, 0.69387755,
       0.71428571, 0.73469388, 0.75510204, 0.7755102 , 0.79591837,
       0.81632653, 0.83673469, 0.85714286, 0.87755102, 0.89795918,
       0.91836735, 0.93877551, 0.95918367, 0.97959184, 1.        ]
i_list = [1.        , 0.97959184, 0.95918367, 0.93877551, 0.91836735,
       0.89795918, 0.87755102, 0.85714286, 0.83673469, 0.81632653,
       0.79591837, 0.7755102 , 0.75510204, 0.73469388, 0.71428571,
       0.69387755, 0.67346939, 0.65306122, 0.63265306, 0.6122449 ,
       0.59183673, 0.57142857, 0.55102041, 0.53061224, 0.51020408,
       0.48979592, 0.46938776, 0.44897959, 0.42857143, 0.40816327,
       0.3877551 , 0.36734694, 0.34693878, 0.32653061, 0.30612245,
       0.28571429, 0.26530612, 0.24489796, 0.2244898 , 0.20408163,
       0.18367347, 0.16326531, 0.14285714, 0.12244898, 0.10204082,
       0.08163265, 0.06122449, 0.04081633, 0.02040816, 0.        ]
current_list = []
x.enable()
x.set_pwm(0.25)
data = 0
for i in i_list:
    x.set_current(i)
    time.sleep(1)
    for l in range(3):
        time.sleep(0.1)
        data += x.get_current()
        time.sleep(0.1)
    data = data/3
    print(i, data)
    current_list.append(data/3)
    data = 0
x.set_current(0)
'''