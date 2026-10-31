#
# Mock control LED panel.

class ConsoleDisplayer(object):
    """Display debugging or status messages on LCD panel."""
    def __init__(self):
        pass

    def display(self, msg1, msg2):
        print('DISPLAY:\n%s\n%s\n' % (msg1, msg2))
