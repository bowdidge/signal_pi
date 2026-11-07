#!/usr/bin/env python
#
# Helper functions for defining signal logic terms used in layout file.
# These return callables that calculate output values based on the
# current logic state and configuration.
#
# Robert Bowdidge, October 2026

# Each term is either the name of an input or output, or another
# callable returning a boolean.
#
# Terms are all evaluated even when the result is already known: reading an
# input has the side effect of recording its state for the status web page and
# for the LCD panel, so skipping reads would hide input changes.

def OR(*terms):
    """True if any term is true."""
    def or_body(logic):
        values = [logic.expression_value(term) for term in terms]
        return any(values)
    return or_body


def AND(*terms):
    """True if all terms are true."""
    def and_body(logic):
        values = [logic.expression_value(term) for term in terms]
        return all(values)
    return and_body


def NOT(term):
    """True if the term is false."""
    def not_body(logic):
        return not logic.expression_value(term)
    return not_body
