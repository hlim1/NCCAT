"""
    This file holds functions for mutating nodes other than constant or operator nodes.

    Author: Terrence J. Lim
"""

import random
import string
import copy

def qualifier_mutator(node: dict, parent: dict, language_info: dict):
    """This function mutates nodes with the qualifiers.

    args:
        nodes (dict): a node in the abstract syntax tree.
        parent (dict): parent of the current node.
        language_info (dict): C language information.

    returns:
        None
    """

    qualifiers = language_info['qualifiers1']

    quals = node['quals']
    
    new_quals = []
    for qual in quals:
        new_qual = random.choice(qualifiers)
        while new_qual == qual:
            new_qual = random.choice(qualifiers)
        new_quals.append(new_qual)

    node['quals'] = copy.deepcopy(new_quals)
    node['type']['type']['quals'] = copy.deepcopy(new_quals)
    
    node["is_mutated"] = True

def identifier_type_mutator(node: dict, language_info: dict):
    """This function mutates nodes with IdentifierType node type.

    args:
        nodes (dict): a node in the abstract syntax tree.
        parent (dict): parent of the current node.
        language_info (dict): C language information.

    returns:
        None
    """

    assert "names" in node, f"ERROR: IdentifierType node must have 'names' element: {node}"

    names = node["names"]

    types = language_info["data-types"]
    
    select_from = []
    if names[0] in types["types2"]:
        select_from = types["types2"]
    elif names[0] in types["types3"]:
        select_from = types["types3"]
    
    if not select_from:
        return

    name = random.choice(select_from)
    while name == names[0]:
        name = random.choice(select_from)
    node["names"][0] = name

    node["is_mutated"] = True

def loop_cf_mutator(node: dict):
    """This function mutates nodes with Continue or Break node type.

    args:
        nodes (dict): a node in the abstract syntax tree.
        parent (dict): parent of the current node.
        language_info (dict): C language information.

    returns:
        None
    """

    _nodetype = node['_nodetype']

    assert (
        _nodetype == 'Continue' or _nodetype == 'Break'
    ), f"ERROR: _nodetype in modify_loop_cf is neither Continue nor Break: {current}."

    if _nodetype == 'Break':
        node['_nodetype'] = 'Continue'
    else:
        node['_nodetype'] = 'Break'

def goto_mutator(node: dict, goto_labels: set):
    """This function mutates nodes with Goto node type.

    args:
        nodes (dict): a node in the abstract syntax tree.
        parent (dict): parent of the current node.
        language_info (dict): C language information.

    returns:
        None
    """

    assert goto_labels, f"ERROR: goto_labels set cannot be empty."

    name = node["name"]
    
    new_label = random.choice(list(goto_labels))
    while name == new_label:
        new_label = random.choice(list(goto_labels))
    node["name"] = new_label

    node["is_mutated"]

def other_mutators(node: dict, parent: dict, language_info: dict, goto_labels: set):
    """This function mutates nodes with the node types other than constant and operator.

    args:
        nodes (dict): a node in the abstract syntax tree.
        parent (dict): parent of the current node.
        language_info (dict): C language information.
        goto_labels (set): set of label names where goto can jump to.

    returns:
        None
    """

    if node["_nodetype"] == "Typename" or node["_nodetype"] == "Decl":
         qualifier_mutator(node, parent, language_info)
    elif node["_nodetype"] == "IdentifierType":
        identifier_type_mutator(node, language_info)
    elif node["_nodetype"] == "Goto":
        goto_mutator(node, goto_labels)
