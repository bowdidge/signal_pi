#!/usr/bin/env python
#
# display_test: exercise the LCDDisplayer class.
#
# Robert Bowdidge, February 2024.

import unittest

# Are we running on the Raspberry Pi with needed device, or elsewhere?
MOCK=False
try:
    import rpi_lcd
except ImportError as e:
    MOCK=True

# TODO(bowdidge): Consider changing display i
if MOCK:
    import mock_display
else:
    import display

class DisplayTest(unittest.TestCase):

    def testSimple(self):
        if MOCK:
            lcd = mock_display.ConsoleDisplayer()
        else:
            lcd = display.LCDDisplayer()

        lcd.display('foo', 'bar')


if __name__ == '__main__':
    unittest.main()
    
