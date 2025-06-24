"""
    This program analyzes generated codes with their asts to identify the ast nodes
    that are directly related to a bug in the compiler.

    Phase-2b: Second learning phase.

    Author: Terrence J. Lim
"""

import os, sys
import json
import copy
import subprocess

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from pycparser import c_generator
import C.pycparser.c_json as c_json
import C.CAstMutator as CMutator
import C.SharedEditor as Shared
import C.CLearning_A as Learning_A
import C.NodeAnalyzer as Analyzer

def learning(
        arguments: dict, code_path: str, asts_path: str, identified_node_ids: list, 
        id_to_type: dict, ast_0: dict, pc2ap: dict, fc2ap: dict, language_info: dict,
        shared_dict: dict, goto_labels: set):
    """This function calls other functions to identify the important ast nodes.
    Important nodes meaning that mutating the identified nodes will alter the execution
    behavior of a compiler resulting to a flipped ouput, i.e. fail to pass and vice versa.

    args:
        arguments (dict): command-line arguments.
        code_path (str): path to the code directory where sub-directories with code files are stored.
        asts_path (str): path to the asts directory where sub-directories with ast files are stored.
        identified_node_ids (list): list of identified ast node ids.
        id_to_type (dict): node id to type dictionary.
        ast_0 (dict): original poc's ast.
        pc2ap (dict): passing_combination_to_ast_path
        fc2ap (dict): failing_combination_to_ast_path
        language_info (dict): javascript language information.
        shared_dict (dict): dictionary that holds shared information about the AST.
        goto_labels (set): set of goto labels.

    return:
        (dict) node id to object.
        (dict) node id to mutation information.
    """
    
    # Temporary default n = 5.
    n = 5
 
    id_to_combination = generate_samples(
            ast_0, code_path, asts_path, identified_node_ids, n, language_info, shared_dict, goto_labels)

    # DEBUG
    id_to_combination = Shared.load_json(f"{asts_path}/id_to_combination.json")
    
    grouped_files = Shared.group_all_programs(arguments, code_path)

    update_Xc2aps(grouped_files, id_to_combination, asts_path, pc2ap, fc2ap)

    # DEBUG
    Shared.json_writer(pc2ap, "./pc2ap.json")
    Shared.json_writer(fc2ap, "./fc2ap.json")
    
    ids_set_to_nodes = get_mutated_nodes(identified_node_ids, pc2ap, fc2ap)

    ids_set_to_mutations = analyze_mutated_nodes(ast_0, ids_set_to_nodes)

    return ids_set_to_nodes, ids_set_to_mutations

def generate_samples(
        ast_0: dict, code_path: str, asts_path: str, identified_node_ids: list, n: int, 
        language_info: dict, shared_dict: dict, goto_labels: set):
    """This function generates additional n number of samples for each identified
    node id, i.e., ids of nodes known to alter the behavior of program when modified.

    args:
        ast_0 (dict): original poc's ast.
        code_path (str): path to the code directory where sub-directories with code files are stored.
        asts_path (str): path to the asts directory where sub-directories with ast files are stored.
        identified_node_ids (list): list of identified ast node ids.
        n (int): number of samples to generate for each node.
        language_info (dict): javascript language information.
        shared_dict (dict): dictionary that holds shared information about the AST.
        goto_labels (set): set of goto labels.

    returns:
        (dict) ast id-to-node id combinaition 
    """

    assert n > 0, f"ERROR: {n} <= 0. n must be > 0."

    id_to_combination = {}

    i = 0
    for nodes in identified_node_ids:
        assert nodes, f"ERROR: nodes is empty: {nodes}."
        j = 0
        while j < n:
            ast_copy = copy.deepcopy(ast_0)
            (
                mutated_ast,
                is_mutated 
            ) = CMutator.ast_mutator(ast_copy, language_info, nodes, shared_dict, goto_labels)
            if is_mutated:
                try:
                    # Write ast to disk.
                    Shared.ast_writer(mutated_ast, f"{asts_path}/ast__{i}.json")
                    # Write code to disk.
                    Shared.code_writer(f"{asts_path}/ast__{i}.json", f"{code_path}/code__{i}.c")

                    id_to_combination[str(i)] = list(nodes)

                    i += 1
                    j += 1
                except Exception as e:
                    print(f"ERROR (BUT CONTINUE): {e}")

    # Write generated asts' mutated summary to a json file.
    with open(f"{asts_path}/id_to_combination.json", "w") as f:
        json.dump(id_to_combination, f, indent=4)

    return id_to_combination

