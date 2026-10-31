#!/usr/bin/env python
#
# Run signal controller.
#
# Hardcoded to Vasona Branch.

import argparse
import atexit
import logging
import os
import sys
import time

# True if we should pretend devices exist.  For use off Raspberry Pi.
MOCK = False

if MOCK:
    import mock_display
    import mock_port_expander as port_expander
else:
    import display
    import port_expander

import layout
import signal_logic

def shutdown(lcd_panel, exc):
    if exc:
        exc_msg = repr(exc)[0:15]
        lcd_panel.display('Shutting down', 'exception')
        lcd_panel.display(exc_msg, 'shutting down')
    else:
        lcd_panel.display('Shutting down', '')
        
def main():
    parser = argparse.ArgumentParser('signal_main',
                                     'control signals')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--testall', action='store_true')
    args = parser.parse_args()
    
    if MOCK:
        lcd_panel = mock_display.ConsoleDisplayer()
    else:
        lcd_panel = display.LCDDisplayer()

    lcd_panel.display('Setting up.', '')

    atexit.register(lambda: shutdown(lcd_panel, None))

    expanders = []
    name_mappers = []
    for exp_cfg in layout.EXPANDERS:
        expander = port_expander.PortExpander(exp_cfg['address'], lcd_panel)
        expander.setup()
        expanders.append(expander)
        name_mappers.append(
            signal_logic.NameMapper(expander, exp_cfg['inputs'], exp_cfg['outputs'])
        )

    lcd_panel.display('Testing lights', '')
    print('Testing all lights - flashing all pairs.')
    repeat = 10
    if args.test:
        repeat = 100000
    for i in range(0, repeat):
        # Set to all green.
        for expander in expanders:
            mask = 0x5500 if expander.device % 2 == 0 else 0x5555
            expander.set_outputs(mask)

        time.sleep(0.25)
        # Set to all red.
        for expander in expanders:
            mask = 0xaa00 if expander.device % 2 == 0 else 0xaaaa
            expander.set_outputs(mask)
        time.sleep(0.25)

        print('')
        for expander in expanders:
            values = ''
            for index in range(0, 8):
                values += '%s ' % str(expander.get_input(index))[0]
            print('Expander %02x: %s' % (expander.device, values))

    lcd_panel.display('Signals running', '')

    # Set all signals to green.
    for expander in expanders:
        mask = 0x5500 if expander.device % 2 == 0 else 0x5555
        expander.set_outputs(mask)

    logic_thingy = signal_logic.Logic(name_mappers, lcd_panel)
    logic_thingy.set_logic(layout.LOGIC_CLAUSES)

    iter = 0
    try:
        while True:
            print('Polling all logic!')
            logic_thingy.poll()
            time.sleep(0.25)
            
            if MOCK:
                value = iter % 2 == 0
                expanders[0].mock_set_input(0, value)

            iter += 1
        lcd_panel.display('Signals stopping.', '')
    except Exception as e:
        logging.exception('fail in main loop')
        shutdown(lcd_panel, e)
        # Exit hard so the separate atexit 
        os._exit(1)

if __name__ == '__main__':
    main()
