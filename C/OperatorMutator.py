"""
    This file holds functions for mutating operator nodes.

    Author: Terrence J. Lim
"""

import random
import string

def unary_mutator(node: dict, language_info: dict):
    """This function mutates unary operator nodes.

    args:
        node (dict): target node to mutate.
        language_info (dict): c language information.

    returns:
        None.
    """

    # We want to avoid mutating some unary operators, such
    # as the operators used for pointers and addresses.
    avoid = ["*", "&", "!"]

    operators = language_info['operators']

    node_op = node['op']

    if node_op in avoid:
        print (f"WARNING: Unary op is '{node_op}'...")
        return

    op = ""
    for k, values in operators.items():
        if node_op in values:
            op = random.choice(values)
            while op == node_op:
                op = random.choice(values)
            break
    
    if not op:
        print ("WARNING: Unary op is empty...")
    else:
        node['op'] = op
        node["is_mutated"] = True
    
    return

def binary_mutator(node: dict, language_info: dict):
    """This function mutates binary operator nodes.

    args:
        node (dict): target node to mutate.
        language_info (dict): c language information.

    returns:
        None.
    """

    operators = language_info['operators']

    node_op = node['op']

    op = None

    for key, value in operators.items():
        if key != "unary1" and node_op in value:
            op = random.choice(value)
            while op == node_op:
                op = random.choice(value)
            break
    
    if not op:
        print ("WARNING: Unary op is empty...")
    else:
        node['op'] = op
        node["is_mutated"] = True

def assignment_mutator(node: dict, language_info: dict):
    """This function mutates assignment operator nodes.

    args:
        node (dict): target node to mutate.
        language_info (dict): c language information.

    returns:
        None.
    """

    if node["op"] == "=":
        return
    else:
        assignments = language_info["operators"]["assignment"]

        op = random.choice(assignments)
        while op == node["op"]:
            op = random.choice(assignments)
        node["op"] = op
        node["is_mutated"] = True

def operator_mutator(node: dict, language_info: dict):
    """This function mutates binary, unary, and assignment operator nodes.

    args:
        node (dict): target node to mutate.
        language_info (dict): c language information.

    returns:
        None.
    """

    if node["_nodetype"] == "UnaryOp":
        unary_mutator(node, language_info)
    elif node["_nodetype"] == "BinaryOp":
        binary_mutator(node, language_info)
    elif node["_nodetype"] == "Assignment":
        assignment_mutator(node, language_info)

    return