def get_nodes(Xc2ap: dict, str_ids_set: str, ids_set: set):
    """This function retrived all the target nodes.

    args:
        Xc2ap (dict): this either is pc2ap or fc2ap.
        str_ids_set (str): string casted ids_set.
        ids_set (set): set of node ids.

    returns:
        (list) list of found nodes.
    """
    
    nodes = []
    for path in Xc2ap[str_ids_set]:
        # Load the target ast and retrive the target node.
        dir_path = "/".join(path.split("/")[:-1])
        file_name = "ast__" + path.split("/")[-1] + ".json"
        path = dir_path + "/" + file_name

        ast = Shared.load_json(path)

        for node_id in ids_set:
            node = CMutator.get_node(ast, node_id)
            nodes.append(node)

    return nodes

def update_Xc2aps(grouped_files: dict, id_to_combination: dict, asts_path: str, pc2ap: dict, fc2ap: dict):
    """This function updates pc2ap and fc2ap dictionaries with the newly generated program information
    during phase 2b.

    args:
        grouped_files (dict): grouped ast/code files information (i.e., passings or failings).
        ids_to_combination (dict): ast id-to-node id combinaition
        asts_path (str): path to the asts directory where sub-directories with ast files are stored.
        pc2ap (dict): passing_combination_to_ast_path
        fc2ap (dict): failing_combination_to_ast_path

    return:
        None.
    """

    for stat, file_ids in grouped_files.items():
        for file_id in file_ids:
            # DEBUG
            file_id = str(file_id)

            assert file_id in id_to_combination, f"ERROR: {file_id} not in id_to_combination."
            combination = id_to_combination[file_id]

            path = f"{asts_path}/{file_id}"

            if stat == "passings":
                if str(combination) in pc2ap:
                    pc2ap[str(combination)].append(path)
                else:
                    pc2ap[str(combination)] = [path]
            else:
                if str(combination) in fc2ap:
                    fc2ap[str(combination)].append(path)
                else:
                    fc2ap[str(combination)] = [path]

def get_mutated_nodes(identified_node_ids: list, pc2ap: dict, fc2ap: dict):
    """This function analyzes the mutated ast nodes to identify what data value(s) flipped the
    execution behavior of the code.

    args:
        identified_node_ids (list): list of node ids known to be able to flip the execution
        behavior of code if mutated.
        pc2ap (dict): passing combination to ast path.
        fc2ap (dict): failing combination to ast path.

    returns:
        (dict) node ids to actual node objects information.
    """

    ids_set_to_nodes = {}

    for ids_set in identified_node_ids:
        str_ids_set = str(sorted(list(ids_set)))

        ids_set_to_nodes[str_ids_set] = {
                "set_in_list": list(ids_set),
                "passing_nodes": [],
                "failing_nodes": []
        }

        assert str_ids_set in pc2ap or str_ids_set in fc2ap, f"{ids_set} in neither pc2ap nor fc2ap."

        if str_ids_set in pc2ap:
            # Retrieve actual node from the ast.
            nodes = get_nodes(pc2ap, str_ids_set, ids_set)
            ids_set_to_nodes[str_ids_set]["passing_nodes"] = nodes

        if str_ids_set in fc2ap:
            nodes = get_nodes(fc2ap, str_ids_set, ids_set)
            ids_set_to_nodes[str_ids_set]["failing_nodes"] = nodes

    return ids_set_to_nodes

