"""
    This program generates code using the information collected and analyzed
    during the learning phase.

    Phase-3: Directed code generation phase.

    Author: Terrence J. Lim
"""

import copy
import os, sys
import random
import ast
import shutil

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.CAstMutator as CMutator
import C.SharedEditor as Shared
import C.CInitGenerator as CInit

def directed_generator(
        arguments: dict, code_path: str, asts_path: str, ast_0: dict, goto_labels: set,
        language_info: dict, shared_dict: dict, ids_set_to_mutations: dict, mutable_node_ids: set,
        root: str):
    """This function mutates and generate c code from the input original poc code ast using
    the collected information during the learning phase.

    args:
        arguments (dict): command-line arguments.
        code_path (str): path to directory where created code files should be stored.
        asts_path (str): path to directory where created ast files should be stored.
        ast_0 (dict): abstract syntax tree of the original input poc.
        goto_labels (set): set of label names where goto can jump to.
        language_info (dict): language information.
        shared_dict (dict): dictionary that holds shared information about the AST.
        ids_set_to_mutations (dict): node id to mutation information.

    returns:

    """
    
    target_ids_sets = get_target_ids(ids_set_to_mutations)

    witness_node_ids = flatten(target_ids_sets)
    node_ids_to_avoid = set(mutable_node_ids) - witness_node_ids

    passing_asts_path = f"{asts_path}/passings"
    passing_code_path = f"{code_path}/passings"
    
    os.mkdir(passing_asts_path)
    os.mkdir(passing_code_path)

    print ("Generating Passing Witness Programs")

    CInit.test_generator(
            ast_0, language_info, witness_node_ids, shared_dict, passing_asts_path, 
            passing_code_path, arguments, goto_labels, [])

    failing_asts_path = f"{asts_path}/failings"
    failing_code_path = f"{code_path}/failings"

    os.mkdir(failing_asts_path)
    os.mkdir(failing_code_path)

    print ("Generating Failing Witness Programs")

    CInit.test_generator(
            ast_0, language_info, node_ids_to_avoid, shared_dict, failing_asts_path,
            failing_code_path, arguments, goto_labels, [])

    return

def flatten(data: list):
    """This function flattens list of lists into a single set.
    E.g., data = [[3], [4], [3, 5], [6]] into {3, 4, 5, 6}

    args:
        data (list): list of lists.

    returns:
        (set) set of elements.
    """

    result = {x for sublist in data for x in sublist}

    return result

def get_target_ids(ids_set_to_mutations: dict):
    """This function extracts node ids that will be target for either avoid or mutate
    during the directed ast mutation/generation.

    args:
        ids_set_to_mutations (dict): node id to mutation information.
    
    returns:
        (list) list of target node ids.
    """

    target_ids_sets = []

    for str_id_set in ids_set_to_mutations:
        mutation_info = ids_set_to_mutations[str_id_set]
        node_ids = list(mutation_info.keys())

        ids_list = ast.literal_eval(str_id_set)
        
        ids = []
        for node_id in node_ids:
            if len(mutation_info[node_id]["passings"]) > 0:
                ids.append(int(node_id))
        
        intersection = list(set(ids_list) & set(ids))
        
        if intersection:
            target_ids_sets.append(intersection)

    return target_ids_sets

def generate_buggy_witnesses():
    """
    """

    for target_ids in target_ids_sets:
        pass

    return

def node_mutator(
        node: dict, parent: dict, language_info: dict, shared_dict: dict, goto_labels: set,
        target_ids: list, ids_set_to_mutations: dict, is_for_buggy: bool):
    """
    """

    # Check if the current node is a dictionary and has the 'type' key
    if isinstance(node, dict) and "_nodetype" in node:
        assert "is_mutable" in node, f"ERROR: is_mutable not in {node}"
        if not is_for_buggy and node["nodeid"] in target_ids:
            node_copy = copy.deepcopy(node)
            # TODO

            if node == node_copy:
                return False
        elif is_for_buggy and node["nodeid"] not in target_ids:
            node_copy = copy.deepcopy(node)
            value = 0 # TODO
            avoid_values = {} # TODO
            CMutator.select_mutator(
                    node_copy, parent, language_info, shared_dict, value, goto_labels, avoid_values)

        parent = node
        # Recursively traverse each key-value in the dictionary
        for key, value in node.items():
            _ = node_mutator(value, parent, language_info, shared_dict, goto_labels, target_ids, is_for_buggy)
    elif isinstance(node, list):
        # If the node is a list, apply traversal to each element
        for item in node:
            _ = node_mutator(item, parent, language_info, shared_dict, goto_labels, target_ids, is_for_buggy)

    return True

def tree_mutator(
        ast: dict, parent: dict, language_info: dict, shared_dict: dict, goto_labels: set,
        target_ids: list, ids_set_to_mutations: dict, is_for_buggy: bool):
    """
    """

    is_mutated = node_mutator(ast, ast, language_info, target_ids, shared_dict, goto_labels, is_for_buggy)
    
    return ast, is_mutated
