#!/usr/bin/env python
#
# Helper functions for defining signal logic terms.
# These return callables that calculate output values based on the
# current logic state and configuration.


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
