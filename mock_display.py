#
# Mock that implements same interface as control LED panel.
#
# Robert Bowdidge, February 2024.

class ConsoleDisplayer(object):
    """Display debugging or status messages on LCD panel."""
    def __init__(self):
        pass

    def display(self, msg1, msg2):
        print('DISPLAY:\n%s\n%s\n' % (msg1, msg2))
