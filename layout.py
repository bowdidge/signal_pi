#!/usr/bin/env python
#
# Layout configuration and signal interlocking logic for Vasona Branch.
#

import signal_helper
from signal_helper import OR, AND, NOT

# Expander configuration.
# Each card has two chips, responding to an even address (with 8 inputs on Port A
# and 8 outputs on Port B) and an odd address (with 16 outputs across Ports A & B).
#
# For block occupancy, input is brought low if block is occupied.
# For switches, generally depends on how switch was wired.
EXPANDERS = [
    {
        'address': 0x20,
        'inputs': [
            {'name': 'BLOCK_1', 'reversed': True},
            {'name': 'BLOCK_2', 'reversed': True},
            {'name': 'BLOCK_3', 'reversed': True},
            {'name': 'BLOCK_4', 'reversed': True},
            {'name': 'SW_ALMA_E', 'reversed': False},
            {'name': 'SW_GLEN_W', 'reversed': True},
            {'name': 'SW_GLEN_E', 'reversed': True},
            {'unused': True},
        ],
        'outputs': [
            'W1R', 'W1G', 'W2UR', 'W2UG',
            'W2LR', 'W2LG', 'W3R', 'W3G',
        ],
    },
    {
        'address': 0x21,
        'inputs': [],
        'outputs': [
            'W4UR', 'W4UG', 'W4LR', 'W4LG',
            'E1R', 'E1G', 'E2UR', 'E2UG',
            'E2LR', 'E2LG', 'E3UR', 'E3UG',
            'E3LR', 'E3LG', 'E4R', 'E4G',
        ],
    },
    {
        'address': 0x22,
        'inputs': [
            {'name': 'BLOCK_5', 'reversed': True},
            {'name': 'BLOCK_6', 'reversed': True},
            {'name': 'BLOCK_7', 'reversed': True},
            {'name': 'BLOCK_8', 'reversed': True},
            {'name': 'SW_ALMA_W', 'reversed': True},
            {'name': 'SW_LG_E', 'reversed': False},
            {'name': 'SW_LG_W', 'reversed': True},
            {'name': 'SW_VASONA', 'reversed': True},
        ],
        'outputs': [
            'W5UR', 'W5UG', 'W5LR', 'W5LG',
            'W6R', 'W6G', 'W7UR', 'W7UG',
        ],
    },
    {
        'address': 0x23,
        'inputs': [],
        'outputs': [
            'W7LR', 'W7LG', 'W8R', 'W8G',
            'E5UR', 'E5UG', 'E5LR', 'E5LG',
            'E6UR', 'E6UG', 'E7R', 'E7G',
            'E8R', 'E8G', 'Camp8R', 'Camp8G',
        ],
    },
]

# Interlocking logic clauses.
LOGIC_CLAUSES = [
    ('W1R', signal_helper.OR('BLOCK_1', 'SW_GLEN_E')),
    ('W1G', signal_helper.NOT('W1R')),
    ('W2UR', signal_helper.OR('SW_GLEN_E', 'BLOCK_2')),
    ('W2UG', signal_helper.NOT('W2UR')),
    ('W2LR', signal_helper.OR('W2UR', 'W3R', 'SW_GLEN_W')),
    ('W2LG', signal_helper.NOT('W2LR')),
    # Glenwood to Wrights.
    ('W3R', signal_helper.OR('BLOCK_3', 'BLOCK_4',
                            'SW_GLEN_W',
                            'SW_ALMA_E')),
    ('W3G', signal_helper.NOT('W3R')),
    # Wrights to Alma. Bipolar LED.
    ('W4UR', signal_helper.OR('BLOCK_4', 'SW_ALMA_E')),
    ('W4UG', signal_helper.NOT('W4UR')),
    ('W4LR', signal_helper.OR('W4UR', 'W5UR')),
    ('W4LG', signal_helper.NOT('W4LR')),
    ('W5UR', signal_helper.OR('BLOCK_5', 'SW_ALMA_E')),
    ('W5UG', signal_helper.NOT('W5UR')),
    ('W5LR', signal_helper.OR('W5UR', 'BLOCK_6', 'SW_ALMA_W')),
    ('W5LG', signal_helper.NOT('W5LR')),
    ('W6R', signal_helper.OR('BLOCK_6', 'SW_ALMA_W', 'SW_LG_E')),
    ('W6G', signal_helper.NOT('W6R')),
    ('W7LR', signal_helper.OR('W7UR', 'BLOCK_8', 'SW_LG_W')),
    ('W7LG', signal_helper.NOT('W7LR')),
    ('W7UR', signal_helper.OR('BLOCK_7', 'SW_LG_E')),
    ('W7UG', signal_helper.NOT('W7UR')),
    ('W8R', signal_helper.OR('BLOCK_8', 'SW_VASONA', 'SW_LG_W')),
    ('W8G', signal_helper.NOT('W8R')),
    ('Camp8R', signal_helper.OR('BLOCK_8', signal_helper.NOT('SW_VASONA'))),
    ('Camp8G', signal_helper.NOT('Camp8R')),

    ('E1R', signal_helper.OR('BLOCK_1', 'SW_GLEN_E')),
    ('E1G', signal_helper.NOT('E1R')),
    ('E2UR', signal_helper.OR('BLOCK_2', 'SW_GLEN_W')),
    ('E2UG', signal_helper.NOT('E2UR')),
    ('E2LR', signal_helper.OR('E2UR', 'SW_GLEN_E', 'BLOCK_1')),
    ('E2LG', signal_helper.NOT('E2LR')),
    ('E3UR', signal_helper.OR('BLOCK_3', 'SW_GLEN_W')),
    ('E3UG', signal_helper.NOT('E3UR')),
    ('E3LR', signal_helper.OR('E3UR', 'SW_GLEN_E', 'BLOCK_2')),
    ('E3LG', signal_helper.NOT('E3LR')),
    ('E4R', signal_helper.OR('BLOCK_4', 'BLOCK_3', 'SW_ALMA_E', 'SW_GLEN_W')),
    ('E4G', signal_helper.NOT('E4R')),
    ('E5UR', signal_helper.OR('BLOCK_5', 'SW_ALMA_W')),
    ('E5UG', signal_helper.NOT('E5UR')),
    ('E5LR', signal_helper.OR('E5UR', 'BLOCK_4', 'SW_ALMA_E')),
    ('E5LG', signal_helper.NOT('E5LR')),
    ('E6UR', signal_helper.OR('BLOCK_6', 'SW_ALMA_W', 'SW_LG_E')),
    ('E6UG', signal_helper.NOT('E6UR')),
    ('E7R', signal_helper.OR('BLOCK_7', 'SW_LG_W')),
    ('E7G', signal_helper.NOT('E7R')),
    ('E8R', signal_helper.OR('BLOCK_8', 'SW_VASONA')),
    ('E8G', signal_helper.NOT('E8R')),
]


def setup_layout(port_expander_class, status_tracker=None):
    """Build and wire the Vasona Branch layout.

    Args:
        port_expander_class: PortExpander class to instantiate (hardware or mock).
        status_tracker: Optional StatusTracker instance for sharing information with display devices..

    Returns:
        (logic_engine, expanders_list)
    """
    import signal_logic
    return signal_logic.build_engine(
        EXPANDERS, LOGIC_CLAUSES, port_expander_class, status_tracker=status_tracker
    )

