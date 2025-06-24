"""
    This is the main program of NCCAT.
    
    How to run NCCAT?
    $python3 path/to/C/Main.py -f arguments.json

    Author: Terrence J. Lim
"""


import os, sys
import json
import math
import copy
import argparse
import subprocess
import time
import shutil

from multiprocessing import Pool

information = ""

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from pycparser import c_generator

import C.pycparser.c_json as c_json
import C.CAstMutator as CMutator
import C.CInitGenerator as CInit
import C.SharedEditor as Shared
import C.CLearning_A as Learning_A
import C.CLearning_B as Learning_B
import C.CDirectedGenerator as CDirected

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-f",
            "--file",
            type=str,
            required=True,
            help="C file to generate variants from."
    )
    args = parser.parse_args()

    return args.file

def read_json_file(file_path: str):
    """This function loads json file data into a python dictionary.

    args:
        file_path (str): path to json file to load.

    return:
        (dict) loaded dictionary.
    """

    data = {}
    with open(file_path) as f:
        data = json.load(f)

    return data

def read_text_file(file_path: str):
    """This function reads file as text and store the data as string.

    args:
        file_path: path to text file.

    returns:
        (string) read text.
    """

    data = ""
    with open(file_path) as f:
        data = f.read()

    return data

def combinations_worker(task_params: list):
    """This function generates all subsets of combination_size.

    args:
        task_params (list): stores the parameter of each task.

    returns:
        (set) combinations of size of combination_size.
    """

    mutable_node_ids, combination_size = task_params

    return [set(combination) for combination in itertools.combinations(mutable_node_ids, combination_size)]

def generate_all_combinations(mutable_node_ids: set):
    """This function generates all possible combinations of mutable node ids
    using parallel processing. Union of nCr, where n = |mutable_node_ids| and r = 1..n.

    args:
        mutable_node_ids (set): set of mutable node ids.

    returns:
        (list) list of all combinations.
    """

    with Pool() as pool:
        # Create a list of arguments (mutable_node_ids, combination_size) for the worker function
        task_params = [(mutable_node_ids, combination_size) for combination_size in range(len(mutable_node_ids) + 1)]
        # Apply the worker function to each value in the range from 0 to len(s) inclusive
        result = pool.map(combinations_worker, task_params)

    # Flatten the list of lists into a single list of subsets
    all_combinations = [subset for sublist in result for subset in sublist]

    return all_combinations[1:]

def preprocess_c_ast(file_path: str, language_info: dict, shared_dict: dict):
    """This function preprocess the ast from the original PoC code.

    args:
        file_path (str): path to the C code file.
        language_info (dict): C language information.
        shared_dict (dict): dictionary with data shared across the phases.

    returns:
        (dict) ast.
        (set) set of mutable node ids.
        (dict) node id to node type dictionary.
        (set) set of label names where goto can jump to.
    """

    ast_0 = c_json.file_to_dict(file_path)

    id_to_type, ast_0, ast_size, goto_labels = CMutator.tree_traverser(ast_0)

    builtins = CMutator.get_builtins(language_info)
    
    mutable_node_ids = set()
    is_loop = {
            "is_loop_enter":False,
            "is_loop_next":False
    }
    is_print = [False]
    CMutator.mark_mutable_nodes(
            ast_0, ast_0, mutable_node_ids, language_info, builtins, 
            shared_dict, is_loop, is_print, goto_labels)

    mutable_node_ids = sorted(mutable_node_ids)

    print (f"Mutable node ids: {mutable_node_ids} ({len(mutable_node_ids)})")

    # CAN BE REMOVED. THIS IS ONLY FOR COLLECTING INFORMATION.
    global information
    information += f"Size of ast: {ast_size}\n"
    information += f"Mutable node ids: {mutable_node_ids}\n"
    information += f"Mutable node size: {len(mutable_node_ids)}\n"

    return ast_0, mutable_node_ids, id_to_type, goto_labels

