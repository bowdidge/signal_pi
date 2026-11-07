#!/usr/bin/env python
#
# Tests for the I2C port expander driver and its mock.
#
# The driver depends on the smbus module, which only exists on a Raspberry Pi.
# A fake bus is installed below so the driver's logic can be tested anywhere.
#
# Robert Bowdidge, November 2026

import contextlib
import sys
import types
import unittest

import mock_port_expander


class FakeBus(object):
    """Stand-in for smbus.SMBus that records traffic and can simulate errors."""

    def __init__(self):
        self.writes = []
        self.reads = []
        self.fail_writes = 0  # Number of upcoming writes that should fail.
        self.fail_reads = 0
        self.input_byte = 0

    def write_byte_data(self, device, register, value):
        if self.fail_writes:
            self.fail_writes -= 1
            raise IOError('simulated write failure')
        self.writes.append((device, register, value))

    def read_byte_data(self, device, register):
        if self.fail_reads:
            self.fail_reads -= 1
            raise IOError('simulated read failure')
        self.reads.append((device, register))
        return self.input_byte


class FakeSmbus(types.ModuleType):
    """Fake smbus module; SMBus() records the bus it handed out."""

    def SMBus(self, bus_number):
        self.bus = FakeBus()
        return self.bus


fake_smbus = FakeSmbus('smbus')
sys.modules['smbus'] = fake_smbus

import port_expander


class _NullWriter(object):
    """Swallow everything written to stdout.

    contextlib.redirect_stdout only exists in Python 3, and io.StringIO() is
    the wrong buffer for Python 2's byte strings, so tests swap sys.stdout
    directly.
    """

    def write(self, text):
        return len(text)

    def flush(self):
        pass


@contextlib.contextmanager
def quiet_stdout():
    """Silence stdout for the duration of the block on Python 2 and 3."""
    real_stdout = sys.stdout
    sys.stdout = _NullWriter()
    try:
        yield
    finally:
        sys.stdout = real_stdout


def quiet(func):
    """Run a test body that prints error messages without polluting test output."""
    def wrapper(*args, **kwargs):
        with quiet_stdout():
            return func(*args, **kwargs)
    return wrapper


class PortExpanderTest(unittest.TestCase):
    """Tests for the hardware driver, using a fake I2C bus."""

    def testSetOutputWritesBothBytes(self):
        """An odd-addressed device has outputs starting at bank A bit 0."""
        expander = port_expander.PortExpander(0x21)
        bus = fake_smbus.bus

        expander.set_output(0, True)

        self.assertEqual([(0x21, port_expander.OLATA, 0x01),
                          (0x21, port_expander.OLATB, 0x00)], bus.writes)
        self.assertTrue(expander.get_output_value(0))

    def testEvenDeviceOutputsStartAtBit8(self):
        """An even-addressed device uses bank A for inputs, so outputs start at bit 8."""
        expander = port_expander.PortExpander(0x20)
        bus = fake_smbus.bus

        expander.set_output(0, True)

        self.assertEqual([(0x20, port_expander.OLATA, 0x00),
                          (0x20, port_expander.OLATB, 0x01)], bus.writes)
        self.assertTrue(expander.get_output_value(0))
        self.assertFalse(expander.get_output_value(1))

    def testUnchangedOutputIsNotRewritten(self):
        """Setting an output to its current value must not touch the I2C bus."""
        expander = port_expander.PortExpander(0x21)
        bus = fake_smbus.bus

        expander.set_output(0, False)
        self.assertEqual([], bus.writes)

        expander.set_output(0, True)
        bus.writes = []

        expander.set_output(0, True)
        self.assertEqual([], bus.writes)

        expander.set_output(0, False)
        self.assertEqual([(0x21, port_expander.OLATA, 0x00),
                          (0x21, port_expander.OLATB, 0x00)], bus.writes)

    def testRetryWritesSameBitAfterFailure(self):
        """A failed write must be retried against the same output bit."""
        expander = port_expander.PortExpander(0x20)
        bus = fake_smbus.bus
        bus.fail_writes = 1

        with quiet_stdout():
            expander.set_output(0, True)

        self.assertEqual([(0x20, port_expander.OLATA, 0x00),
                          (0x20, port_expander.OLATB, 0x01)], bus.writes)
        self.assertEqual(0x100, expander.now_value)

    @quiet
    def testGetInputRaisesAfterRetries(self):
        """Repeated read failures must raise the I2C error, not a NameError."""
        expander = port_expander.PortExpander(0x20)
        fake_smbus.bus.fail_reads = 10

        with self.assertRaises(IOError):
            expander.get_input(0)

    def testGetInputReturnsBit(self):
        expander = port_expander.PortExpander(0x20)
        fake_smbus.bus.input_byte = 0b00000100

        self.assertTrue(expander.get_input(2))
        self.assertFalse(expander.get_input(3))


class MockPortExpanderTest(unittest.TestCase):
    """Tests for the mock's compatibility with the real driver interface."""

    @quiet
    def testSetOutputsFromMask(self):
        """Mock set_outputs accepts the integer masks the main loop passes in."""
        expander = mock_port_expander.PortExpander(0x21)

        expander.set_outputs(0x5555)

        expected = [bool(0x5555 & (1 << index)) for index in range(24)]
        self.assertEqual(expected, expander.output_values)
        self.assertTrue(expander.get_output_value(0))
        self.assertFalse(expander.get_output_value(1))

    @quiet
    def testSetOutputsRejectsOversizedMask(self):
        expander = mock_port_expander.PortExpander(0x21)
        with self.assertRaises(ValueError):
            expander.set_outputs(1 << 24)

    @quiet
    def testSetOutputRejectsBadIndex(self):
        expander = mock_port_expander.PortExpander(0x21)
        with self.assertRaises(ValueError):
            expander.set_output(24, True)
        with self.assertRaises(ValueError):
            expander.get_input(8)


if __name__ == '__main__':
    unittest.main()
