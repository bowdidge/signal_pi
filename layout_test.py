#!/usr/bin/env python
#
# Smoke test for layout configuration.
#

import unittest

import layout
import mock_port_expander


class LayoutSmokeTest(unittest.TestCase):
    """Smoke test ensuring the Vasona Branch layout configuration minimally works."""

    def setUp(self):
        self.logic_engine, self.expanders = layout.setup_layout(
            mock_port_expander.PortExpander
        )

    def testLayoutStructure(self):
        """Verify expanders and line mappings instantiate correctly."""
        self.assertEqual(len(self.expanders), 4)
        expected_addresses = [0x20, 0x21, 0x22, 0x23]
        actual_addresses = [exp.device for exp in self.expanders]
        self.assertEqual(actual_addresses, expected_addresses)

        # Check key inputs and outputs are indexed
        for input_name in ['BLOCK_1', 'BLOCK_5', 'SW_GLEN_E', 'SW_VASONA']:
            self.assertIn(input_name, self.logic_engine.name_to_name_mapper)
        for output_name in ['W1R', 'W1G', 'E1R', 'E1G', 'Camp8R', 'Camp8G']:
            self.assertIn(output_name, self.logic_engine.name_to_name_mapper)

    def testAllClausesTargetKnownOutputs(self):
        """Verify that every logic clause targets a valid declared output."""
        for output_name, _ in layout.LOGIC_CLAUSES:
            self.assertIn(
                output_name,
                self.logic_engine.name_to_name_mapper,
                'Clause target %s is not a registered output' % output_name
            )

    def testAllClearTrackProducesGreens(self):
        """When all blocks are clear and switches normal, mainline signals show green."""
        # Hardware inputs are high (True) when blocks are clear because detectors are reversed=True.
        for exp in self.expanders:
            for line in range(8):
                exp.mock_set_input(line, True)

        # TODO(bowdidge): Automatically set reversed inputs to False.
        # SW_ALMA_E is reversed.
        self.expanders[0].mock_set_input(4, False)
        # SW_LG_E is reversed.
        self.expanders[2].mock_set_input(5, False)

        self.logic_engine.poll()

        mainline_greens = [
            'W1G', 'W2UG', 'W2LG', 'W3G', 'W4UG', 'W4LG',
            'W5UG', 'W5LG', 'W6G', 'W7UG', 'W7LG', 'W8G',
            'E1G', 'E2UG', 'E2LG', 'E3UG', 'E3LG', 'E4G',
            'E5UG', 'E5LG', 'E6UG', 'E7G', 'E8G',
        ]
        mainline_reds = [
            'W1R', 'W2UR', 'W2LR', 'W3R', 'W4UR', 'W4LR',
            'W5UR', 'W5LR', 'W6R', 'W7UR', 'W7LR', 'W8R',
            'E1R', 'E2UR', 'E2LR', 'E3UR', 'E3LR', 'E4R',
            'E5UR', 'E5LR', 'E6UR', 'E7R', 'E8R',
        ]

        for green in mainline_greens:
            self.assertTrue(
                self.logic_engine.variable_value(green),
                'Expected %s to be True (clear) when track is clear' % green
            )
        for red in mainline_reds:
            self.assertFalse(
                self.logic_engine.variable_value(red),
                'Expected %s to be False (stop) when track is clear' % red
            )

    def testOccupancyDropTriggersStop(self):
        """Occupying BLOCK_1 must place protecting signals W1 and E1 at stop."""
        # Set all track clear initially
        for exp in self.expanders:
            for line in range(8):
                exp.mock_set_input(line, True)

        # TODO(bowdidge): Automatically set reversed inputs to False.
        # SW_ALMA_E is reversed.
        self.expanders[0].mock_set_input(4, False)
        # SW_LG_E is reversed.
        self.expanders[2].mock_set_input(5, False)

        self.logic_engine.poll()

        self.assertFalse(self.logic_engine.variable_value('W1R'))
        self.assertTrue(self.logic_engine.variable_value('W1G'))

        # Drop BLOCK_1 low (hardware line 0 on expander 0x20 pulled low by train wheels)
        self.expanders[0].mock_set_input(0, False)
        self.logic_engine.poll()

        # Signal must show red (W1R True, W1G False)
        self.assertTrue(
            self.logic_engine.variable_value('W1R'),
            'Expected W1R to be True when BLOCK_1 is occupied'
        )
        self.assertFalse(
            self.logic_engine.variable_value('W1G'),
            'Expected W1G to be False when BLOCK_1 is occupied'
        )

        # Clear BLOCK_1 back to unoccupied (hardware line high)
        self.expanders[0].mock_set_input(0, True)
        self.logic_engine.poll()

        self.assertFalse(self.logic_engine.variable_value('W1R'))
        self.assertTrue(self.logic_engine.variable_value('W1G'))

    def testThrownSwitchGlenwoodWest(self):
        """Throwing SW_GLEN_W must place protecting signals E3UR, E4R, and W3R at stop.

        Note: Signal heads 3 and 4 in this layout are single-headed westbound (W3R)
        and eastbound (E4R), while signal 3 eastbound has an upper head (E3UR).
        """
        # Set all track clear initially (hardware inputs high)
        for exp in self.expanders:
            for line in range(8):
                exp.mock_set_input(line, True)

        # TODO(bowdidge): Automatically set reversed inputs to False.
        # SW_ALMA_E is reversed.
        self.expanders[0].mock_set_input(4, False)
        # SW_LG_E is reversed.
        self.expanders[2].mock_set_input(5, False)

        self.logic_engine.poll()

        # In clear/normal state, these signals show green (Red is False, Green is True)
        self.assertFalse(self.logic_engine.variable_value('E3UR'))
        self.assertTrue(self.logic_engine.variable_value('E3UG'))
        self.assertFalse(self.logic_engine.variable_value('E4R'))
        self.assertTrue(self.logic_engine.variable_value('E4G'))
        self.assertFalse(self.logic_engine.variable_value('W3R'))
        self.assertTrue(self.logic_engine.variable_value('W3G'))

        # Throw SW_GLEN_W (line 5 on expander 0x20 pulled low)
        self.expanders[0].mock_set_input(5, False)
        self.logic_engine.poll()

        # E3UR, E4R, and W3R must now show red (True) and their greens must be False
        self.assertTrue(
            self.logic_engine.variable_value('E3UR'),
            'Expected E3UR to be True (stop) when SW_GLEN_W is thrown'
        )
        self.assertFalse(
            self.logic_engine.variable_value('E3UG'),
            'Expected E3UG to be False when SW_GLEN_W is thrown'
        )
        self.assertTrue(
            self.logic_engine.variable_value('E4R'),
            'Expected E4R to be True (stop) when SW_GLEN_W is thrown'
        )
        self.assertFalse(
            self.logic_engine.variable_value('E4G'),
            'Expected E4G to be False when SW_GLEN_W is thrown'
        )
        self.assertTrue(
            self.logic_engine.variable_value('W3R'),
            'Expected W3R to be True (stop) when SW_GLEN_W is thrown'
        )
        self.assertFalse(
            self.logic_engine.variable_value('W3G'),
            'Expected W3G to be False when SW_GLEN_W is thrown'
        )

        # Restore switch to normal (line 5 high)
        self.expanders[0].mock_set_input(5, True)
        self.logic_engine.poll()

        self.assertFalse(self.logic_engine.variable_value('E3UR'))
        self.assertTrue(self.logic_engine.variable_value('E3UG'))
        self.assertFalse(self.logic_engine.variable_value('E4R'))
        self.assertTrue(self.logic_engine.variable_value('E4G'))
        self.assertFalse(self.logic_engine.variable_value('W3R'))
        self.assertTrue(self.logic_engine.variable_value('W3G'))

    def testBlock3OccupancySignals(self):
        """Train in single-track BLOCK_3 sets W3R, E3UR, and E4R to red, but leaves E2 and W4 green."""
        # Set all track clear initially (hardware inputs high)
        for exp in self.expanders:
            for line in range(8):
                exp.mock_set_input(line, True)

        # TODO(bowdidge): Automatically set reversed inputs to False.
        # SW_ALMA_E is reversed.
        self.expanders[0].mock_set_input(4, False)
        # SW_LG_E is reversed.
        self.expanders[2].mock_set_input(5, False)

        self.logic_engine.poll()

        # Occupy BLOCK_3 (line 2 on expander 0x20 pulled low)
        self.expanders[0].mock_set_input(2, False)
        self.logic_engine.poll()

        # Opposing and protecting signals for the block 3/4 single-track section must show red (stop):
        # 1. W3R protects westbound entry into block 3
        self.assertTrue(
            self.logic_engine.variable_value('W3R'),
            'Expected W3R to be True (red) when BLOCK_3 is occupied'
        )
        self.assertFalse(
            self.logic_engine.variable_value('W3G'),
            'Expected W3G to be False (green off) when BLOCK_3 is occupied'
        )
        # 2. E3UR protects eastbound entry at signal 3
        self.assertTrue(
            self.logic_engine.variable_value('E3UR'),
            'Expected E3UR to be True (red) when BLOCK_3 is occupied'
        )
        self.assertFalse(
            self.logic_engine.variable_value('E3UG'),
            'Expected E3UG to be False (green off) when BLOCK_3 is occupied'
        )
        # 3. E4R protects eastbound entry into block 4 (preventing head-on collision on connected single track)
        self.assertTrue(
            self.logic_engine.variable_value('E4R'),
            'Expected E4R to be True (red) when BLOCK_3 is occupied'
        )
        self.assertFalse(
            self.logic_engine.variable_value('E4G'),
            'Expected E4G to be False (green off) when BLOCK_3 is occupied'
        )

        # Signals for exiting the block or adjacent blocks (E2 and W4) must remain green (stop is False):
        # E2 (upper and lower heads)
        self.assertFalse(
            self.logic_engine.variable_value('E2UR'),
            'Expected E2UR to be False (green) so train can leave block'
        )
        self.assertTrue(
            self.logic_engine.variable_value('E2UG'),
            'Expected E2UG to be True (green)'
        )
        self.assertFalse(
            self.logic_engine.variable_value('E2LR'),
            'Expected E2LR to be False (green)'
        )
        self.assertTrue(
            self.logic_engine.variable_value('E2LG'),
            'Expected E2LG to be True (green)'
        )
        # W4 (upper and lower heads)
        self.assertFalse(
            self.logic_engine.variable_value('W4UR'),
            'Expected W4UR to be False (green) so train can leave block'
        )
        self.assertTrue(
            self.logic_engine.variable_value('W4UG'),
            'Expected W4UG to be True (green)'
        )
        self.assertFalse(
            self.logic_engine.variable_value('W4LR'),
            'Expected W4LR to be False (green)'
        )
        self.assertTrue(
            self.logic_engine.variable_value('W4LG'),
            'Expected W4LG to be True (green)'
        )


if __name__ == '__main__':
    unittest.main()
