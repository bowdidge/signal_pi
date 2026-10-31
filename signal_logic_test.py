#!/usr/bin/env python
#
# Unittests for signal_logic.

import unittest

import mock_port_expander

import signal_logic

class BasicTest(unittest.TestCase):
    def testSimple(self):
        port_expander_1 = mock_port_expander.PortExpander(0x1, None)
        inputs = ['IN_0', 'IN_1', '', '', '', '', '', '']
        outputs = ['OUT_0', 'OUT_1', 'OUT_2', 'OUT_3', '', '', '', '',
                   '', '', '', '', '', '', '', ''
                   '', '', '', '', '', '', '', '']

        # TODO(bowdidge): be able to have single value.
        logic_clauses = [('OUT_0', signal_logic.OR('IN_0')),
                         ('OUT_1', signal_logic.NOT('IN_0')),
                         ('OUT_2', signal_logic.OR('IN_0', 'IN_1'))]
        name_mapper = signal_logic.NameMapper(port_expander_1,
                                              inputs,
                                              outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        logic_thingy.poll()

        # Check starting state.
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Try setting one of the inputs, and confirm logic changed.
        port_expander_1.mock_set_input(0, True)

        logic_thingy.poll()

        # Test single value.
        self.assertTrue(port_expander_1.get_output_value(0))
        # Check NOT reversed new value.
        self.assertFalse(port_expander_1.get_output_value(1))
        # Check OR got correct value.
        self.assertTrue(port_expander_1.get_output_value(2))

    def testOr(self):
        port_expander_1 = mock_port_expander.PortExpander(0x1, None)
        inputs = ['IN_0', 'IN_1', '', '', '', '', '', '']
        outputs = ['OUT_0', '', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', ''
                   '', '', '', '', '', '', '', '']

        # TODO(bowdidge): be able to have single value.
        logic_clauses = [('OUT_0', signal_logic.OR('IN_0', 'IN_1'))]

        name_mapper = signal_logic.NameMapper(port_expander_1,
                                              inputs,
                                              outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        logic_thingy.poll()

        # Check starting state.
        self.assertFalse(port_expander_1.get_output_value(0))

        # Try setting one of the inputs, and confirm logic changed
        port_expander_1.mock_set_input(0, True)

        logic_thingy.poll()

        # Test single value.
        self.assertTrue(port_expander_1.get_output_value(0))

        port_expander_1.mock_set_input(0, False)
        port_expander_1.mock_set_input(1, True)

        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))

        port_expander_1.mock_set_input(0, True)
        port_expander_1.mock_set_input(1, True)

        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        
    def testReferenceOutput(self):
        """Check that an output can be used as part of logic."""
        port_expander_1 = mock_port_expander.PortExpander(0x1, None)
        inputs = ['IN_0', 'IN_1', '', '', '', '', '', '']
        outputs = ['OUT_0', 'OUT_1', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', ''
                   '', '', '', '', '', '', '', '']

        # TODO(bowdidge): be able to have single value.
        logic_clauses = [('OUT_0', signal_logic.OR('IN_0')),
                         ('OUT_1', signal_logic.NOT('OUT_0'))]

        name_mapper = signal_logic.NameMapper(port_expander_1,
                                              inputs,
                                              outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        logic_thingy.poll()

        # Check starting state.
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))

        # Try setting one of the inputs, and confirm logic changed
        port_expander_1.mock_set_input(0, True)

        logic_thingy.poll()

        # Test single value.
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))

        port_expander_1.mock_set_input(0, False)

        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))

    def testAnd(self):
        port_expander_1 = mock_port_expander.PortExpander(0x1, None)
        inputs = ['IN_0', 'IN_1', '', '', '', '', '', '']
        outputs = ['OUT_0', '', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', ''
                   '', '', '', '', '', '', '', '']

        # TODO(bowdidge): be able to have single value.
        logic_clauses = [('OUT_0', signal_logic.AND('IN_0', 'IN_1'))]

        name_mapper = signal_logic.NameMapper(port_expander_1,
                                              inputs,
                                              outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        logic_thingy.poll()

        # Check starting state.
        self.assertFalse(port_expander_1.get_output_value(0))

        # Try setting one of the inputs, and confirm logic changed
        port_expander_1.mock_set_input(0, True)

        logic_thingy.poll()

        # Test single value.
        self.assertFalse(port_expander_1.get_output_value(0))

        port_expander_1.mock_set_input(0, False)
        port_expander_1.mock_set_input(1, True)

        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))

        port_expander_1.mock_set_input(0, True)
        port_expander_1.mock_set_input(1, True)

        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))

if __name__ == '__main__':
    unittest.main()
