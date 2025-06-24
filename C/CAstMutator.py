"""
    This program mutates abstract syntax tree of given C code.

    Author: Terrence J. Lim
"""

import os, sys
import json
import copy

from multiprocessing import Pool

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.ConstantMutator as ConstantMutator
import C.OperatorMutator as OperatorMutator
import C.OtherMutator as OtherMutator

def tree_traverser(ast: dict):
    """This function calls a helper function traverser() to traverse
    the abstract-syntax tree (AST).

    args:
        ast (dict): abstract syntax tree.

    returns:
        (dict) node id to node type dictionary.
        (dict) traversed abstract syntax tree.
        (int) number of nodes in the traversed ast.
    """

    id_to_type = {}
    node_id = [0]
    goto_labels = set()

    traverser(ast, id_to_type, node_id, goto_labels)

    ast["processed"] = True

    return id_to_type, ast, node_id[0]+1, goto_labels

def traverser(node: dict, id_to_type: dict, node_id: list, goto_labels: set):
    """This function recursively traverses each node the syntax tree
    and does the following operations:
        (1) collects encountered node types in a set,
        (2) assigns id to each node,
        (3) collect labels where goto can jump to.

    args:
        node (dict): current node.
        id_to_type (dict): node id to type dictionary.
        node_id (list): data structure to track node id.
        goto_labels (set): set of goto labels.

    returns:
        None.
    """

    if isinstance(node, dict):
        node["nodeid"] = node_id[0]
        id_to_type[node["nodeid"]] = node["_nodetype"]
        node_id[0] += 1

        node["is_mutable"] = True
        node["is_mutated"] = False

        if node["_nodetype"] == "Label":
            goto_labels.add(node["name"])

        for key, value in node.items():
            if key != "nodeid":
                traverser(value, id_to_type, node_id, goto_labels)
    elif isinstance(node, list):
        for item in node:
            traverser(item, id_to_type, node_id, goto_labels)

def clean_ast(node: dict):
    """This function removes all the key-item added post ast construction
    using pycparser as they are not recognized by pycparser and lead to
    error during code generation.

    args:
        node (dict): current node.

    returns:
        None.
    """

    if isinstance(node, dict):
        if "processed" in node:
            del node["processed"]
        if "nodeid" in node:
            del node["nodeid"]
        if "is_mutated" in node:
            del node["is_mutated"]
        if "is_mutable" in node:
            del node["is_mutable"]

        for key, value in node.items():
            clean_ast(value)
    elif isinstance(node, list):
        for item in node:
            clean_ast(item)

def mark(
        node: dict, parent: dict, mutable_node_ids: set, language_info: dict, builtins: set, 
        shared_dict: dict, is_loop: dict, is_print: list, goto_labels: set):
    """This function checks the node type and other details to determine whether the node should be
    marked as mutable or not.

    args:
        node (dict): abstract syntax tree node.
        parent (dict): parent node of the current node.
        mutable_node_ids (set): set of mutable node ids.
        language_info (dict): C language information.
        builtins (set): set of built-in functions/methods of JavaScript language
        shared_dict (dict): dictionary that holds shared information about the AST.
        goto_labels (set): set of label names where goto can jump to.

    returns:
        None.
    """

    
    op_names = ["UnaryOp", "BinaryOp", "Assignment"]

    operators = []
    for key, value in language_info["operators"].items():
        operators = operators + value

    if node["_nodetype"] not in shared_dict["handled-types"]:
        node["is_mutable"] = False
        if node["_nodetype"] == "For" and node["next"] != None:
            node["next"]["is_mutable"] = False
    elif node["_nodetype"] in shared_dict["handled-types"]:
        if node["_nodetype"] == "Decl" and len(node["quals"]) < 1:
            node["is_mutable"] = False
        elif node["_nodetype"] == "Typename" and len(node["quals"]) < 1:
            node["is_mutable"] = False
        elif node["_nodetype"] == "IdentifierType" and len(node["names"]) < 2:
            node["is_mutable"] = False
        elif node["_nodetype"] == "Goto" and len(goto_labels) < 2:
            node["is_mutable"] = False
        elif node["_nodetype"] in op_names and node["op"] not in operators:
            node["is_mutable"] = False
        elif is_loop["is_loop_enter"] and is_loop["is_loop_next"]:
            node["is_mutable"] = False
        elif is_print[0]:
            node["is_mutable"] = False
        elif parent["_nodetype"] == "Return" and node["_nodetype"] == "Constant":
            node["is_mutable"] = False
        elif node["_nodetype"] == "ID" and node["name"] not in builtins:
            node["is_mutable"] = False
        elif node["_nodetype"] == "Assignment" and node["op"] == "=":
            node["is_mutable"] = False
        elif node["is_mutable"]:
            mutable_node_ids.add(node["nodeid"])
            