def collect_code_files(poc_path: str, code_path: str):
    """This function collects all code file information.

    args:
        code_path (str): root code directory path.

    returns:
        None.
    """

    assert os.path.exists(code_path), f"ERROR: {code_path} does not exist"

    subdirs = os.listdir(code_path)

    # Copy the original proof-of-concept code to the code directory.
    new_path = f"{code_path}/fail_r0__0.c"
    shutil.copy(poc_path, new_path)

    grouped_info_main = {
            "sizes": {
                "passings":0,
                "failings":1
            },
            "passings": [],
            "failings": ["fail_r0__0.c"]
    }

    for subdir_name in subdirs:
        assert os.path.isdir(f"{code_path}/{subdir_name}"), f"ERROR: {code_path}/{subdir_name} is not a directory."
        files = os.listdir(f"{code_path}/{subdir_name}")

        grouped_file = f"{code_path}/{subdir_name}/grouped_files.json"
        assert os.path.exists(grouped_file), f"ERROR: {grouped_file} does not exist."
        group_info = Shared.load_json(grouped_file)
        assert "passings" in group_info and "failings" in group_info, f"ERROR: {group_info} not valid."
        
        for file_name in files:
            if not file_name.endswith(".c"):
                continue

            file_id = int(file_name.split("__")[1].split(".")[0])

            prefix = ""
            if file_id in group_info["passings"]:
                prefix = "pass"
            elif file_id in group_info["failings"]:
                prefix = "fail"
            elif file_id in group_info["invalids"]:
                continue
            else:
                assert False, f"ERROR: {file_id} is not in passings, failings, and invalids group."
            
            # r: r from nCr.
            new_path = f"{code_path}/{subdir_name}/{prefix}_r{subdir_name}__{file_id}.c"
            
            # Move the file.
            os.rename(f"{code_path}/{subdir_name}/{file_name}", new_path)

            if prefix == "pass":
                grouped_info_main["passings"].append(f"{prefix}_r{subdir_name}__{file_id}.c")
            else:
                grouped_info_main["failings"].append(f"{prefix}_r{subdir_name}__{file_id}.c")

    grouped_info_main["sizes"]["passings"] = len(grouped_info_main["passings"])
    grouped_info_main["sizes"]["failings"] = len(grouped_info_main["failings"])

    with open(f"{code_path}/grouped_files.json", "w") as f:
        json.dump(grouped_info_main, f, indent=4)

def move_files_with_extension(source_dir, target_dir, extension):
    """
    Moves all files ending with `extension` from `source_dir` (and its subdirectories)
    to `target_dir`.

    args:
        source_dir: Path to the source directory.
        target_dir: Path to the target directory.
        extension: File extension to match (e.g., '.txt').
    """
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    file_id = 1
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith(extension):
                source_path = os.path.join(root, filename)
                new_filename = "code" + "__" + str(file_id) + ".c"
                destination_path = os.path.join(target_dir, new_filename)

                # Move the file to the target directory
                print(f"Moving: {source_path} -> {destination_path}")
                shutil.copy2(source_path, destination_path)
                file_id += 1

def nccat(arguments: dict):
    """This function is called from the main function of the tool to mutate & create
    new code from the original input poc code.

    args:
        arguments (dict): arguments dictionary.

    returns:
        None.
    """

    checkpoint_1_start_time = time.perf_counter()

    root = arguments["root"]
    poc_name = arguments["filename"]
    asts_path = f"{root}/phase_1/asts"
    code_path = f"{root}/phase_1/code"

    file_path = f"{root}/{poc_name}"

    assert os.path.exists(code_path), f"ERROR: {file_path} not exists"

    language_info = read_json_file(f"{currentdir}/CLanguage.json")
    shared_dict = read_json_file(f"{currentdir}/SharedDictionary.json")

    (
        ast_0,
        mutable_node_ids,
        id_to_type,
        goto_labels
    ) = preprocess_c_ast(file_path, language_info, shared_dict)
    
    Shared.text_writer(
            f"Mutable Node Ids: {str(mutable_node_ids)}\n",
            f"{root}/phase_2a/mutable_node_ids.out")
    Shared.ast_writer(ast_0, f"{root}/phase_2a/ast__0.json")
    Shared.json_writer(id_to_type, f"{root}/phase_2a/id_to_type.json")
    
    print ("Phase-1: Initial Test Programs Generation")
    CInit.test_generator(
            ast_0, language_info, mutable_node_ids, shared_dict, 
            asts_path, code_path, arguments, goto_labels, [])

    collect_code_files(f"{root}/{poc_name}", code_path)

    print ("Phase-2A: Learning A")
    (
         identified_node_ids,
         pc2ap,
         fc2ap
    ) = Learning_A.learning(
            arguments, code_path, asts_path, set(mutable_node_ids), id_to_type, goto_labels)

    # CAN BE REMOVED. THIS IS ONLY FOR COLLECTING INFORMATION.
    global information
    merged_list = [item for subset in identified_node_ids for item in subset]
    information += f"identified_node_ids: {merged_list}\n"
    information += f"identified_node_ids size: {len(merged_list)}\n"
    Shared.text_writer(information, f"{root}/information.txt")

    code_path2 = f"{root}/phase_2b/code"
    asts_path2 = f"{root}/phase_2b/asts"
    
    print ("Phase-2B: Learning B")
    (
         ids_set_to_nodes,
         ids_set_to_mutations
    ) = Learning_B.learning(
             arguments, code_path2, asts_path2, identified_node_ids, id_to_type, ast_0,
             pc2ap, fc2ap, language_info, shared_dict, goto_labels)

    checkpoint_1_end_time = time.perf_counter()
    elapsed_seconds = checkpoint_1_end_time - checkpoint_1_start_time
    elapsed_minutes = elapsed_seconds / 60
    elapsed_time = f"Checkpoint-1: {elapsed_minutes:.2f}\n" 
    checkpoint_2_start_time = time.perf_counter()

    Shared.json_writer(ids_set_to_nodes, f"{root}/phase_2b/ids_set_to_nodes.json")
    Shared.json_writer(ids_set_to_mutations, f"{root}/phase_2b/ids_set_to_mutations.json")

    code_path3 = f"{root}/phase_3/code"
    asts_path3 = f"{root}/phase_3/asts"

    print ("Phase-3: Witness Test Program Generation")
    CDirected.directed_generator(
                arguments, code_path3, asts_path3, ast_0, goto_labels, language_info,
                shared_dict, ids_set_to_mutations, mutable_node_ids, root)

    witness_path = f"{root}/witnesses"

    if not os.path.exists(witness_path):
        os.mkdir (witness_path)
    if not os.path.exists(f"{witness_path}/invalids"):
        os.mkdir (f"{witness_path}/invalids")

    move_files_with_extension(code_path3, witness_path, ".c")

    grouped_files = Shared.group_all_programs(arguments, witness_path)
    
    for file_id in grouped_files["invalids"]:
        shutil.move(f"{witness_path}/code__{file_id}.c", f"{witness_path}/invalids")

    shutil.copy2(file_path, f"{witness_path}/code__0.c")

    checkpoint_2_end_time = time.perf_counter()
    elapsed_seconds = checkpoint_2_end_time - checkpoint_2_start_time
    elapsed_minutes = elapsed_seconds / 60
    elapsed_time += f"Checkpoint-1: {elapsed_minutes:.2f}\n" 

    Shared.text_writer(elapsed_time, f"{arguments['root']}/elapsed_time.out", "w")

    return

