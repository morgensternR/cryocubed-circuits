from machine import Pin, idle, UART, RTC, PWM, ADC
import time
import rp2
import gc
from sys import stdin, stdout, exit


def readUSBSerial():
    global ONCE, DEBUG, last
    gc.collect()
    while stdin in select.select([stdin], [], [], 0)[0]:
        #print('Got USB serial message')
        gc.collect()
        #print('in select')
        cmd = stdin.readline()
        #print(type(cmd), repr(cmd))
        cmd = cmd.strip().upper()
        doCommand(cmd)


def doCommand(cmd, responder=print):
    global ONCE, DEBUG, last, p9, counter
    #print('do Command', cmd)
    if len(cmd):  # respond to command
        args = cmd.split();
        cmd = args[0]
        if (cmd[0]=='Q'):
            responder('Got Q')
            exit(0)
        elif (cmd=='PING'):
            responder('PONG')
        elif (cmd=="R?"):
            resp = adc.read_u16()/1e6 #uV to V
            responder(f'{resp}')
        elif (cmd=="PWM?"):
            resp = pwm0.duty_u16()
            responder(f'{resp}')
        elif (cmd=="PWM"):
            responder(f'{last}')
            if len(args)>1:
                pwm0.duty_u16(args[1])      # set the duty cycle of channel A, range 0-65535
        elif (cmd=="BIAS?"):
            response = p9.value()
            responder(f'{response}')
        elif (cmd=="BIAS"):
            if len(args)>1:
                print('args', args);
                channel = int(args[1])
                if channel:
                    p9.on()
                else:
                    p9.off()
                counter = 0
                responder("done")
            else:
                responder("bad channel for bias");
        elif (cmd=="DEBUG"):
            DEBUG = not DEBUG
            responder(f"DEBUG: {DEBUG}")
        elif (cmd=="DEBUG?"):
            responder(f'{DEBUG}')
        else:
            responder('bad command');
# create PWM object from a pin and set the frequency of slice 0
# and duty cycle for channel A
adc = ADC(Pin(29))
pwm_ctrl = PWM(Pin(28, Pin.OUT))
pwm_pwr = PWM(Pin(27, Pin.OUT))
pwm_list= [pwm_ctrl, pwm_pwr]
en_switch = Pin(24, Pin.OUT)
for i in pwm_list:
    i.freq(40000)
    i.duty_u16(0)



def adc_read(adc, current = True):
    r = 100e-3
    adc_voltage = ((adc.read_u16()/65535)*3.3 )
    ismon_v = adc_voltage /10
    if current:
        return ismon_v / r
    else:
        return adc_voltage, ismon_v 
def set_pwm(duty_percent, pwm_input, ctrl = True):
    if isinstance(pwm_input, PWM):
        if ctrl:
            if (duty_percent <= 1) and (duty_percent >= 0):
                v_equv = duty_percent*2 #CTRL pin range is 12.5mV - 2V
                pwm_equiv_duty = v_equv / 3.2 #pwm max is 3.2 V when 65535
                duty = pwm_equiv_duty *  (65535-1) #8191.875 from 12.5% offset and maxes LED current 10 62.5%
                pwm_input.duty_u16(int(duty))
            else:
                raise Exception('Duty cycle must be a number 0>=Duty>=1')
        else:
            if (duty_percent <= 1) and (duty_percent >= 0):
                v_equv = duty_percent*2 #CTRL pin range is 12.5mV - 2V
                pwm_equiv_duty = v_equv / 3.2 #pwm max is 3.2 V when 65535
                duty = pwm_equiv_duty *  (65535-1) #8191.875 from 12.5% offset and maxes LED current 10 62.5%
                pwm_input.duty_u16(int(duty))
            else:
                raise Exception('Duty cycle must be a number 0>=Duty>=1')
    else:
        raise Exception ('Input a pwm object')

pwm_pwr.duty_u16(int(65533))
pwm_ctrl.duty_u16(int(65533))


'''
for i in range(0, int(65534), 2048):
    pwm_ctrl.duty_u16(i)
    time.sleep(3)
    print('adc =' , adc_read(adc, current =1), 'PWM =' , i, 'CTRL Applied Voltage =', (i/65535)*3.2)
    
for i in pwm_list:
    i.duty_u16(0)
'''
