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
import status_server
import status_tracker

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
    parser.add_argument('--port', type=int, default=8080, help='Port for HTTP status server')
    parser.add_argument('--no-http', action='store_true', help='Disable HTTP status server')
    args = parser.parse_args()
    
    if MOCK:
        lcd_panel = mock_display.ConsoleDisplayer()
    else:
        lcd_panel = display.LCDDisplayer()

    lcd_panel.display('Setting up.', '')

    atexit.register(lambda: shutdown(lcd_panel, None))

    tracker = status_tracker.StatusTracker()
    logic_engine, expanders = layout.setup_layout(
        port_expander.PortExpander, status_tracker=tracker
    )

    if not args.no_http:
        server, _ = status_server.start_status_server(tracker, port=args.port)
        print('HTTP status server running at http://0.0.0.0:%d/' % args.port)
        atexit.register(lambda: status_server.stop_status_server(server))

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

    lcd_panel.display('Signals running', '')

    # Set all signals to green.
    for expander in expanders:
        mask = 0x5500 if expander.device % 2 == 0 else 0x5555
        expander.set_outputs(mask)

    iter = 0
    try:
        while True:
            logic_engine.poll()

            # If we have an I2C LCD attached, then we'll put out status
            # messages to it.  The message changes are done here to ensure
            # other writes to I2C for signalling are not also in progress.
            pending_lcd = tracker.pop_pending_lcd_message()
            if pending_lcd:
                # Line name on first line, state on second.
                lcd_panel.display(pending_lcd[0], pending_lcd[1])

            # Wait a bit before re-polling signals.
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
