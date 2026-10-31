#!/usr/bin/python
#
# Logic for manipulating I/O device connected to signals.
#
# In this case, we're manipulating a Model Railroad Control Systems
# IOX32 expander board, which uses two Microchip MCP23017 I2C I/O expander
# chips to control 32 inputs and outputs.

import sys
import time

# For LCD1602 16x2 character display:
# https://www.raspberrypi-spy.co.uk/2015/05/using-an-i2c-enabled-lcd-screen-with-the-raspberry-pi/
import rpi_lcd
import smbus

# Registers for GPIO Ports Bank=0
IODIRA = 0x00 # first line configuration register
IODIRB = 0x01 # second line configuration register.
IPOLA = 0x02  # first polarity inversion register.
IPOLB = 0x03  # second polarity inversion register.
GPINTENA = 0x04  #
GPINTENB = 0x05
GPPUA = 0x0c
GPPUB = 0x0d
# Register for reading input values.
GPIOA = 0x12 # register for inputs
GPIOB = 0x13
# Register for writing output values.
OLATA = 0x14 # register for outputs
OLATB = 0x15

class PortExpander(object):
    """Support for Model Railroad Control Systems 32 port I/O expander.

    Manipulates two MCP23017 chips on the same board via I2C.
    """
    def __init__(self, device):
        """Set up port expander.

        device: integer value that device responds to on I2C bus.

        """
        # Bus 1 on Raspberry Pis is for I2C.
        self.bus = smbus.SMBus(1)
        self.device = device
        # Current output lines set for device, as integer.
        self.now_value = 0

    def setup(self):
        # All output ports off.
        # All outputs.
        if self.device % 2 == 0:
            # All lines in bank A are inputs on even numbered devices.
            self.bus.write_byte_data(self.device, IODIRA, 0xff)
            time.sleep(0.02)
            self.bus.write_byte_data(self.device, GPPUA, 0xff)
            time.sleep(0.02)
        else:
            # All of lines in bank A are outputs on odd numbered devices.
            self.bus.write_byte_data(self.device, IODIRA, 0)
            time.sleep(0.02)

        # For all expanders, second set of lines are all outputs.
        self.bus.write_byte_data(self.device, IODIRB, 0x00)
        time.sleep(0.02)
        # Clear outputs.
        self.bus.write_byte_data(self.device, OLATA, 0)
        time.sleep(0.02)
        self.bus.write_byte_data(self.device, OLATB, 0)
        time.sleep(0.02)

    def get_input(self, index):
        e = None
        for i in range(0,3):
            try:
                # Return true, false.
                resp = self.bus.read_byte_data(self.device, GPIOA)
                # print(resp)
                value = bool(resp & (1 << index))
                # print('Request value from device %d input %d is %s' %(self.device,
                # index, value))
                return value
            except IOError as e:
                print('Error in get_input: %s' % e)
                # and repeat
        print("Multiple IOErrors when trying to read bus.  Failing.")
        throw(e)

    def get_output_value(self, index):
        if self.device % 2 == 0:
            index += 8
        value = self.now_value & (1 << index)
        return bool(value)

    def set_output(self, index, value):
        try:
            self.set_output_inner(index, value)
        except Exception as e:
            print('failure to write, trying again')
            self.set_output_inner(index, value)

    def set_output_inner(self, index, value):
        e = None
        for i in range(0, 3):
            try:
                if self.device % 2 == 0:
                    index += 8
                now_value = self.now_value

                if value:
                    now_value |= (1 << index)
                else:
                    now_value &= ~ (1 << index)
                #print('Now value is 0x%08x' % now_value)
                #print('Set device %s output %s to %s' % (self.device, index, value))

                self.bus.write_byte_data(self.device, OLATA, now_value & 0xff)
                time.sleep(0.02)
                self.bus.write_byte_data(self.device, OLATB, (now_value & 0xff00) >> 8)
                time.sleep(0.02)
                self.now_value = now_value
                return
            except IOError as e:
                print('Error in set_output_inner: %s' % e)
                # and try again.
        # Failed too many times?  Bail out.
        throw(e)


    def set_outputs(self, value):
        """Set all outputs at once.

        Value is 16 bits, one bit per output.
        """
        self.now_value = value
        self.bus.write_byte_data(self.device, OLATA, (value & 0xff))
        time.sleep(0.02)
        self.bus.write_byte_data(self.device, OLATB, (value & 0xff00) >> 8)
        time.sleep(0.02)


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

    expander = PortExpander(port_number)
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
