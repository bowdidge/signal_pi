#!/usr/bin/python
#
# Control signals with logic.

import time

# Registers for GPIO Ports Bank=0
IODIRA = 0x00 # pin dir reg
IODIRB = 0x01
IPOLA = 0x02
IPOLB = 0x03
GPINTENA = 0x04
GPINTENB = 0x05
GPPUA = 0x0c
GPPUB = 0x0d
GPIOA = 0x12 # register for inputs
GPIOB = 0x13
OLATA = 0x14 # register for outputs
OLATB = 0x15

class SignalLogic(object):
    def __init__(self, logic_array):
        pass

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

# Helper functions for defining logic.  These return lambdas that
# can correctly calculate the output value based on current configuration.
def OR(term_a, term_b=None, term_c=None, term_d=None, term_e=None):
    def or_body(logic):
        values = []
        values.append(logic.expression_value(term_a))
        if term_b is not None:
            values.append(logic.expression_value(term_b))
        if term_c is not None:
            values.append(logic.expression_value(term_c))
        if term_d is not None:
            values.append(logic.expression_value(term_d))
        if term_e is not None:
            values.append(logic.expression_value(term_e))
        return any(values)
    return or_body

def AND(term_a, term_b, term_c=None, term_d=None, term_e=None):
    def and_body(logic):
        values = []
        values.append(logic.expression_value(term_a))
        values.append(logic.expression_value(term_b))
        if term_c is not None:
            values.append(logic.expression_value(term_c))
        if term_d is not None:
            values.append(logic.expression_value(term_d))
        if term_e is not None:
            values.append(logic.expression_value(term_e))
        return all(values)
    return and_body

def NOT(term_a):
    def not_body(logic):
        return not(logic.expression_value(term_a))
    return not_body
