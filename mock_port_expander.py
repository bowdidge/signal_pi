#
# Simple mock to imitate the PortExpander class which manipulates the
# Microchip MCP23017 chip.
#
# Robert Bowdidge, February 2024

class PortExpander(object):
    def __init__(self, device):
        self.device = device
        self.input_values = [False] * 8
        self.output_values = [False] * 24

    def setup(self):
        self.output_values = [False] * 24

    def mock_set_input(self, index, value):
        print('Fake setting value of device %d input %d to %s' % (
            self.device, index, value))
        self._check_input_index(index)
        self.input_values[index] = value

    def get_output_value(self, index):
        """Retrieve last value for output."""
        self._check_output_index(index)
        return self.output_values[index]

    def get_input(self, index):
        self._check_input_index(index)
        value = self.input_values[index]
        print('Request value from device %d input %d is %s' %(self.device,
                                                              index, value))
        return value

    def set_output(self, index, value):
        self._check_output_index(index)
        print('Set device %s output %s to %s' % (self.device, index, value))
        self.output_values[index] = value

    def set_outputs(self, value):
        """Set all outputs at once from a bit mask, one bit per output."""
        if not 0 <= value < (1 << 24):
            raise ValueError('Invalid output mask: %d' % value)
        print('Set device %s outputs to 0x%04x' % (self.device, value))
        for index in range(0, 24):
            self.output_values[index] = bool(value & (1 << index))

    def _check_input_index(self, index):
        if not 0 <= index < 8:
            raise ValueError('Invalid input index: %d' % index)

    def _check_output_index(self, index):
        if not 0 <= index < 24:
            raise ValueError('Invalid output index: %d' % index)
