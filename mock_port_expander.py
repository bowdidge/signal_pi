#
# Simple debugging port expander.

class PortExpander(object):
    def __init__(self, device, display):
        self.device = device
        self.input_values = [False for x in range(0, 8)]
        self.output_values = [False for x in range(0, 24)]
        self.display = display
        if self.display:
            self.display.display('Foo', 'bar')
        pass

    def setup(self):
        pass

    def mock_set_input(self, index, value):
        print('Fake setting value of device %d input %d to %s' % (
            self.device, index, value))
        self.input_values[index] = value

    def get_output_value(self, index):
        """Retrieve last value for output."""
        return self.output_values[index]

    def get_input(self, index):
        value = self.input_values[index]
        print('Request value from device %d input %d is %s' %(self.device,
                                                              index, value))
        return value

    def set_output(self, index, value):
        print('Set device %s output %s to %s' % (self.device, index, value))
        self.output_values[index] = value
        pass

    def set_outputs(self, value):
        print('Set device %s outputs to 0x%04x' % (self.device, value))
        bits = value
        for index in range(0, 24):
            bit = bool(bits % 2)
            self.output_values[index] = bit
            bits = bits >> 1
            
        pass

