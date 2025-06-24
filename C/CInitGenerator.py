"""
  This program generates a modified PoC that is one different from the original PoC.

  Phase-1: Initial random variant code generation phase.

  Author: Terrence J. Lim
"""

import json
import copy
import os, sys
import random

from multiprocessing import Pool

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.CAstMutator as CMutator
import C.SharedEditor as Shared

def test_generator(
        ast: dict, language_info: dict, mutable_node_ids: set, shared_dict: dict,
        asts_path: str, code_path: str, arguments: dict, goto_labels: list,
        combinations: set):
    """This function randomly mutates and generates c code from the input original poc code ast.

    args:
        ast (dict): abstract syntax tree.
        language_info (dict): language information.
        mutable_node_ids (set): set of mutable node ids.
        shared_dict (dict): dictionary that holds shared information about the AST.
        asts_path (str): path to directory where created ast files should be stored.
        code_path (str): path to directory where created code files should be stored.
        arguments (dict): command-line arguments.
        goto_labels (set): set of label names where goto can jump to.
        combinations (list): list of pre-populated, if any, node id combinations.

    returns:
        None.
    """
 
    combinations_size = len(combinations)

    i = 1
    for r in range(1, len(mutable_node_ids) + 1):

        if not os.path.exists(f"{code_path}/{r}") and not os.path.exists(f"{asts_path}/{r}"):
            if r > 1:
                # Check all the generated code in r-1 directory. 
                grouped_files = Shared.group_all_programs(arguments, f"{code_path}/{r-1}")
                # If no newly generated files are grouped as failing programs, it indicates that
                # all modifications flipped the failing beahviour to passing.
                if len(grouped_files["failings"]) == 0 and len(grouped_files["passings"]) > 0:
                    break
            os.mkdir(f"{asts_path}/{r}")
            os.mkdir(f"{code_path}/{r}")

        if combinations_size == 0:
            combinations = Shared.generate_combinations(mutable_node_ids, r)

        print (f"Handling r = {r}...{combinations}")

        test_generator_parallelized(
                ast, language_info, combinations, shared_dict, 
                f"{asts_path}/{r}", f"{code_path}/{r}", goto_labels)

        i = r

    if os.path.exists(f"{code_path}/{i}") and not os.path.exists(f"{code_path}/{i}/grouped_files.json"):
        grouped_files = Shared.group_all_programs(arguments, f"{code_path}/{i}")

def worker(args: list):
    """this function mutates ast and writes code to the designated path.

    args:
        args (list): list of arguments.

    returns:
        (int) ast id.
        (set) a combination set.
    """

    ast_id, combination, ast, language_info, shared_dict, asts_path, code_path, goto_labels = args

    # Copy the ast before passing to ast_mutator to prevent modifying the original.
    ast_copy = copy.deepcopy(ast)

    try:
        (
            mutated_ast, 
            is_mutated 
        ) = CMutator.ast_mutator(ast_copy, language_info, combination, shared_dict, goto_labels)

        if is_mutated:
            # Write ast to disk.
            ast_file_path = f"{asts_path}/ast__{ast_id}.json"
            Shared.ast_writer(mutated_ast, ast_file_path)

            # Write code to disk.
            code_file_path = f"{code_path}/code__{ast_id}.c"
            Shared.code_writer(ast_file_path, code_file_path)

            return ast_id, combination
    except Exception as e:
        print(f"ERROR (BUT CONTINUE): {e}")

    return None

def test_generator_parallelized(
        ast: dict, language_info: dict, all_combinations: list, shared_dict: dict,
        asts_path: str, code_path: str, goto_labels: set, num_processors=None):
    """This function randomly mutates and generates js code from the input original poc code ast.

    args:
        ast (dict): abstract syntax tree.
        language_info (dict): language information.
        shared_dict (dict): dictionary that holds shared information about the AST.
        all_combinations (list): list of all combinations.
        asts_path (str): path to directory where created ast files should be stored.
        code_path (str): path to directory where created code files should be stored.
        goto_labels (set): set of label names where goto can jump to.
        num_processors (int, optional): number of processors to use for parallel processing.

    returns:
        None.
    """

    tasks = [(i, combination, ast, language_info, shared_dict, asts_path, code_path, goto_labels)
             for i, combination in enumerate(all_combinations, start=1)]

    id_to_combination = {}

    with Pool(processes=num_processors) as pool:
        results = pool.map(worker, tasks)

    # Collect results and write summary
    for result in results:
        if result is not None:
            ast_id, combination = result
            id_to_combination[ast_id] = list(combination)

    # Write generated asts' mutated summary to a json file.
    with open(f"{asts_path}/id_to_combination.json", "w") as f:
        json.dump(id_to_combination, f, indent=4)

    print(f"CRANDOM: {len(results)} ast/code files generated out of {len(all_combinations)} possible combinations")


