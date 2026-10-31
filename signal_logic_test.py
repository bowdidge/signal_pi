#!/usr/bin/env python
#
# Unittests for signal_logic.

import unittest

import signal_logic

import mock_port_expander
import signal_helper

class BasicTest(unittest.TestCase):
    def testSimple(self):
        port_expander_1 = mock_port_expander.PortExpander(0x1)
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
        port_expander_1 = mock_port_expander.PortExpander(0x1)
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
        port_expander_1 = mock_port_expander.PortExpander(0x1)
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
        port_expander_1 = mock_port_expander.PortExpander(0x1)
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
        port_expander_1 = mock_port_expander.PortExpander(0x1)
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
        port_expander_1 = mock_port_expander.PortExpander(0x1)
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
        logic_engine, expanders = layout.setup_layout(mock_port_expander.PortExpander)
        self.assertEqual(len(expanders), 4)
        # Should evaluate all rules without raising KeyError or unhandled exceptions
        logic_engine.poll()

    def testMultiExpanderRouting(self):
        """Verify that Logic coordinates inputs and outputs across multiple expanders."""
        expander_1 = mock_port_expander.PortExpander(0x20)
        expander_2 = mock_port_expander.PortExpander(0x21)
        expander_3 = mock_port_expander.PortExpander(0x22)

        mapper_1 = signal_logic.NameMapper(
            expander_1,
            inputs=['EXP1_IN_0', 'EXP1_IN_1', '', '', '', '', '', ''],
            outputs=['EXP1_OUT_0', '', '', '', '', '', '', '']
        )
        mapper_2 = signal_logic.NameMapper(
            expander_2,
            inputs=['EXP2_IN_0', '', '', '', '', '', '', ''],
            outputs=['EXP2_OUT_0', '', '', '', '', '', '', '']
        )
        mapper_3 = signal_logic.NameMapper(
            expander_3,
            inputs=['', '', '', '', '', '', '', ''],
            outputs=['EXP3_OUT_0', '', '', '', '', '', '', '']
        )

        logic_engine = signal_logic.Logic([mapper_1, mapper_2, mapper_3])

        # Cross-expander rules:
        # 1. Output on Expander 2 depends on Input on Expander 1
        # 2. Output on Expander 3 depends on Inputs from both Expander 1 AND Expander 2
        # 3. Output on Expander 1 depends on Output on Expander 2
        logic_clauses = [
            ('EXP2_OUT_0', signal_helper.OR('EXP1_IN_0')),
            ('EXP3_OUT_0', signal_helper.AND('EXP1_IN_0', 'EXP2_IN_0')),
            ('EXP1_OUT_0', signal_helper.OR('EXP2_OUT_0')),
        ]
        logic_engine.set_logic(logic_clauses)

        # Initial state: all inputs False
        logic_engine.poll()
        self.assertFalse(expander_2.get_output_value(0))
        self.assertFalse(expander_3.get_output_value(0))
        self.assertFalse(expander_1.get_output_value(0))

        # Turn on input on expander 1
        expander_1.mock_set_input(0, True)
        logic_engine.poll()

        # Expander 2 output should be True (driven by Expander 1 input)
        self.assertTrue(expander_2.get_output_value(0))
        # Expander 1 output should be True (driven by Expander 2 output)
        self.assertTrue(expander_1.get_output_value(0))
        # Expander 3 output should still be False (waiting on Expander 2 input)
        self.assertFalse(expander_3.get_output_value(0))

        # Now turn on input on expander 2
        expander_2.mock_set_input(0, True)
        logic_engine.poll()

        # Expander 3 output should now be True (both Expander 1 and 2 inputs are True)
        self.assertTrue(expander_3.get_output_value(0))

    def testMultiTermOr(self):
        """Verify that OR works with 3, 4, and 5 terms."""
        port_expander_1 = mock_port_expander.PortExpander(0x1)
        inputs = ['IN_0', 'IN_1', 'IN_2', 'IN_3', 'IN_4', '', '', '']
        outputs = ['OUT_3', 'OUT_4', 'OUT_5', '', '', '', '', '',
                   '', '', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', '']

        logic_clauses = [
            ('OUT_3', signal_helper.OR('IN_0', 'IN_1', 'IN_2')),
            ('OUT_4', signal_helper.OR('IN_0', 'IN_1', 'IN_2', 'IN_3')),
            ('OUT_5', signal_helper.OR('IN_0', 'IN_1', 'IN_2', 'IN_3', 'IN_4')),
        ]
        name_mapper = signal_logic.NameMapper(port_expander_1, inputs, outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        # All inputs False initially -> all outputs False
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Set 5th term (IN_4) -> only OUT_5 becomes True
        port_expander_1.mock_set_input(4, True)
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertTrue(port_expander_1.get_output_value(2))

        # Set 4th term (IN_3) -> OUT_4 and OUT_5 become True
        port_expander_1.mock_set_input(4, False)
        port_expander_1.mock_set_input(3, True)
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))
        self.assertTrue(port_expander_1.get_output_value(2))

        # Set 3rd term (IN_2) -> all become True
        port_expander_1.mock_set_input(3, False)
        port_expander_1.mock_set_input(2, True)
        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))
        self.assertTrue(port_expander_1.get_output_value(2))

    def testMultiTermAnd(self):
        """Verify that AND works with 3, 4, and 5 terms."""
        port_expander_1 = mock_port_expander.PortExpander(0x1)
        inputs = ['IN_0', 'IN_1', 'IN_2', 'IN_3', 'IN_4', '', '', '']
        outputs = ['OUT_3', 'OUT_4', 'OUT_5', '', '', '', '', '',
                   '', '', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', '']

        logic_clauses = [
            ('OUT_3', signal_helper.AND('IN_0', 'IN_1', 'IN_2')),
            ('OUT_4', signal_helper.AND('IN_0', 'IN_1', 'IN_2', 'IN_3')),
            ('OUT_5', signal_helper.AND('IN_0', 'IN_1', 'IN_2', 'IN_3', 'IN_4')),
        ]
        name_mapper = signal_logic.NameMapper(port_expander_1, inputs, outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        # Initially all False -> all False
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Turn on IN_0 and IN_1 (2 terms) -> not enough for 3-term AND
        port_expander_1.mock_set_input(0, True)
        port_expander_1.mock_set_input(1, True)
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Turn on IN_2 -> OUT_3 (3-term) becomes True
        port_expander_1.mock_set_input(2, True)
        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Turn on IN_3 -> OUT_4 (4-term) becomes True
        port_expander_1.mock_set_input(3, True)
        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Turn on IN_4 -> OUT_5 (5-term) becomes True
        port_expander_1.mock_set_input(4, True)
        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))
        self.assertTrue(port_expander_1.get_output_value(2))

        # Turn off IN_0 -> all immediately False
        port_expander_1.mock_set_input(0, False)
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

    def testNestedExpressions(self):
        """Verify that combinators can be nested (e.g. OR(A, NOT(B)), OR(A, AND(B, C)))."""
        port_expander_1 = mock_port_expander.PortExpander(0x1)
        inputs = ['IN_0', 'IN_1', 'IN_2', '', '', '', '', '']
        outputs = ['OUT_OR_NOT', 'OUT_OR_AND', 'OUT_DE_MORGAN', '', '', '', '', '',
                   '', '', '', '', '', '', '', '',
                   '', '', '', '', '', '', '', '']

        logic_clauses = [
            # OR with nested NOT: True if IN_0 is True OR IN_1 is False
            ('OUT_OR_NOT', signal_helper.OR('IN_0', signal_helper.NOT('IN_1'))),
            # OR with nested AND: True if IN_0 is True OR (IN_1 and IN_2 are True)
            ('OUT_OR_AND', signal_helper.OR('IN_0', signal_helper.AND('IN_1', 'IN_2'))),
            # NOT of OR: True only if neither IN_0 nor IN_1 is True
            ('OUT_DE_MORGAN', signal_helper.NOT(signal_helper.OR('IN_0', 'IN_1'))),
        ]
        name_mapper = signal_logic.NameMapper(port_expander_1, inputs, outputs)
        logic_thingy = signal_logic.Logic([name_mapper])
        logic_thingy.set_logic(logic_clauses)

        # Initially all False:
        # OUT_OR_NOT: IN_0(False) or NOT(IN_1(False)) -> False or True -> True
        # OUT_OR_AND: False or (False and False) -> False
        # OUT_DE_MORGAN: NOT(False or False) -> True
        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertTrue(port_expander_1.get_output_value(2))

        # Set IN_1 to True:
        # OUT_OR_NOT: False or NOT(True) -> False
        # OUT_OR_AND: False or (True and False) -> False
        # OUT_DE_MORGAN: NOT(False or True) -> False
        port_expander_1.mock_set_input(1, True)
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertFalse(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Set IN_2 to True as well:
        # OUT_OR_AND: False or (True and True) -> True
        port_expander_1.mock_set_input(2, True)
        logic_thingy.poll()
        self.assertFalse(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

        # Set IN_0 to True:
        # OUT_OR_NOT: True or NOT(True) -> True
        # OUT_OR_AND: True or ... -> True
        # OUT_DE_MORGAN: NOT(True or ...) -> False
        port_expander_1.mock_set_input(0, True)
        logic_thingy.poll()
        self.assertTrue(port_expander_1.get_output_value(0))
        self.assertTrue(port_expander_1.get_output_value(1))
        self.assertFalse(port_expander_1.get_output_value(2))

if __name__ == '__main__':
    unittest.main()