def select_analyzer(node: dict, ast_0_node: dict):
    """This function calls appropriate analyzer function analyze the mutated node
    with the original ast node.

    args:
        node (dict): node to analyze.
        ast_0_node (dict): original ast node.

    returns:

    """

    assert (
        '_nodetype' in node
    ), f"ERROR: '_nodetype' does not exist in the AST node: {node[key]}"

    _nodetype = node['_nodetype']

    operator_types = ["UnaryOp", "BinaryOp", "Assignment"]

    if _nodetype == "Constant":
        value, ast_0_node_value = Analyzer.constant_analyzer(node, ast_0_node)
        return str(value), str(ast_0_node_value)
    elif _nodetype in operator_types:
        op, ast_0_node_op = Analyzer.operator_analyzer(node, ast_0_node)
        return op, ast_0_node_op
    elif _nodetype == "IdentifierType":
        type_name, ast_0_node_name = Analyzer.identifier_type_analyzer(node, ast_0_node)
        return type_name, ast_0_node_name
    elif _nodetype == "Goto":
        goto_label, ast_0_node_label = Analyzer.goto_analyzer(node, ast_0_node)
        return goto_label, ast_0_node_label
    elif node["_nodetype"] == "Typename" or node["_nodetype"] == "Decl":
        quals, ast_0_node_quals = Analyzer.qualifier_analyzer(node, ast_0_node)
        return quals, ast_0_node_quals
    else:
        pass

    return None, None

def analyze_mutated_nodes(ast_0: dict, ids_set_to_nodes: dict):
    """This function analyzes the mutated ast nodes to identify what data value(s) flipped the
    execution behavior of the code.

    args:
        ast_0 (dict): original poc's ast.
        ids_set_to_nodes (dict): node ids to actual node objects information.

    returns:
        (dict)
    """

    ast_0_id_to_node = {} 
    CMutator.map_id_to_node(ast_0, ast_0_id_to_node)

    ids_set_to_mutations = {}

    for str_ids_set, mutation_info in ids_set_to_nodes.items():
        ids_set_to_mutations[str_ids_set] = {}

        for node in mutation_info["passing_nodes"]:
            node_id = node["nodeid"]
            try:
                ast_0_node = ast_0_id_to_node[node_id]
            except:
                Shared.json_writer(ast_0_id_to_node, "./debug_ast_0_id_to_node.json")
                assert node_id in ast_0_id_to_node, f"ERROR: {node_id} not in ast_0_id_to_node"

            if str(node_id) not in ids_set_to_mutations[str_ids_set]:
                ids_set_to_mutations[str_ids_set][str(node_id)] = {
                        "passings":[], 
                        "failings":[], 
                        "original": None
                }

            result, ast_0_node_info = select_analyzer(node, ast_0_node)
            
            if result and result not in ids_set_to_mutations[str_ids_set][str(node_id)]["passings"]:
                ids_set_to_mutations[str_ids_set][str(node_id)]["passings"].append(result)

            if ast_0_node_info and not ids_set_to_mutations[str_ids_set][str(node_id)]["original"]:
                ids_set_to_mutations[str_ids_set][str(node_id)]["original"] = ast_0_node_info

        for node in mutation_info["failing_nodes"]:
            node_id = node["nodeid"]
            ast_0_node = ast_0_id_to_node[node_id]

            if str(node_id) not in ids_set_to_mutations[str_ids_set]:
                ids_set_to_mutations[str_ids_set][str(node_id)] = {
                        "passings":[], 
                        "failings":[], 
                        "original": None
                }

            result, ast_0_node_info = select_analyzer(node, ast_0_node)
            
            if (
                    result and 
                    result not in ids_set_to_mutations[str_ids_set][str(node_id)]["failings"] and
                    result != "None"
            ):
                ids_set_to_mutations[str_ids_set][str(node_id)]["failings"].append(result)

            if ast_0_node_info and not ids_set_to_mutations[str_ids_set][str(node_id)]["original"]:
                ids_set_to_mutations[str_ids_set][str(node_id)]["original"] = ast_0_node_info

        assert (
                len(ids_set_to_mutations[str_ids_set]) == len(mutation_info["set_in_list"])
        ), f"ERROR: len(ids_set_to_mutations[str_ids_set]) != len(mutation_info['set_in_list'])"

    return ids_set_to_mutations