def create_dirs(root: str):
    """This function creates necessary directories for the tool to execute
    and store the outputs.

    args:
        root (str): path to the bug directory root.

    returns:
        None.
    """

    assert os.path.exists(root), f"ERROR: bug directory does not exist"
    
    # Directories for Phase 1.
    if not os.path.exists(f"{root}/phase_1"):
        os.mkdir(f"{root}/phase_1")
    if not os.path.exists(f"{root}/phase_1/asts"):
        os.mkdir(f"{root}/phase_1/asts")
    if not os.path.exists(f"{root}/phase_1/code"):
        os.mkdir(f"{root}/phase_1/code")
    if not os.path.exists(f"{root}/phase_1/illegal"):
        os.mkdir(f"{root}/phase_1/illegal")

    # Directories for Phase 2a.
    if not os.path.exists(f"{root}/phase_2a"):
        os.mkdir(f"{root}/phase_2a")
    if not os.path.exists(f"{root}/phase_2a/asts"):
        os.mkdir(f"{root}/phase_2a/asts")
    if not os.path.exists(f"{root}/phase_2a/code"):
        os.mkdir(f"{root}/phase_2a/code")
    if not os.path.exists(f"{root}/phase_2a/illegal"):
        os.mkdir(f"{root}/phase_2a/illegal")

    # Directories for Phase 2b.
    if not os.path.exists(f"{root}/phase_2b"):
        os.mkdir(f"{root}/phase_2b")
    if not os.path.exists(f"{root}/phase_2b/asts"):
        os.mkdir(f"{root}/phase_2b/asts")
    if not os.path.exists(f"{root}/phase_2b/code"):
        os.mkdir(f"{root}/phase_2b/code")
    if not os.path.exists(f"{root}/phase_2b/illegal"):
        os.mkdir(f"{root}/phase_2b/illegal")

    # Directories for Phase 3.
    if not os.path.exists(f"{root}/phase_3"):
        os.mkdir(f"{root}/phase_3")
    if not os.path.exists(f"{root}/phase_3/asts"):
        os.mkdir(f"{root}/phase_3/asts")
    if not os.path.exists(f"{root}/phase_3/code"):
        os.mkdir(f"{root}/phase_3/code")
    if not os.path.exists(f"{root}/phase_3/illegal"):
        os.mkdir(f"{root}/phase_3/illegal")


def main():
    
    file_path = argument_parser()

    arguments = read_json_file(file_path)

    create_dirs(arguments["root"])

    start_time = time.perf_counter()
    
    nccat(arguments)
    
    end_time = time.perf_counter()
    elapsed_seconds = end_time - start_time
    elapsed_minutes = elapsed_seconds / 60
    Shared.text_writer(f"Elapsed time: {elapsed_minutes:.2f} minutes\n", f"{arguments['root']}/elapsed_time.out", "a")

    return

if __name__ == "__main__":
    main()
