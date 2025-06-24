"""
    This program analyzes generated codes with their asts to identify the ast nodes
    that are directly related to a bug in the compiler.

    Phase-2: Generated code analysis phase.

    Author: Terrence J. Lim
"""



import os, sys
import subprocess
import copy

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.SharedEditor as Shared
import C.CInitGenerator as CInit

def learning(
        arguments: dict, code_path: str, asts_path: str, mutable_node_ids: set, id_to_type: dict, 
        goto_labels: set):
    """This function calls other functions to identify the important ast nodes.
    Important nodes meaning that mutating the identified nodes will alter the execution
    behavior of a compiler resulting to a flipped ouput, i.e. fail to pass and vice versa.

    args:
        arguments (dict): command-line arguments.
        code_path (str): path to the code directory where sub-directories with code files are stored.
        asts_path (str): path to the asts directory where sub-directories with ast files are stored.
        mutable_node_ids (set): set of all the nodes that are target for the mutation.
        id_to_type (dict): node id to type dictionary.
        goto_labels (set): set of goto labels.

    return:
        (set) set of identified ast node ids.
    """

    # pc2ap: passing_combination_to_ast_path
    # fc2ap: failing_combination_to_ast_path
    (
        passings, failings,
        pc2ap, fc2ap
    ) = collect_combinations(code_path, asts_path)

    r1_combinations = get_r1(passings)

    passing_combinations, for_retries = identify_from_larger_r(passings, r1_combinations)

    failing_nodes = get_always_existing_nodes(failings, mutable_node_ids)

    identified_nodes = join_lists_of_sets(passing_combinations, failing_nodes)

    new_mutable_node_ids = refine_retries(for_retries, identified_nodes, id_to_type)

    if new_mutable_node_ids:
        identified_nodes, re_pc2ap, re_fc2ap = retry(arguments, new_mutable_node_ids, identified_nodes, goto_labels)

        pc2ap = merge_dictionaries(pc2ap, re_pc2ap)
        fc2ap = merge_dictionaries(fc2ap, re_fc2ap)

    print (f"LEARNING: List of identified node id combinations: {identified_nodes}")

    return identified_nodes, pc2ap, fc2ap

def collect_combinations(code_path: str, asts_path: str):
    """This function collects all the combinations of mutated node ids from passings and failings groups.


    args:
        code_path (str): path to the code directory where sub-directories with code files are stored.
        asts_path (str): path to the asts directory where sub-directories with ast files are stored.

    return:
        (list) list of passing combination sets.
        (list) list of failing combination sets.
    """

    asts_subdirs = os.listdir(asts_path)
    code_subdirs = os.listdir(code_path)

    passing_combination_to_ast_path = {}
    failing_combination_to_ast_path = {}

    passings = []
    failings = []

    for asts_subdir in asts_subdirs:
        code_subdir = f"{code_path}/{asts_subdir}"
        assert os.path.exists(code_subdir), f"ERROR: {code_subdir} does not exist."
        group_info = Shared.load_json(f"{code_subdir}/grouped_files.json")
        assert "passings" in group_info and "failings" in group_info, f"ERROR: {group_info} not valid."

        ast_id_to_combination = Shared.load_json(f"{asts_path}/{asts_subdir}/id_to_combination.json")

        for ast_id, combination in ast_id_to_combination.items():
            if int(ast_id) in group_info["passings"] and set(combination) not in passings:
                passings.append(set(combination))
                passing_combination_to_ast_path[str(sorted(combination))] = [f"{asts_path}/{asts_subdir}/{ast_id}"]
            elif int(ast_id) in group_info["failings"] and set(combination) not in failings: 
                failings.append(set(combination))
                failing_combination_to_ast_path[str(sorted(combination))] = [f"{asts_path}/{asts_subdir}/{ast_id}"]

    return passings, failings, passing_combination_to_ast_path, failing_combination_to_ast_path

def get_r1(all_combinations: list):
    """This function retrieves sets of nodes, where |set| = 1 (i.e., r = 1 in nCr).

    args:
        all_combinations (list): list of combination sets.

    returns:
        (list) sets of combinations, where |set| = 1.
    """

    r1_combinations = []

    for combination in all_combinations:
        if len(combination) == 1:
            r1_combinations.append(combination)

    return r1_combinations

def identify_from_larger_r(all_combinations: list, r1_combinations: list):
    """This function retrieves combination of nodes, where r > 1. However, every node in 
    the combination must not be identified as passing (or failing) previously.
    For example, given the following,

    r1_combinations = {{2}, {3}, {4}}
    all_combinations = {..., {3, 7}, ..., {5, 8},...}

    {3, 7} has 3 in the set, so we do not collect the combination.
    On the other hand, neither node in {5, 8} identified earlier, so we collect it.

    args:
        all_combinations (list): list of combination sets.
        r1_combinations (list): list of combination sets, where every |set| = 1.

    returns:
        (list) sets of combinations.
        (list) sets of combinations for retry.
    """
    
    finite_union = get_finite_union(r1_combinations)

    combinations = r1_combinations

    for_retries = []

    for combination in all_combinations:
        if len(set(combination).intersection(finite_union)) == 0:
            if set(combination) in combinations:
                continue
            combinations.append(set(combination))
            finite_union = finite_union.union(set(combination))
        else:
            # What are retries? Retries are that nodes that we are yet to confirm
            # whether mutating them could lead to a flipping output or not. For
            # example, given the combination {3, 7} that flipped the output from fail to pass, 
            # where we know that mutating node 3 can flip the output while while 7 is unsure.
            # Thus, we do not know yet whether {3, 7} flipped the output because of node 3
            # or flipping 7 could also flip the output, but the initial random generation
            # produced false negative on mutating only node 7. Therefore, we collect node 7
            # to re-attempt on mutating and generating once more.
            for_retry = set(combination).difference(finite_union)
            if for_retry and for_retry not in for_retries:
                for_retries.append(for_retry)

    return combinations, for_retries

