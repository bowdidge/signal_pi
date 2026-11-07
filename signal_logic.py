#!/usr/bin/python
#
# Machinery for implementing the signal controller - be able to process
# a description of the signal system, and handle resolving how inputs
# change output values.
#
# Robert Bowdidge, February 2024

import time

class NameMapper(object):
    """Wraps PortExpander so it can be manipulated by names.

    Multiple port expanders can be tested to find the correct
    one for a port name.
    """
    
    def __init__(self, port_expander, inputs, outputs):
        self.port_expander = port_expander
        self.outputs = list(outputs)

        # Map each input name to its (port index, inverted) pair.  Entries in
        # `inputs` are either plain names or dicts with a 'name' and an
        # optional 'inverted'.  Missing or empty names are skipped.
        self.inputs = {}
        for index, spec in enumerate(inputs):
            if isinstance(spec, dict):
                name = spec.get('name')
                inverted = spec.get('inverted', False)
            else:
                name = spec
                inverted = False
            if name:
                self.inputs[name] = (index, inverted)

    def is_input(self, name):
        """Returns true if an input with the name exists in the expander."""
        return name in self.inputs
    
    def test_input_or_output(self, name):
        """Returns the current state of the named input or output.

        If input is defined to be inverted, then return the inverse value
        of the output.
        """
        if name in self.inputs:
            index, inverted = self.inputs[name]
            value = bool(self.port_expander.get_input(index))
            return not value if inverted else value

        # No match?  check if there's an output with that name.
        if name in self.outputs:
            return self.port_expander.get_output_value(self.outputs.index(name))

        print('Unknown input %s in %s' % (name, self.inputs))
        return None

    def set_input(self, name, value):
        """Set a mock input value by name (for testing only).

        Applies the reversal so callers pass the logical value
        (True = occupied/thrown) rather than the raw hardware level.
        Returns True if the name was found, False otherwise.
        """
        if name not in self.inputs:
            return False
        index, inverted = self.inputs[name]
        self.port_expander.mock_set_input(index, (not value) if inverted else value)
        return True

    def set_output(self, name, value):
        # Unchanged values are filtered out by PortExpander.set_output.
        if name not in self.outputs:
            return None
        output_index = self.outputs.index(name)
        self.port_expander.set_output(output_index, value)
        
    
class Logic(object):
    """Handle signal logic via inputs and outputs in port expander boards."""
    
    def __init__(self, name_mappers, status_tracker=None):
        self.name_mappers = name_mappers
        self.status_tracker = status_tracker
        self.name_to_name_mapper = {}

        all_inputs = []
        all_outputs = []
        for name_mapper in self.name_mappers:
            for input_name in name_mapper.inputs:
                self.name_to_name_mapper[input_name] = name_mapper
                all_inputs.append(input_name)
            for output in name_mapper.outputs:
                if output:
                    self.name_to_name_mapper[output] = name_mapper
                    all_outputs.append(output)

        if self.status_tracker:
            self.status_tracker.initialize_names(all_inputs, all_outputs)

    def set_logic(self, logic_classes):
        self.logic_classes = logic_classes
        
    def logic_eval(self, output_name, predicate):
        """ Evaluate the predicate and change the correct output."""

        # Evaluate here.
        name_mapper = self.name_to_name_mapper[output_name]
        val = predicate(self)
        if self.status_tracker:
            self.status_tracker.record_change(output_name, val, is_input=False)
        name_mapper.set_output(output_name, val)

    def variable_value(self, input_name):
        try:
            name_mapper = self.name_to_name_mapper[input_name]
        except KeyError as e:
            print('Unknown key %s in %s' % (input_name, self.name_to_name_mapper))
            return None
        value = name_mapper.test_input_or_output(input_name)

        if name_mapper.is_input(input_name):
            if self.status_tracker:
                self.status_tracker.record_change(input_name, value, is_input=True)
        return value

    def expression_value(self, expression):
        if callable(expression):
            return expression(self)
        return self.variable_value(expression)
            
    def set_input(self, name, value):
        """Set a named input to a logical value (for testing).

        Looks up which NameMapper owns the input and delegates to it,
        handling any hardware-level reversal automatically.
        Raises KeyError if the name is not a registered input.
        """
        name_mapper = self.name_to_name_mapper.get(name)
        if name_mapper is None or not name_mapper.is_input(name):
            raise KeyError('Unknown input name: %s' % name)
        name_mapper.set_input(name, value)

    def poll(self):
        # Go through all logic terms and calculate the new value.
        # Undefined behavior if circular dependencies in outputs.
        for logic_term in self.logic_classes:
            output_name, predicate = logic_term
            self.logic_eval(output_name, predicate)


def build_engine(expanders_config, logic_clauses, port_expander_class,
                 status_tracker=None):
    """Instantiate PortExpanders, NameMappers, and wire them into a Logic engine.

    Args:
        expanders_config: List of expander definition dicts with address, inputs, outputs.
        logic_clauses: List of (output_name, predicate) logic tuples.
        port_expander_class: PortExpander class to instantiate (hardware or mock).
        status_tracker: Optional StatusTracker instance for tracking states and web updates.

    Returns:
        (logic_engine, expanders_list)
    """
    expanders = []
    name_mappers = []
    for exp_cfg in expanders_config:
        expander = port_expander_class(exp_cfg['address'])
        expander.setup()
        expanders.append(expander)
        name_mappers.append(
            NameMapper(expander, exp_cfg['inputs'], exp_cfg['outputs'])
        )

    logic_engine = Logic(name_mappers, status_tracker=status_tracker)
    logic_engine.set_logic(logic_clauses)
    return logic_engine, expanders