def mark_mutable_nodes(
        node: dict, parent: dict, mutable_node_ids: set, language_info: dict, builtins: set, 
        shared_dict: dict, is_loop: dict, is_print: list, goto_labels: set):
    """This function trecursively traversed each node in the pre-processed syntax tree
    and update mutability of nodes appropriately.

    args:
        node (dict): abstract syntax tree node.
        parent (dict): parent node of the current node.
        mutable_node_ids (set): set of mutable node ids.
        language_info (dict): C language information.
        builtins (set): set of built-in functions/methods of JavaScript language
        shared_dict (dict): dictionary that holds shared information about the AST.
        goto_labels (set): set of label names where goto can jump to.

    returns:
        None.
    """

    if isinstance(node, dict):
        mark(node, parent, mutable_node_ids, language_info, builtins, shared_dict, is_loop, is_print, goto_labels)

        parent = node
        for key, value in node.items():
            if node["_nodetype"] == "For":
                is_loop["is_loop_enter"] = True
            if is_loop["is_loop_enter"] and key == "next":
                is_loop["is_loop_next"] = True
            if node["_nodetype"] == "FuncCall" and node["name"]["name"] == "printf":
                is_print[0] = True

            mark_mutable_nodes(value, parent, mutable_node_ids, language_info, builtins, shared_dict, is_loop, is_print, goto_labels)

            if node["_nodetype"] == "For":
                is_loop["is_loop_enter"] = False
            if is_loop["is_loop_enter"] and key == "next":
                is_loop["is_loop_next"] = False
            if node["_nodetype"] == "FuncCall" and node["name"]["name"] == "printf":
                is_print[0] = False
    elif isinstance(node, list):
        for item in node:
            mark_mutable_nodes(item, parent, mutable_node_ids, language_info, builtins, shared_dict, is_loop, is_print, goto_labels)

    return

def map_id_to_node(node: dict, id_to_node: dict):
    """This function maps node id-to-object.

    args:
        node (dict): abstract syntax tree node.
        id_to_node (dict): node id-to-object dictionary.

    returns:
        None.
    """

    # check if the current node is a dictionary and has the 'type' key.
    if isinstance(node, dict) and "_nodetype" in node:

        id_to_node[node["nodeid"]] = node

        # recursively traverse each key-value in the dictionary.
        for key, value in node.items():
            map_id_to_node(value, id_to_node)
    elif isinstance(node, list):
        # if the node is a list, apply traversal to each element.
        for item in node:
            map_id_to_node(item, id_to_node)
 
def get_node(node: dict, node_id: list):
    """This function recursively traverses the ast until it finds the node with the target
    node id.

    args:
        node (dict): abstract syntax tree node.
        node_id (int): target node id.

    returns:
        None.
    """

    if isinstance(node, dict):
        if node["nodeid"] == node_id:
            return node

        for key, value in node.items():
            ret = get_node(value, node_id)
            if ret:
                return ret
    elif isinstance(node, list):
        for item in node:
            ret = get_node(item, node_id)
            if ret:
                return ret

    return None

def get_builtins(language_info: dict):
    """This function collects the builtin method names into a single set.

    args:
        language_info (dict): language information.

    returns:
        (set) set of builtin mathod names.
    """

    builtins = set()

    for method_type, methods in language_info["methods"].items():
        # Update the builtins set with methods list
        builtins.update(methods)

    return builtins

