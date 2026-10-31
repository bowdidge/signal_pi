#!/usr/bin/python
#
# Control signals with logic.

import sys
import time

# For LCD1602 16x2 character display:
# https://www.raspberrypi-spy.co.uk/2015/05/using-an-i2c-enabled-lcd-screen-with-the-raspberry-pi/
import rpi_lcd
import smbus

# Registers for GPIO Ports Bank=0
IODIRA = 0x00 # pin dir reg
IODIRB = 0x01
IPOLA = 0x02
IPOLB = 0x03
GPINTENA = 0x04
GPINTENB = 0x05
GPPUA = 0x0c
GPPUB = 0x0d
GPIOA = 0x12 # register for inputs
GPIOB = 0x13
OLATA = 0x14 # register for outputs
OLATB = 0x15

class PortExpander(object):
    """Support for Model Railroad Control Systems 32 port I/O expander.
    
    Uses blah blah card.
    """
    def __init__(self, device, display_device):
        """Set up port expander.

        device: integer value that device responds to on I2C bus.
        display_device: device to display significant status messages (on order
        of one every several seconds.)
        
        """
        # Bus 1 on Raspberry Pis is for I2C.
        self.bus = smbus.SMBus(1)
        self.device = device
        self.now_value = 0
        self.displayer = display_device
        if self.displayer:
            self.displayer.display('Set up device %02x' % self.device, '')

    def setup(self):
        # All output ports off.
        # All outputs.
        if self.device % 2 == 0:
            self.bus.write_byte_data(self.device, IODIRA, 0xff)
            self.bus.write_byte_data(self.device, GPPUA, 0xff)
        else:
            self.bus.write_byte_data(self.device, IODIRA, 0)
            
        self.bus.write_byte_data(self.device, IODIRB, 0x00)
        # Clear outputs.
        self.bus.write_byte_data(self.device, OLATA, 0)
        self.bus.write_byte_data(self.device, OLATB, 0)

    def get_input(self, index):
        # Return true, false.
        resp = self.bus.read_byte_data(self.device, GPIOA)
        # print(resp)
        value = bool(resp & (1 << index))
        # print('Request value from device %d input %d is %s' %(self.device,
        # index, value))
        return value

    def get_output_value(self, index):
        if self.device % 2 == 0:
            index += 8
        value = self.now_value & (1 << index)
        return bool(value)
    
    def set_output(self, index, value):
        if self.device % 2 == 0:
            index += 8
        now_value = self.now_value

        if value:
            now_value |= (1 << index)
        else:
            now_value &= ~ (1 << index)
        print('Now value is 0x%08x' % now_value)
        print('Set device %s output %s to %s' % (self.device, index, value))

        self.bus.write_byte_data(self.device, OLATA, now_value & 0xff)
        self.bus.write_byte_data(self.device, OLATB, (now_value & 0xff00) >> 8)
        self.now_value = now_value

    def set_outputs(self, value):
        self.now_value = value
        self.bus.write_byte_data(self.device, OLATA, (value & 0xff))
        self.bus.write_byte_data(self.device, OLATB, (value & 0xff00) >> 8)
        
    def flash(self):
        print('baz')
        for data in range(0,8):
             self.bus.write_byte_data(self.device, OLATA, data)
             self.bus.write_byte_data(self.device, OLATB, data)
             time.sleep(1)

        # Turn off outputs.
        self.bus.write_byte_data(self.device, OLATA, 0)
        self.bus.write_byte_data(self.device, OLATB, 0)

def main():
    """Test inputs and outputs."""
    # Port 20 and 22 are the two expanders.
    # Expander cards actually have two chips, one responding to 20
    # and the other to 21.
    if len(sys.argv) != 2:
        print('Usage: port_expander.py port')
        sys.exit(1)

    port = sys.argv[1]
    port_number = int(port, 16)

    expander = PortExpander(port_number, None)
    expander.setup()
    
    print('Flipping outputs')
    for i in range(0, 100):
        expander.set_outputs(0x5500)
        expander.set_outputs(0x5555)
        time.sleep(0.25)

        expander.set_outputs(0xaa00)
        expander.set_outputs(0xaaaa)
        time.sleep(0.25)

        if expander.device % 2 == 0:
            for i in range(0, 8):
                print('Input %d: %d' % (i, expander.get_input(i)))
                
        for i in range(0, 24):
            expander.set_output(i, 1)
            time.sleep(0.1)
    
if __name__ == '__main__':
    main()
