#Code Designed for UART Mux V3
import supervisor
import microcontroller
import busio
import board
from digitalio import DigitalInOut, Direction, Pull
import json
import sn74
import PCA8550 as pca

uart = busio.UART(board.TX, board.RX, baudrate=9600)
pinA0 = DigitalInOut(board.D8)
pinB0 = DigitalInOut(board.D10)
pinA0.direction = Direction.OUTPUT
pinB0.direction = Direction.OUTPUT

pinA0.value = False
pinB0.value = False


mux = sn74.SN74LV4052A(pinA0, pinB0)
pca = pca.PCA8550()


unique_id = microcontroller.cpu.uid
name = 'lockin_mux'

def writeUSB(item):
    print(json.dumps(item))

def main():

    while True:
        if supervisor.runtime.serial_bytes_available:
            value = input().strip()
            params = value.split()
            if len(params):
                value = params[0].upper();
            if len(params)==1:
                params = []
            elif len(params)>1:
                params = params[1:];
                #print('params', params)
            #print(f"Received: {value.split()}\r")
            if value.upper()=='*IDN?':
                writeUSB(unique_id)
            elif value.upper()=='*NAME?':
                writeUSB(name)
            elif value.upper() == 'Q':
                break;
            elif value.upper()=='DISABLE':
                if (len(params)>0):
                    channel = int(params[0])
                    pca.disable_output(channel)
                else:
                        writeUSB('bad command')
            elif value.upper()=='ENABLE':
                if (len(params)>0):
                    channel = int(params[0])
                    pca.enable_output(channel)
                else:
                        writeUSB('bad command')
            elif value.upper()=='RESET':
                if (len(params)>0):
                    channel = int(params[0])
                    pca.disable_output(channel)
                    pca.enable_output(channel)
                else:
                        writeUSB('bad command')
            elif value.upper()=='RESETALL':
                    pca.disable_all()
                    pca.enable_all()

            #elif value.upper()=='R?' or value.upper()=='RA?' or value.upper()=='LAST?' or value.upper()=='BIAS?' or :
            elif value.upper() in ['R?', 'RA?', 'LAST?', 'BIAS?', 'BIAS']:
                if (len(params)>0):
                    #print(params);
                    channel = int(params[0])
                    if value.upper()=='BIAS':
                        cmd = 'BIAS '+params[1]
                    else:
                        cmd = value.upper();
                    if (channel>=1) and (channel<5):
                        #print("got R, channel:", channel)
                        mux.choose_output(channel);  # Use lowest two bits
                        cmd = cmd + '\n'
                        cmd = cmd.encode()
                        uart.write(cmd)
                        failed_counter = 0
                        while True:
                            response = uart.readline()
                            if response is None:  # sometimes the request to readline happens to fast... try again
                                if failed_counter == 5:
                                    response = 'failed to read'
                                    break;
                                failed_counter += 1
                            else:
                                break
                        writeUSB(response);
                    else:
                        writeUSB('bad command')
                else:
                    writeUSB('bad command')
            else:
                writeUSB('bad command')

main()
