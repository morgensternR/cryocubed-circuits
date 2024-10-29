# -*- coding: utf-8 -*
import machine
import utime
import ustruct
import sys

'''
# Select DAC output voltage of 0-5V
OUTPUT_RANGE_5V = 0
# Select DAC output voltage of 0-10V
OUTPUT_RANGE_10V = 17
# Select to output from channel 0
CHANNEL0 = 1
# Select to output from channel 1
CHANNEL1 = 2
# Select to output from all the channels
CHANNELALL = 3
'''

class GP8403():
    # Configure current sensor register
    GP8403_CONFIG_CURRENT_REG = 0x02
    # Store function timing start head
    GP8302_STORE_TIMING_HEAD = 0x02
    # The first address for entering store timing
    GP8302_STORE_TIMING_ADDR = 0x10
    # The command 1 to enter store timing
    GP8302_STORE_TIMING_CMD1 = 0x03
    # The command 2 to enter store timing
    GP8302_STORE_TIMING_CMD2 = 0x00
    # Total I2C communication cycle 5us
    I2C_CYCLE_TOTAL = 5
    # The first half cycle of the total I2C communication cycle 2us
    I2C_CYCLE_BEFORE = 2
    # The second half cycle of the total I2C communication cycle 3us
    I2C_CYCLE_AFTER = 3
    # Store procedure interval delay time: 10ms (1000us) 
    # (should be more than 7ms according to spec)
    GP8302_STORE_TIMING_DELAY = 1000


    def __init__(self, addr, i2c = None, sclpin = None, sdapin = None, i2cfreq = None, hard = False):
        """
        Initilize the I2C bus.
        On Pico, Software I2C (using bit-banging) works on all output-capable pins
        :param addr: I2C address
        :param sclpin: SCL pin
        :param sdapin: SDA pin
        :param i2cfreq: I2C frequency
        :param hard: I2C or SoftI2C
        """
        self._addr = addr
        self.outPutSetRange = 0x01
        self.voltage = 10000
        self.dataTransmission = 0
        self._hard = hard
        self.voltage_ch1 = 0
        self.voltage_ch2 = 0
        self.en_ch1 = False
        self.en_ch2 = False

        # Need it because "store" bit bangs and uninitialize the I2C bus
        if i2c == None:
            self._sclpin = sclpin
            self._sdapin = sdapin
            self._scl = machine.Pin(sclpin)
            self._sda = machine.Pin(sdapin)
            self._i2cfreq = i2cfreq
            self._initializeI2C()
        else:
            self.i2c = i2c

    def _initializeI2C(self):
        if self._hard:
            self.i2c = machine.I2C(0,
                                   scl=self._scl,
                                   sda=self._sda,
                                   freq=self._i2cfreq)
        else:
            # Pylance is not happy with this because stubs are wrong.
            # see: https://github.com/paulober/Pico-W-Go/issues/55
            self.i2c = machine.SoftI2C(scl=self._scl,
                                sda=self._sda,
                                freq=self._i2cfreq)
            

    def begin(self):
        # List devices
        print("Found i2c addresses: ", self.i2c.scan())
        
        # Initialize the sensor
        try:
            if self.i2c.readfrom(self._addr, 1) != 0:
                return 0
            return 1            
        except OSError as e:
            print("Error: {0} on address {1}".format(e, hex(self._addr)))
            return 1
        except Exception as e: # exception if read_byte fails
            print("Error unk: {0} on address {1}".format(e, hex(self._addr)))
            return 1
    

    def set_dac_out_range(self, mode):
        """
        Set DAC output range
        :param mode: 5V or 10V OUTPUT_RANGE mode
        """       
        if mode == OUTPUT_RANGE_5V:
            self.voltage = 5000
        elif mode == OUTPUT_RANGE_10V:
            self.voltage = 10000
        
        b = bytearray(1)
        b[0] = mode
        self.i2c.writeto_mem(self._addr, self.outPutSetRange, b, addrsize=8)
        
    def get_dac_out_range(self):
        return self.voltage
    def get_dac_out_voltage(self, channel):
        if channel == 0:
            return self.voltage_ch1 
        elif channel == 1:
            return self.voltage_ch2
    def get_dac_ch_en(self, channel):
        if channel == 0:
            return self.en_ch1
        elif channel == 1:
            return self.en_ch2
        elif channel == 2:
            return self.en_ch1, self.en_ch2
    def set_dac_out_voltage(self, data, channel):
        """
        Select DAC output channel & range
        :param data: Set voltage in mV between 0-5000 or 0-10000 depending on range
        :param channel: Set output channel
        """
        try:
            if self.votage >= data >= 0: 
                self.dataTransmission = int((float(data) / self.voltage) * 4095)
                self.dataTransmission = int(self.dataTransmission) << 4
                self._send_data(self.dataTransmission, channel)
                if channel == 0:
                    self.voltage_ch1 = data
                elif channel == 1:
                    self.voltage_ch2 = data
                elif channel == 2:
                    self.voltage_ch1 = data
                    self.voltage_ch2 = data
            else:
                return {'error':f'input voltage not in range of 0 - {self.voltage}'}
        except:
            return {'error':'invalid data input'}


    def _send_data(self, data, channel):
        if channel == 0 or channel == 3:
            b = bytearray(3)
            b[0] = self.GP8403_CONFIG_CURRENT_REG
            b[1] = data & 0xFF
            b[2] = (data >> 8) & 0xFF
            self.i2c.writeto(self._addr, b)

        if channel == 1 or channel == 3:
            b = bytearray(3)
            b[0] = self.GP8403_CONFIG_CURRENT_REG << 1
            b[1] = data & 0xFF
            b[2] = (data >> 8) & 0xFF
            self.i2c.writeto(self._addr, b)


    def store(self):
        """
        Save the present current config, after the config is saved successfully,
        it will be enabled when the module is powered down and restarts
        
        This is done with bit-banging because the chip does custom I2C with less than 1 Byte data.
        """       
        # Re-initialise Pin because it was initialized 
        # with SoftI2C and we need to use it as GPIO
        _scl = machine.Pin(self._sclpin, machine.Pin.OUT)
        _sda = machine.Pin(self._sdapin, machine.Pin.OUT)

        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_HEAD, 0, 3, False)
        self._stop_signal()
        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_ADDR)
        self._send_byte(self.GP8302_STORE_TIMING_CMD1)
        self._stop_signal()

        self._start_signal()
        self._send_byte(self._addr<<1, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2, 1)
        self._stop_signal()

        utime.sleep_us(self.GP8302_STORE_TIMING_DELAY)

        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_HEAD, 0, 3, False)
        self._stop_signal()
        self._start_signal()
        self._send_byte(self.GP8302_STORE_TIMING_ADDR)
        self._send_byte(self.GP8302_STORE_TIMING_CMD2)
        self._stop_signal()

        # re-initialize I2C
        self._initializeI2C()


    def _start_signal(self):
        self._scl.high()
        self._sda.high()
        utime.sleep_us(self.I2C_CYCLE_BEFORE)
        self._sda.low()
        utime.sleep_us(self.I2C_CYCLE_AFTER)
        self._scl.low()
        utime.sleep_us(self.I2C_CYCLE_TOTAL)
  
    def _stop_signal(self):
        self._sda.low()
        utime.sleep_us(self.I2C_CYCLE_BEFORE)
        self._scl.high()
        utime.sleep_us(self.I2C_CYCLE_TOTAL)
        self._sda.high()
        utime.sleep_us(self.I2C_CYCLE_TOTAL)

    def _recv_ack(self, ack = 0):
        ack_ = 0
        error_time = 0
        self._sda = machine.Pin(self._sdapin, machine.Pin.IN)

        utime.sleep_us(self.I2C_CYCLE_BEFORE)
        self._scl.high()
        utime.sleep_us(self.I2C_CYCLE_AFTER)
        while self._sda.value() != ack:
            utime.sleep_us(1)
            error_time += 1
            if error_time > 250:
                break
        ack_ = self._sda.value() # suspicious to read the value here, should save it before the while loop?
        utime.sleep_us(self.I2C_CYCLE_BEFORE)
        self._scl.low()
        utime.sleep_us(self.I2C_CYCLE_AFTER)
        self._sda = machine.Pin(self._sdapin, machine.Pin.OUT)
        return ack_

    def _send_byte(self, data, ack = 0, bits = 8, flag = True):
        i = bits
        # Ensure 8 bits only
        data = data & 0xFF
        while i > 0:
            i -= 1
            if data & (1 << i):
                self._sda.high()
            else:
                self._sda.low()
            utime.sleep_us(self.I2C_CYCLE_BEFORE)
            self._scl.high()
            utime.sleep_us(self.I2C_CYCLE_TOTAL)
            self._scl.low()
            utime.sleep_us(self.I2C_CYCLE_AFTER)
        if flag:
            return self._recv_ack(ack)
        else:
            self._sda.low()
            self._scl.high()
        return ack
#import machine
#GP8403(addr = 88, sclpin = 23, sdapin = 22, i2cfreq = 40000, hard = 1)

