#!/usr/bin/env python
#
# Smoke test for layout configuration.
#

import unittest

import layout
import mock_port_expander


class LayoutSmokeTest(unittest.TestCase):
    """Smoke test ensuring the Vasona Branch layout configuration minimally works."""

    # All named inputs in the layout and their logical "clear/normal" value.
    _CLEAR_STATE = {
        'BLOCK_1': False, 'BLOCK_2': False, 'BLOCK_3': False, 'BLOCK_4': False,
        'SW_ALMA_E': False,
        'SW_GLEN_W': False, 'SW_GLEN_E': False,
        'BLOCK_5': False, 'BLOCK_6': False, 'BLOCK_7': False, 'BLOCK_8': False,
        'SW_ALMA_W': False,
        'SW_LG_E': False, 'SW_LG_W': False,
        'SW_VASONA': False,
    }

    def setUp(self):
        self.logic_engine, self.expanders = layout.setup_layout(
            mock_port_expander.PortExpander
        )

    def _set_all_clear(self):
        """Set every input to its logical clear/normal state."""
        for name, value in self._CLEAR_STATE.items():
            self.logic_engine.set_input(name, value)

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
        self._set_all_clear()
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
        self._set_all_clear()
        self.logic_engine.poll()

        self.assertFalse(self.logic_engine.variable_value('W1R'))
        self.assertTrue(self.logic_engine.variable_value('W1G'))

        # Occupy BLOCK_1
        self.logic_engine.set_input('BLOCK_1', True)
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

        # Clear BLOCK_1 back to unoccupied
        self.logic_engine.set_input('BLOCK_1', False)
        self.logic_engine.poll()

        self.assertFalse(self.logic_engine.variable_value('W1R'))
        self.assertTrue(self.logic_engine.variable_value('W1G'))

    def testThrownSwitchGlenwoodWest(self):
        """Throwing SW_GLEN_W must place protecting signals E3UR, E4R, and W3R at stop.

        Note: Signal heads 3 and 4 in this layout are single-headed westbound (W3R)
        and eastbound (E4R), while signal 3 eastbound has an upper head (E3UR).
        """
        self._set_all_clear()
        self.logic_engine.poll()

        # In clear/normal state, these signals show green (Red is False, Green is True)
        self.assertFalse(self.logic_engine.variable_value('E3UR'))
        self.assertTrue(self.logic_engine.variable_value('E3UG'))
        self.assertFalse(self.logic_engine.variable_value('E4R'))
        self.assertTrue(self.logic_engine.variable_value('E4G'))
        self.assertFalse(self.logic_engine.variable_value('W3R'))
        self.assertTrue(self.logic_engine.variable_value('W3G'))

        # Throw SW_GLEN_W
        self.logic_engine.set_input('SW_GLEN_W', True)
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

        # Restore switch to normal
        self.logic_engine.set_input('SW_GLEN_W', False)
        self.logic_engine.poll()

        self.assertFalse(self.logic_engine.variable_value('E3UR'))
        self.assertTrue(self.logic_engine.variable_value('E3UG'))
        self.assertFalse(self.logic_engine.variable_value('E4R'))
        self.assertTrue(self.logic_engine.variable_value('E4G'))
        self.assertFalse(self.logic_engine.variable_value('W3R'))
        self.assertTrue(self.logic_engine.variable_value('W3G'))

    def testBlock3OccupancySignals(self):
        """Train in single-track BLOCK_3 sets W3R, E3UR, and E4R to red, but leaves E2 and W4 green."""
        self._set_all_clear()
        self.logic_engine.poll()

        # Occupy BLOCK_3
        self.logic_engine.set_input('BLOCK_3', True)
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


    def testCamp8SignalVasonaSwitch(self):
        """Check that the Camp8R signal at Vasona Junction is correct.

        Camp8R has unique logic because it's a junction, and the signal
        stopping traffic from the divergent route.

        In the normal/clear state SW_VASONA=False, so
        NOT(SW_VASONA)=True and Camp8R is always True (protecting the
        Vasona siding). Throwing SW_VASONA clears Camp8R; occupying
        BLOCK_8 brings it back Tru regardless.

        """
        self._set_all_clear()
        self.logic_engine.poll()

        # Normal position: NOT(SW_VASONA=False) = True -> Camp8R True (siding protected).
        self.assertTrue(self.logic_engine.variable_value('Camp8R'),
                        'Camp8R should be red when SW_VASONA is in normal position')
        self.assertFalse(self.logic_engine.variable_value('Camp8G'))

        # Throw SW_VASONA: NOT(True) = False, BLOCK_8 still clear -> Camp8R False.
        self.logic_engine.set_input('SW_VASONA', True)
        self.logic_engine.poll()
        self.assertFalse(self.logic_engine.variable_value('Camp8R'),
                         'Camp8R should clear when SW_VASONA is thrown and block is empty')
        self.assertTrue(self.logic_engine.variable_value('Camp8G'))

        # Occupy BLOCK_8 while switch thrown -> Camp8R True again.
        self.logic_engine.set_input('BLOCK_8', True)
        self.logic_engine.poll()
        self.assertTrue(self.logic_engine.variable_value('Camp8R'),
                        'Camp8R should be red when BLOCK_8 is occupied regardless of switch')
        self.assertFalse(self.logic_engine.variable_value('Camp8G'))

    def testSignalsAtPassingSiding(self):
        """Train in BLOCK_2 sets W2UR, W2LR, E2UR, and E3LR to red."""
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('BLOCK_2', True)
        self.logic_engine.poll()

        # Signals protecting entry to block will be red.
        # E3LR is red to warn oncoming train that next signal will be  red.
        for red in ['W2UR', 'W2LR', 'E2UR', 'E3LR']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red when BLOCK_2 is occupied' % red)
        for green in ['W2UG', 'W2LG', 'E2UG', 'E3LG']:
            self.assertFalse(self.logic_engine.variable_value(green),
                             'Expected %s to be off when BLOCK_2 is occupied' % green)

        # Signals protecting other blocks must remain green.
        for unaffected_green in ['W1G', 'E1G', 'E3UG']:
            self.assertTrue(self.logic_engine.variable_value(unaffected_green),
                            'Expected %s to stay green when only BLOCK_2 is occupied' % unaffected_green)

    def testSignalsInSingleTrackMultipleBlocks(self):
        """Train in BLOCK_4 sets W3R, W4UR, W4LR, E4R, and E5LR to red."""
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('BLOCK_4', True)
        self.logic_engine.poll()

        for red in ['W3R', 'W4UR', 'W4LR', 'E4R', 'E5LR']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red when BLOCK_4 is occupied' % red)
        for green in ['W3G', 'W4UG', 'W4LG', 'E4G', 'E5LG']:
            self.assertFalse(self.logic_engine.variable_value(green),
                             'Expected %s to be off when BLOCK_4 is occupied' % green)

    def testSignalsAtPassingSiding2(self):
        """Check Alma siding is correct too.

        rain in BLOCK_5 sets W5UR, W5LR, E5UR, and E5LR to red.
        """
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('BLOCK_5', True)
        self.logic_engine.poll()

        for red in ['W5UR', 'W5LR', 'E5UR', 'E5LR']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red when BLOCK_5 is occupied' % red)
        for green in ['W5UG', 'W5LG', 'E5UG', 'E5LG']:
            self.assertFalse(self.logic_engine.variable_value(green),
                             'Expected %s to be off when BLOCK_5 is occupied' % green)

        # Adjacent signals protecting trains leaving the block should stay green.
        for unaffected_green in ['W4UG', 'E6UG']:
            self.assertTrue(self.logic_engine.variable_value(unaffected_green),
                            'Expected %s to stay green when only BLOCK_5 is occupied' % unaffected_green)

    def testBlock6OccupancySignals(self):
        """Train in BLOCK_6 sets W5LR, W6R, and E6UR to red."""
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('BLOCK_6', True)
        self.logic_engine.poll()

        for red in ['W5LR', 'W6R', 'E6UR']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red when BLOCK_6 is occupied' % red)
        for green in ['W5LG', 'W6G', 'E6UG']:
            self.assertFalse(self.logic_engine.variable_value(green),
                             'Expected %s to be off when BLOCK_6 is occupied' % green)

    def testBlock7OccupancySignals(self):
        """Train in BLOCK_7 sets W7UR, W7LR, and E7R to red.

        Note: W7LR depends on W7UR, but W7LR is listed before W7UR in
        LOGIC_CLAUSES (layout.py lines 96/98), so W7LR picks up the updated
        W7UR value one poll after W7UR itself changes.  Two polls are required.
        """
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('BLOCK_7', True)
        self.logic_engine.poll()

        # W7UR and E7R are resolved immediately from raw inputs.
        for red in ['W7UR', 'E7R']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red when BLOCK_7 is occupied' % red)
        for green in ['W7UG', 'E7G']:
            self.assertFalse(self.logic_engine.variable_value(green),
                             'Expected %s to be off when BLOCK_7 is occupied' % green)

        # W7LR depends on W7UR, which is listed after W7LR in LOGIC_CLAUSES,
        # so it takes a second poll to propagate.
        self.logic_engine.poll()
        self.assertTrue(self.logic_engine.variable_value('W7LR'),
                        'Expected W7LR to be red after second poll when BLOCK_7 is occupied')
        self.assertFalse(self.logic_engine.variable_value('W7LG'),
                         'Expected W7LG to be off after second poll when BLOCK_7 is occupied')

    def testBlock8OccupancySignals(self):
        """Train in BLOCK_8 sets W7LR, W8R, and E8R to red."""
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('BLOCK_8', True)
        self.logic_engine.poll()

        for red in ['W7LR', 'W8R', 'E8R']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red when BLOCK_8 is occupied' % red)
        for green in ['W7LG', 'W8G', 'E8G']:
            self.assertFalse(self.logic_engine.variable_value(green),
                             'Expected %s to be off when BLOCK_8 is occupied' % green)

    def testThrownSwitchAlmaEast(self):
        """Check that a switch thrown to the siding sets correct signals red.

        The signals at the switch should be red, as well as the signal
        protecting the single track block leading into the siding.

        For east end of Alma, sets W3R, W4UR,
        W5UR, E4R, and E5LR to red.  Note all signals from Alma to Glenwood
        westbound are red because no train should leave Glenwood if siding
        is open in Alma.
        """
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('SW_ALMA_E', True)
        self.logic_engine.poll()

        for red in ['W3R', 'W4UR', 'W5UR', 'E4R', 'E5LR']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red when SW_ALMA_E is thrown' % red)
        for green in ['W3G', 'W4UG', 'W5UG', 'E4G', 'E5LG']:
            self.assertFalse(self.logic_engine.variable_value(green),
                             'Expected %s to be off when SW_ALMA_E is thrown' % green)

        # Restore switch; signals must return to green.
        self.logic_engine.set_input('SW_ALMA_E', False)
        self.logic_engine.poll()
        for green in ['W3G', 'W4UG', 'W5UG', 'E4G', 'E5LG']:
            self.assertTrue(self.logic_engine.variable_value(green),
                            'Expected %s to return to green after SW_ALMA_E restored' % green)

    def testSimultaneousOccupancyAndThrownSwitch(self):
        """BLOCK_1 occupied and SW_GLEN_W thrown simultaneously must keep all
        affected signals red -- faults must accumulate via OR, not mask each other.
        """
        self._set_all_clear()
        self.logic_engine.poll()

        self.logic_engine.set_input('BLOCK_1', True)
        self.logic_engine.set_input('SW_GLEN_W', True)
        self.logic_engine.poll()

        for red in ['W1R', 'W3R', 'E3UR', 'E4R']:
            self.assertTrue(self.logic_engine.variable_value(red),
                            'Expected %s to be red under simultaneous BLOCK_1 + SW_GLEN_W fault' % red)

    def testClearBlockRestoresGreenInOnePoll(self):
        """Check signals go green after block goes vacant.

        Guards against any 'signal stuck red' regression.
        """
        self._set_all_clear()
        self.logic_engine.poll()

        # Introduce a fault
        self.logic_engine.set_input('BLOCK_1', True)
        self.logic_engine.poll()
        self.assertTrue(self.logic_engine.variable_value('W1R'))
        self.assertFalse(self.logic_engine.variable_value('W1G'))

        # Clear fault -- one poll is all that should be needed
        self.logic_engine.set_input('BLOCK_1', False)
        self.logic_engine.poll()

        self.assertFalse(self.logic_engine.variable_value('W1R'),
                         'W1R should return to False after BLOCK_1 clears')
        self.assertTrue(self.logic_engine.variable_value('W1G'),
                        'W1G should return to True after BLOCK_1 clears')


if __name__ == '__main__':
    unittest.main()
