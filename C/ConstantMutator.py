"""
    This file holds functions for mutating constant nodes.

    Author: Terrence J. Lim
"""

import random
import string

# ISO C standard (ISO/IEC 9899)
SCHAR_MAX = 127
UCHAR_MAX = 255
INT16_MAX = 32767
INT32_MAX = 2147483647
INT64_MAX = 9223372036854775807

# IEEE754 standard for double-precision floating-point numbers
FLOAT_MIN = 5e-324
FLOAT_MAX = 1.7976931348623157e+308

def integer_mutator(node: dict, value: int, avoid_values: set):
    """This function randomly mutates a node with integer value.

    args:
        node (dict): a node to mutate.
        value (int): if exist, it's a value to mutate the node's value.
        avoid_value (set): the values to avoid when selecting a new value.

    returns:
        None.
    """
    
    if not value:
        value = 0
        current_value = int(node["value"])

        value_choices = []

        # Decide the mutation range based on the current value
        if current_value < INT16_MAX + 1:
            value_choices = [0, 1, int(INT16_MAX/2), INT16_MAX-1, INT16_MAX, INT16_MAX+1]
        elif INT16_MAX < current_value <= INT32_MAX:
            value_choices = [INT16_MAX, INT16_MAX+1, int(INT32_MAX/2), INT32_MAX-1, INT32_MAX, INT32_MAX+1]
        elif INT32_MAX < current_value <= INT64_MAX:
            value_choices = [INT32_MAX, INT32_MAX+1, int(INT64_MAX/2), INT64_MAX-1, INT64_MAX, INT64_MAX+1]

        assert value_choices, f"ERROR: value_choices is empty."

        value = random.choice(value_choices)

        while value in avoid_values:
            value = random.choice(value_choices)

    node["value"] = str(value)

    node["is_mutated"] = True

def char_mutator(node: dict, value: int, avoid_values: set):
    """This function randomly mutates a node with char value.

    args:
        node (dict): a node to mutate.
        value (int): if exist, it's a value to mutate the node's value.
        avoid_value (set): the values to avoid when selecting a new value.

    returns:
        None.
    """

    if not value:
        value = 0
        current_value = int(node["value"])

        value_choices = []

        if current_value < SCHAR_MAX+1:
            value_choices = [0, 1, SCHAR_MAX/2, SCHAR_MAX-1, SCHAR_MAX, SCHAR_MAX+1]
        else:
            value_choices = [0, 1, UCHAR_MAX/2, UCHAR_MAX-1, UCHAR_MAX, UCHAR_MAX+1]

        assert value_choices, f"ERROR: value_choices is empty."

        value = random.choice(value_choices)

        while value in avoid_values:
            value = random.choice(value_choices)

    node["value"] = str(value)

    node["is_mutated"] = True

def float_mutator(node: dict, value: float, avoid_values: set):
    """This function randomly mutates a node with float value.

    args:
        node (dict): a node to mutate.
        value (float): if exist, it's a value to mutate the node's value.
        avoid_value (set): the values to avoid when selecting a new value.

    returns:
        None.
     """
    
    if not value:
        # Define the range for mutation
        value_choices = [0, FLOAT_MIN, 1.0, FLOAT_MAX/2, FLOAT_MAX-1.0, FLOAT_MAX]
        # float_max = node["value"] + 0.00001 * 2.0

        # Generate a random float within the specified range
        # new_value = random.uniform(0, float_max)
        value = random.choice(value_choices)

        while value in avoid_values:
            value = random.choice(value_choices)

    # Update the node with the new value
    node["value"] = str(value)

    node["is_mutated"] = True

def bool_mutator(node: dict, value: int):
    """This function randomly mutates a node with float value.

    args:
        node (dict): a node to mutate.
        value (int): if exist, it's a value to mutate the node's value.

    returns:
        None.
     """
    
    if not value:
        value = None

        current_value = int(node["value"])

        if current_value == 1:
            value = "0"
        else:
            value = "1"

    node["value"] = str(value)

    node["is_mutated"] = True

def constant_mutator(node: dict, parent: dict, avoid_values: set, value=None):
    """This function is the main function to mutate the constant node.

    args:
        nodes (dict): a node in the abstract syntax tree.
        parent (dict): parent of the current node.
        value (depends): if exist, it's a value to mutate the node's value.
        avoid_value (set): the values to avoid when selecting a new value.

    returns:
        None.
    """

    if '_nodetype' in parent and parent['_nodetype'] == 'Decl':
        valType = ' '.join(parent['type']['type']['names'])
    else:
        valType = node['type']

    integers = [
            "int", "unsigned int", "short", "short int", "unsigned short", 
            "unsigned short int", "long", "long int", "unsigned long", 
            "unsigned long int"
    ]

    chars = [
            "char", "unsigned char", "signed char"
    ]

    floats = [
            "float", "double", "long double"
    ]

    bools = ["_Bool"]
    
    if valType in integers:
        integer_mutator(node, value, avoid_values)
    elif valType in chars:
        char_mutator(node, value, avoid_values)
    elif valType in floats:
        float_mutator(node, value, avoid_values)
    elif valType in bools:
        # Bool type is a binary selection, so we do not need avoid_values.
        # If the current node's value is 1, then the avoid value is 0.
        bool_mutator(node, value)

    return
