#!/usr/bin/env python

#
# Control LED panel.

import time

# For LCD1602 16x2 character display:
# https://www.raspberrypi-spy.co.uk/2015/05/using-an-i2c-enabled-lcd-screen-with-the-raspberry-pi/
#
# Problems?  i2cdetect -y 1 should show something on I2C bus address 0x27.
# Make sure i2c-1 device exists in /dev.

import rpi_lcd

class LCDDisplayer(object):
    """Display debugging or status messages on LCD panel."""
    def __init__(self):
        self.lcd = rpi_lcd.LCD(address=0x27, width=16, rows=2)

    def display(self, msg1, msg2):
        self.lcd.text(msg1, 1)
        self.lcd.text(msg2, 2)

def main():
    displayer = MessageDisplayer()
    displayer.display('hello', 'world')
    time.sleep(2)

    displayer.display('1234567890123456',
                      '1234567890123456')
    time.sleep(2)

    displayer.display('----------------',
                      '----------------')

if __name__ == '__main__':
    main()