def get_always_existing_nodes(all_combinations: list, mutable_node_ids: set):
    """This function finds all the node (ids) that existed in one side (i.e., failing
    or passing) of the combinations.

    args:
        all_combinations (list): list of all combinations.
        mutable_node_ids (set): set of all mutable node ids.

    returns:
        (list) list of node id sets.
    """

    node_ids = set()

    for combination in all_combinations:
        if len(node_ids) == 0:
            node_ids = mutable_node_ids.difference(combination)
        else:
            node_ids = node_ids.difference(combination)

    list_of_sets = []
    for elem in node_ids:
        list_of_sets.append({elem})

    return list_of_sets

def join_lists_of_sets(l1: list, l2: list):
    """This function joins two lists, which elements are sets, into a single list.
    It removes any duplicates meaning that the data structure the function returns
    is really a set of sets.

    args:
        l1 (list): first list of sets.
        l2 (list): second list of sets.

    returns:
        (list) joined list of sets
    """

    identified_nodes = l1

    for elem in l2:
        if type(elem) != set:
            elem = {elem}

        if elem not in identified_nodes:
            identified_nodes.append(elem)

    return identified_nodes

def refine_retries(for_retries: list, identified_nodes: list, id_to_type: dict):
    """This function refines the list of nodes in the for_retries list.
    This can reduce the nodes mutate and eliminate the redundancies in testing nodes
    those were already identified as nodes that will flip the result from earlier
    analysis.

    args:
        for_retries (list): sets of combinations for retry.
        identified_nodes (list): joined list of combination sets known to flip the output.

    returns:
        (list) refined sets of retry nodes.
    """

    finite_union_1 = get_finite_union(for_retries)
    finite_union_2 = get_finite_union(identified_nodes)

    temp_1 = []
    for node_id in finite_union_1:
        if node_id not in finite_union_2 and node_id not in temp_1:
            temp_1.append(node_id)
    
    # TODO: Document the below code. Justify why this works.
    # Idea is from the boundary testing.
    temp_2 = []
    for node_id in temp_1:
        temp_2 = temp_2 + [node_id] * 12

    new_mutable_node_ids = []
    for node_id in temp_2:
        new_mutable_node_ids.append({node_id})

    return new_mutable_node_ids

def retry(arguments: dict, mutable_node_ids: list, identified_nodes: list, goto_labels: set):
    """This function generates another set of programs with given target mutable node ids.

    args:
        arguments (dict): arguments dictionary.
        mutable_node_ids (set): set of mutable node ids.
        identified_nodes (list): list of identified node ids.
        goto_labels (set): set of goto labels.

    returns:
        None.
    """
    
    root = arguments["root"]
    poc_name = arguments["filename"]
    asts_path = f"{root}/phase_2a/asts"
    code_path = f"{root}/phase_2a/code"

    language_info = Shared.load_json(f"{currentdir}/CLanguage.json")
    shared_dict = Shared.load_json(f"{currentdir}/SharedDictionary.json")
    ast_0 = Shared.load_json(f"{root}/phase_2a/ast__0.json")
    
    CInit.test_generator(ast_0, language_info, [1], shared_dict, asts_path, code_path, arguments, goto_labels, mutable_node_ids)

    identified_nodes, re_pc2ap, re_fc2ap = check_nodes(asts_path, code_path, mutable_node_ids, identified_nodes)

    return identified_nodes, re_pc2ap, re_fc2ap

def check_nodes(asts_path: str, code_path: str, mutable_node_ids: list, identified_nodes: list):
    """This function checks all the nodes mutated during the retry to further identify any of the nodes
    were able to flip the execution result of the compiled program.

    args:
        code_path (str): path to the code directory where sub-directories with code files are stored.
        asts_path (str): path to the asts directory where sub-directories with ast files are stored.
        mutable_node_ids (set): set of all the nodes that are target for the mutation.
        identified_nodes (list): list of node combinations.

    returns:
        (list) list of updated, if any, nodes combination sets
    """

    mutable_node_ids = get_finite_union(mutable_node_ids)

    (
        passings, failings,
        passing_combination_to_ast_path,
        failing_combination_to_ast_path
    ) = collect_combinations(code_path, asts_path)

    passing_ids = get_finite_union(passings)

    for node_id in mutable_node_ids:
        if node_id in passing_ids and {node_id} not in identified_nodes:
            identified_nodes.append({node_id})

    return identified_nodes, passing_combination_to_ast_path, failing_combination_to_ast_path

def get_finite_union(sets_list: list):
    """This function constructs finite union from finite number sets in the list.

    args:
        sets_list (list): list of sets.

    returns:
        (set) finite union set.
    """

    finite_union = set()
    for s in sets_list:
        finite_union = finite_union.union(s)

    return finite_union

def merge_dictionaries(dict_1: dict, dict_2: dict):
    """This function merges dict_2 to dict_1.

    args:
        dict_1 (dict): the base dictionary.
        dict_2 (dict)2: the dictionary to be merged to the base dictionary.

    returns:
        (dict) merged dictionary.
    """

    for combination, path in dict_2.items():
        if combination not in dict_1:
            dict_1[combination] = path

    return dict_1
