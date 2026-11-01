#!/usr/bin/env python
#
# Thread-safe code for recording and supplying recent interesting events.
#
# This code is used to give the web server information about the current
# signal system state, and also to provide single messages to the attached
# I2C LED display to give debugging messages.
#
# Robert Bowdidge, October 2026

import collections
import datetime
import threading


class StatusTracker(object):
    """Thread-safe store for signal inputs, outputs, and change events."""

    def __init__(self, history_len=50):
        self._lock = threading.Lock()
        self.inputs = {}
        self.outputs = {}
        self.recent_changes = collections.deque(maxlen=history_len)
        # Most recent input change.
        # For display on LCD at server - because of size and location of
        # the screen, we only show inputs because input changes are most
        # important for debugging at the layout.
        self.pending_lcd_message = None

    def initialize_names(self, input_names, output_names):
        """Pre-populate tracker with all known input and output line names."""
        with self._lock:
            for name in input_names:
                if name:
                    self.inputs.setdefault(name, False)
            for name in output_names:
                if name:
                    self.outputs.setdefault(name, False)

    def record_change(self, name, new_value, is_input):
        """Record state change if value differs from the previous recorded state."""
        with self._lock:
            store = self.inputs if is_input else self.outputs
            old_value = store.get(name)
            if old_value != new_value:
                store[name] = new_value
                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                event = {
                    'time': timestamp,
                    'name': name,
                    'value': bool(new_value),
                    'type': 'input' if is_input else 'output',
                }
                self.recent_changes.appendleft(event)

                tag = 'IN' if is_input else 'OUT'
                val_str = 'ON' if new_value else 'OFF'
                if is_input:
                    self.pending_lcd_message = ('%s: %s' % (tag, name[:12]),
                                                'State: %s' % val_str)

    def pop_pending_lcd_message(self):
        """Retrieve and clear the latest pending message for the LCD display."""
        with self._lock:
            msg = self.pending_lcd_message
            self.pending_lcd_message = None
            return msg

    def get_snapshot(self):
        """Return a thread-safe snapshot of all inputs, outputs, and recent events."""
        with self._lock:
            return {
                'inputs': dict(self.inputs),
                'outputs': dict(self.outputs),
                'recent_changes': list(self.recent_changes),
            }
