#!/usr/bin/python
#
# Control signals with logic.

import time

class NameMapper(object):
    """Wraps PortExpander so it can be manipulated by names.

    Multiple port expanders can be tested to find the correct
    one for a port name.
    """
    
    def __init__(self, port_expander, inputs, outputs):
        self.port_expander = port_expander
        self.inputs = inputs
        self.outputs = outputs
        pass

    def has_name(self, name):
        """Returns true if the output name exists in the port expander."""
        return name in self.outputs

    def is_input(self, name):
        """Returns true if an input with the name exists in the expander."""
        for input in self.inputs:
            if type(input) == dict:
                if input.get('name') == name:
                    return True
            else:
                if input == name:
                    return True
        return False
    
    def test_input(self, name):
        """Returns input state (True for high), or None if doesn't exist.

        If input is known to be reversed, then return the opposite.
        """
        index = 0
        for input in self.inputs:
            if type(input) == dict:
                input_name = input.get('name')
                reversed = input.get('reversed', False)
            else:
                input_name = input
                reversed = False
            if name == input_name:
                value = self.port_expander.get_input(index)
                # lcd_panel('Input %s is %s' % (name, bool(value)), '')
                if reversed:
                    return not(bool(value))
                else:
                    return bool(value)
                
            index += 1

        # No match?  check if there's an output with that name.
        if name in self.outputs:
            output_index = self.outputs.index(name)
            output_value = self.port_expander.get_output_value(output_index)
            return output_value

        print('Unknown input %s in %s' % (name, self.inputs))
        return None

    def set_output(self, name, value):
        # TODO(bowdidge): Avoid rewriting value if not changed.
        if name not in self.outputs:
            return None
        output_index = self.outputs.index(name)
        self.port_expander.set_output(output_index, value)
        
    
class Logic(object):
    """Handle signal logic via inputs and outputs in port expander boards."""
    
    def __init__(self, name_mappers, lcd_panel=None):
        self.name_mappers = name_mappers
        self.lcd_panel = lcd_panel
        self.past_values = {}
        self.name_to_name_mapper = {}

        for name_mapper in self.name_mappers:
            for input in name_mapper.inputs:
                input_name = input
                reversed = False
                if type(input) == dict:
                    input_name = input.get('name')
                    reversed = input.get('reversed', False)
                if input_name:
                    self.name_to_name_mapper[input_name] = name_mapper
            for output in name_mapper.outputs:
                self.name_to_name_mapper[output] = name_mapper

    def set_logic(self, logic_classes):
        self.logic_classes = logic_classes
        
    def logic_eval(self, output_name, predicate):
        """ Evaluate the predicate and change the correct output."""

        # Evaluate here.
        name_mapper = self.name_to_name_mapper[output_name]
        val = predicate(self)
        print('Set %s to %s' % (output_name, val))
        name_mapper.set_output(output_name, val)

    def variable_value(self, input_name):
        try:
            name_mapper = self.name_to_name_mapper[input_name]
        except KeyError as e:
            print('Unknown key %s in %s' % (input_name, self.name_to_name_mapper))
            return None
        value = name_mapper.test_input(input_name)

        if name_mapper.is_input(input_name):
            past_value = self.past_values.get(input_name)
            if past_value is None or past_value != value:
                if self.lcd_panel:
                    self.lcd_panel.display('Change %s' % input_name,
                                           '%s' % value),
            self.past_values[input_name] = value
        return value

    def expression_value(self, expression):
        if callable(expression):
            return expression(self)
        return self.variable_value(expression)
            
    def poll(self):
        # Go through all logic terms and calculate the new value.
        # Undefined behavior if circular dependencies in outputs.
        for logic_term in self.logic_classes:
            output_name, predicate = logic_term
            self.logic_eval(output_name, predicate)


def build_engine(expanders_config, logic_clauses, port_expander_class, lcd_panel=None):
    """Instantiate PortExpanders, NameMappers, and wire them into a Logic engine.

    Args:
        expanders_config: List of expander definition dicts with address, inputs, outputs.
        logic_clauses: List of (output_name, predicate) logic tuples.
        port_expander_class: PortExpander class to instantiate (hardware or mock).
        lcd_panel: Optional display panel.

    Returns:
        (logic_engine, expanders_list)
    """
    expanders = []
    name_mappers = []
    for exp_cfg in expanders_config:
        expander = port_expander_class(exp_cfg['address'], lcd_panel)
        expander.setup()
        expanders.append(expander)
        name_mappers.append(
            NameMapper(expander, exp_cfg['inputs'], exp_cfg['outputs'])
        )

    logic_engine = Logic(name_mappers, lcd_panel)
    logic_engine.set_logic(logic_clauses)
    return logic_engine, expanders

