#!/usr/bin/env python
#
# Unittests for signal_logic.

import unittest

import signal_logic

import mock_port_expander
import signal_helper

class BasicTest(unittest.TestCase):
    def testSimple(self):
        port_expander_1 = mock_port_expander.PortExpander(0x1, None)
        inputs = ['IN_0', 'IN_1', '', '', '', '', '', '']
        outputs = ['OUT_0', 'OUT_1', 'OUT_2', 'OUT_3', '', '', '', '',
                   '', '', '', '', '', '', '', ''
                   '', '', '', '', '', '', '', '']

        # TODO(bowdidge): be able to have single value.
        logic_clauses = [('OUT_0', signal_helper.OR('IN_0')),
                         ('OUT_1', signal_helper.NOT('IN_0')),
                         ('OUT_2', signal_helper.OR('IN_0', 'IN_1'))]
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
        logic_clauses = [('OUT_0', signal_helper.OR('IN_0', 'IN_1'))]

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
        logic_clauses = [('OUT_0', signal_helper.OR('IN_0')),
                         ('OUT_1', signal_helper.NOT('OUT_0'))]

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
        logic_clauses = [('OUT_0', signal_helper.AND('IN_0', 'IN_1'))]

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

    def testReversedInput(self):
        """Check that inputs configured with reversed=True invert their hardware signal."""
        port_expander_1 = mock_port_expander.PortExpander(0x1, None)
        inputs = [{'name': 'BLOCK_1', 'reversed': True},
                  {'name': 'BLOCK_2', 'reversed': False},
                  {'unused': True},
                  'BLOCK_3', '', '', '', '']
        outputs = ['W1R', 'W1G', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', '']

        name_mapper = signal_logic.NameMapper(port_expander_1, inputs, outputs)
        self.assertTrue(name_mapper.is_input('BLOCK_1'))
        self.assertTrue(name_mapper.is_input('BLOCK_2'))
        self.assertFalse(name_mapper.is_input('unused'))

        # Hardware inputs default to False in mock_port_expander.
        # BLOCK_1 (reversed=True) should evaluate to True (e.g. block occupied when pulled low).
        # BLOCK_2 (reversed=False) and BLOCK_3 (str) should evaluate to False.
        self.assertTrue(name_mapper.test_input('BLOCK_1'))
        self.assertFalse(name_mapper.test_input('BLOCK_2'))
        self.assertFalse(name_mapper.test_input('BLOCK_3'))

        # When hardware input goes HIGH (True):
        # BLOCK_1 should invert to False (block clear).
        port_expander_1.mock_set_input(0, True)
        self.assertFalse(name_mapper.test_input('BLOCK_1'))

        # When hardware input for BLOCK_2 goes HIGH:
        port_expander_1.mock_set_input(1, True)
        self.assertTrue(name_mapper.test_input('BLOCK_2'))

    def testReversedInputInLogic(self):
        """Check that reversed inputs correctly drive logic evaluation and outputs."""
        port_expander_1 = mock_port_expander.PortExpander(0x1, None)
        inputs = [{'name': 'BLOCK_1', 'reversed': True},
                  {'unused': True}, '', '', '', '', '', '']
        outputs = ['W1R', 'W1G', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', '']

        logic_clauses = [('W1R', signal_helper.OR('BLOCK_1')),
                         ('W1G', signal_helper.NOT('W1R'))]

        name_mapper = signal_logic.NameMapper(port_expander_1, inputs, outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        # Initially hardware input 0 is False (low).
        # Since BLOCK_1 has reversed=True, BLOCK_1 is True -> W1R is True, W1G is False.
        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))

        # Hardware input 0 goes True (high, block cleared).
        # BLOCK_1 becomes False -> W1R is False, W1G is True.
        port_expander_1.mock_set_input(0, True)
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))

    def testLayoutConfiguration(self):
        """Verify that the production layout configuration in layout.py loads and polls cleanly."""
        import layout
        mappers = [
            signal_logic.NameMapper(
                mock_port_expander.PortExpander(c['address'], None),
                c['inputs'],
                c['outputs']
            )
            for c in layout.EXPANDERS
        ]
        logic_engine = signal_logic.Logic(mappers)
        logic_engine.set_logic(layout.LOGIC_CLAUSES)
        # Should evaluate all rules without raising KeyError or unhandled exceptions
        logic_engine.poll()

if __name__ == '__main__':
    unittest.main()
