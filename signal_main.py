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

    # Vasona branch has two port expander cards for
    # 16 inputs and 48 outputs.
    port_expander_1 = port_expander.PortExpander(0x20, lcd_panel)
    port_expander_2 = port_expander.PortExpander(0x21, lcd_panel)

    port_expander_3 = None
    port_expander_4 = None

    port_expander_3 = port_expander.PortExpander(0x22, lcd_panel)
    port_expander_4 = port_expander.PortExpander(0x23, lcd_panel)

    port_expander_1.setup()
    port_expander_2.setup()

    if port_expander_3:
        port_expander_3.setup()
    if port_expander_4:
        port_expander_4.setup()
    
    lcd_panel.display('Testing lights', '')
    print('Testing all lights - flashing all pairs.')
    repeat = 10
    if args.test:
        repeat = 100000
    for i in range(0, repeat):
        # Set to all green.
        port_expander_1.set_outputs(0x5500)
        port_expander_2.set_outputs(0x5555)

        if port_expander_3:
            port_expander_3.set_outputs(0x5500)
        if port_expander_4:
            port_expander_4.set_outputs(0x5555)

        time.sleep(0.25)
        # Set to all red.
        port_expander_1.set_outputs(0xaa00)
        port_expander_2.set_outputs(0xaaaa)

        if port_expander_3:
            port_expander_3.set_outputs(0xaa00)
        if port_expander_4:
            port_expander_4.set_outputs(0xaaaa)
        time.sleep(0.25)

        print('')
        for expander in [port_expander_1, port_expander_2,
                         port_expander_3, port_expander_4]:
            values = ''
            for index in range(0, 8):
                values += '%s ' % str(expander.get_input(index))[0]
            print('Expander %02x: %s' % (expander.device,
                                         values))
                                             
                              
    lcd_panel.display('Signals running', '')

    # Set all signals to green for initial values.
    port_expander_1.set_outputs(0x5500)
    port_expander_2.set_outputs(0x5555)
    port_expander_3.set_outputs(0x5500)
    port_expander_4.set_outputs(0x5555)

    # For block occupancy, input is brought low if block is occupied.
    # For switches, generally depends on how switch was wired.
    inputs = [{'name': 'BLOCK_1', 'reversed': True},
              {'name': 'BLOCK_2', 'reversed': True},
              {'name': 'BLOCK_3', 'reversed': True},
              {'name': 'BLOCK_4', 'reversed': True},
              {'name': 'SW_ALMA_E', 'reversed': True},
              {'name': 'SW_GLEN_W', 'reversed': True},
              {'name': 'SW_GLEN_E', 'reversed': True},
              {'unused': True}]
    outputs = ['W1R', 'W1G', 'W2UR', 'W2UG',
               'W2LR', 'W2LG', 'W3R', 'W3G']

    inputs_2 = []
    outputs_2 = ['W4UR', 'W4UG', 'W4LR', 'W4LG',
                 'E1R', 'E1G', 'E2UR', 'E2UG',
                 'E2LR', 'E2LG', 'E3UR', 'E3UG',
                 'E3LR', 'E3LG', 'E4R', 'E4G']

    inputs_3 = [{'name': 'BLOCK_5', 'reversed': True},
                {'name': 'BLOCK_6', 'reversed': True},
                {'name': 'BLOCK_7', 'reversed': True},
                {'name': 'BLOCK_8', 'reversed': True},
                {'name': 'SW_ALMA_W', 'reversed': True},
                {'name': 'SW_LG_E', 'reversed': True},
                {'name': 'SW_LG_W', 'reversed': True},
                {'name': 'SW_VASONA', 'reversed': True}]
    outputs_3 = ['W5UR', 'W5UG', 'W5LR', 'W5LG',
                 'W6R', 'W6G', 'W7UR', 'W7UG']

    inputs_4 = []
    outputs_4 = ['W7LR', 'W7LG', 'W8R', 'W8G',
                 'E5UR', 'E5UG', 'E5LR', 'E5LG',
                 'E6UR', 'E6UG', 'E7R', 'E7G',
                 'E8R', 'E8G', 'Camp8R', 'Camp8G']

    # Specify the inputs and outputs in order.
    # Expects 32 total inputs and outputs including unused.
    # inputs will fill port A, then outputs will fill the rest.
    name_mapper_1 = signal_logic.NameMapper(port_expander_1, inputs, outputs)
    name_mapper_2 = signal_logic.NameMapper(port_expander_2,
                                            inputs_2, outputs_2)

    name_mapper_3 = signal_logic.NameMapper(port_expander_3,
                                            inputs_3, outputs_3)

    name_mapper_4 = signal_logic.NameMapper(port_expander_4,
                                            inputs_4, outputs_4)

    logic_thingy = signal_logic.Logic([name_mapper_1, name_mapper_2,
                                       name_mapper_3, name_mapper_4],
                                      lcd_panel)

    logic_clauses = [('W1R', signal_logic.OR('BLOCK_1', 'SW_GLEN_E')),
                     ('W1G', signal_logic.NOT('W1R')),
                     ('W2UR', signal_logic.OR('SW_GLEN_E',
                                              'BLOCK_2')),
                     ('W2UG', signal_logic.NOT('W2UR')),
                     ('W2LR', signal_logic.OR('W2UR', 'W3R', 'SW_GLEN_W')),
                     ('W2LG', signal_logic.NOT('W2LR')),
                     # Glenwood to Wrights.
                     ('W3R', signal_logic.OR('BLOCK_3', 'BLOCK_4',
                                             'SW_GLEN_W',
                                             'SW_ALMA_E')),
                     ('W3G', signal_logic.NOT('W3R')),
                     # Wrights to Alma. Bipolar LED.
                     ('W4UR', signal_logic.OR('BLOCK_4',
                                              'SW_ALMA_E')),
                     ('W4UG', signal_logic.NOT('W4UR')),
                     ('W4LR', signal_logic.OR('W4UR',
                                              'W5UR')),
                     ('W4LG', signal_logic.NOT('W4LR')),
                     ('W5UR', signal_logic.OR('BLOCK_5',
                                              'SW_ALMA_E')),
                     ('W5UG', signal_logic.NOT('W5UR')),
                     ('W5LR', signal_logic.OR('W5UR',
                                              'BLOCK_6',
                                              'SW_ALMA_W')),
                     ('W5LG', signal_logic.NOT('W5LR')),
                     ('W6R', signal_logic.OR('BLOCK_6',
                                              'SW_ALMA_W',
                                              'SW_LG_E')),
                     ('W6G', signal_logic.NOT('W6R')),
                     ('W7LR', signal_logic.OR('W7UR',
                                              'BLOCK_8',
                                              'SW_LG_W')),
                     ('W7LG', signal_logic.NOT('W7LR')),
                     ('W7UR', signal_logic.OR('BLOCK_7',
                                              'SW_LG_E')),
                     ('W7UG', signal_logic.NOT('W7UR')),
                     ('W8R', signal_logic.OR('BLOCK_8',
                                             'SW_VASONA',
                                             'SW_LG_W')),
                     ('W8G', signal_logic.NOT('W8R')),
                     ('Camp8R', signal_logic.OR('BLOCK_8',
                                                signal_logic.NOT('SW_VASONA'))),
                     ('Camp8G', signal_logic.NOT('Camp8R')),
                     
                     ('E1R', signal_logic.OR('BLOCK_1',
                                             'SW_GLEN_E')),
                     ('E1G', signal_logic.NOT('E1R')),
                     ('E2UR', signal_logic.OR('BLOCK_2',
                                              'SW_GLEN_W')),
                     ('E2UG', signal_logic.NOT('E2UR')),
                     ('E2LR', signal_logic.OR('E2UR',
                                              'SW_GLEN_E',
                                              'BLOCK_1')),
                     ('E2LG', signal_logic.NOT('E2LR')),
                     ('E3UR', signal_logic.OR('BLOCK_3',
                                              'SW_GLEN_W')),
                     ('E3UG', signal_logic.NOT('E3UR')),
                     ('E3LR', signal_logic.OR('E3UR',
                                              'SW_GLEN_E',
                                              'BLOCK_2')),
                     ('E3LG', signal_logic.NOT('E3LR')),
                     ('E4R', signal_logic.OR('BLOCK_4',
                                             'BLOCK_3',
                                          'SW_ALMA_E',
                                          'SW_GLEN_W')),
                     ('E4G', signal_logic.NOT('E4R')),
                     ('E5UR', signal_logic.OR('BLOCK_5',
                                              'SW_ALMA_W')),
                     ('E5UG', signal_logic.NOT('E5UR')),
                     ('E5LR', signal_logic.OR('E5UR',
                                              'BLOCK_4',
                                              'SW_ALMA_E')),
                     ('E5LG', signal_logic.NOT('E5LR')),
                     ('E6UR', signal_logic.OR('BLOCK_6',
                                           'SW_ALMA_W',
                                           'SW_LG_E')),
                     ('E6UG', signal_logic.NOT('E6UR')),
                     ('E7R', signal_logic.OR('BLOCK_7',
                                            'SW_LG_W')),
                     ('E7G', signal_logic.NOT('E7R')),
                     ('E8R', signal_logic.OR('BLOCK_8',
                                             'SW_VASONA')),
                     ('E8G', signal_logic.NOT('E8R'))]
                      
    logic_thingy.set_logic(logic_clauses)
    

    iter = 0
    try:
        while True:
            print('Polling all logic!')
            logic_thingy.poll()
            time.sleep(0.25)
            
            if MOCK:
                value = iter % 2 == 0
                port_expander_1.mock_set_input(0, value)

            iter += 1
        lcd_panel.display('Signals stopping.', '')
    except Exception as e:
        logging.exception('fail in main loop')
        shutdown(lcd_panel, e)
        # Exit hard so the separate atexit 
        os._exit(1)

if __name__ == '__main__':
    main()