def is_for_loop(node: dict):
    """This function determines if a given node represents a for loop.

    args:
        node (dict)
    """

    assert type(node) == dict, f"ERROR: node type must be a dict: {node}"

    # Check for common structure of a for loop
    if 'init' in node and 'cond' in node and 'next' in node and 'stmt' in node:
        return True

    return False

def select_mutator(
        node: dict, parent: dict, language_info: dict, shared_dict: dict, 
        value: int, goto_labels: set, avoid_values: set):
    """This function calls appropriate mutator function to mutate the node.

    args:
        node (dict): target node to mutate.
        parent (dict): parent of the current node.
        language_info (dict): c language information.
        shared_dict (dict): dictionary that holds shared information about the AST.
        value (depends): if exist, it's a value to mutate the node's value.
        goto_labels (set): set of label names where goto can jump to.

    returns:
        None.
    """
    
    assert (
        '_nodetype' in node
    ), f"ERROR: '_nodetype' does not exist in the AST node: {node[key]}"

    _nodetype = node['_nodetype']

    operator_types = ["UnaryOp", "BinaryOp", "Assignment"]

    if _nodetype == "Constant":
        avoid_values.add(int(node["value"]))
        ConstantMutator.constant_mutator(node, parent, avoid_values, value)
    elif _nodetype in operator_types:
        OperatorMutator.operator_mutator(node, language_info)
    elif _nodetype in shared_dict["handled-types"]:
        OtherMutator.other_mutators(node, parent, language_info, goto_labels)
    else:
        pass

    return

def node_mutator(
        node: dict, parent: dict, language_info: dict, target_ids: set, shared_dict: dict, 
        goto_labels: set
):
    """This function recursively traverses each node in the syntax tree
    and does following two operations:
        (1) seeks for the node with the target node id.
        (2) mutates the found target node id.

    args:
        nodes (dict): a node in the abstract syntax tree.
        parent (dict): parent node of the current node.
        language_info (dict): c language information.
        target_id (list): target node id to mutate.
        shared_dict (dict): dictionary that holds shared information about the AST.
        goto_labels (set): set of label names where goto can jump to.

    returns:
        (bool) false if the node was mutated; true, otherwise.
    """

    # Check if the current node is a dictionary and has the 'type' key
    if isinstance(node, dict) and "_nodetype" in node:
        assert "is_mutable" in node, f"ERROR: is_mutable not in {node}"
        if (
                node["nodeid"] in target_ids and 
                node["_nodetype"] in shared_dict["handled-types"] and 
                node["is_mutable"]
        ):
            node_copy = copy.deepcopy(node)
            # Pass an empty set.
            avoid_values = set()
            select_mutator(node, parent, language_info, shared_dict, None, goto_labels, avoid_values)
            if node == node_copy:
                return False
        parent = node
        # Recursively traverse each key-value in the dictionary
        for key, value in node.items():
            _ = node_mutator(value, parent, language_info, target_ids, shared_dict, goto_labels)
    elif isinstance(node, list):
        # If the node is a list, apply traversal to each element
        for item in node:
            _ = node_mutator(item, parent, language_info, target_ids, shared_dict, goto_labels)

    return True

def ast_mutator(ast: dict, language_info: dict, target_ids: set, shared_dict: dict, goto_labels: set):
    """This function is the main function to mutate the passed AST.
    The passed AST must be the processed AST returned from the tree_traverser() function.

    args:
        ast (dict): processed abstract syntax tree.
        language_info (dict): c language information.
        target_id (list): target node id to mutate.
        shared_dict (dict): dictionary that holds shared information about the AST.
        goto_labels (set): set of label names where goto can jump to.

    return:
        (dict): mutated abstract syntax tree.
        (bool): boolean to indicate whether the ast was completed in mutation or not.
    """

    assert (
        "processed" in ast and ast["processed"]
    ), f"ERROR: Unprocessed abstract syntax tree was passed."

    is_mutated = node_mutator(ast, ast, language_info, target_ids, shared_dict, goto_labels)
    
    return ast, is_mutated
