"""This program is for collecting "any" necessary information of the abstract 
syntax trees of "all" JavaScript programs in the specified directory.

$

Author: Terrence J. Lim
"""

import os, sys
import json
import argparse
import subprocess

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.CAstMutator as Mutator
import C.pycparser.c_json as c_json

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-d",
            "--directory",
            type=str,
            required=True,
            help="Directory where all the C files are stored."
    )
    args = parser.parse_args()

    return args.directory

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

def open_text_file(file_path: str):
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

def collect_asts(dir_path: str):
    """This function generates and collects all asts of C programs."

    args:
        dir_path (str): path to directories.

    returns:
        None.
    """
    
    if not os.path.exists(f"{dir_path}/asts"):
        os.mkdir(f"{dir_path}/asts")

    files = os.listdir(dir_path)

    for file_name in files:
        file_path = f"{dir_path}/{file_name}"
        name = file_name.split(".")[0]

        if os.path.exists(f"{dir_path}/asts/{name}.json"):
            continue

        print (f"Constructing AST for: {file_path}...")
        
        try:
            ast_dict = c_json.file_to_dict(file_path)
            ast = c_json.from_dict(ast_dict)
            with open(f"{dir_path}/asts/{name}.json", "w") as f:
                json.dump(ast_dict, f, indent=4)
        except:
            print (f"PARSING ERROR: {file_name}")
            subprocess.run(["rm", file_path])

def node_types_identifier(directory_path: str, language_info: dict, shared_dict: dict):
    """This function loads all the C files in the Data/C directory,
    and collected all the encountered node types.

    args:
        directory_path (str): path to a directory where all C code are stored.
        language_info (dict): language information.
        shared_dict (dict): dictionary that holds shared information about the AST.

    returns:
        (set) set of encountered node types.
        (list) list of all asts
    """

    types = set()
    
    files = os.listdir(directory_path)

    for file_name in files:
        if not file_name.endswith(".c"):
            continue

        file_path = f"{directory_path}/{file_name}"

        print (f"Collecting types from {file_path}...")

        ast_dict = c_json.file_to_dict(file_path)
        id_to_type, _, _ = Mutator.tree_traverser(ast_dict)
        scanned_types = set()
        for node_id, node_type in id_to_type.items():
            scanned_types = scanned_types.union({node_type})
        types = types.union(scanned_types)

    return types

def update_types(types: set, root_path: str):
    """This function updates SharedDictionary.json file accordingly to the
    existing C code.

    args:
        types (set): set of all node types in the scanned abstract syntax trees.
        root_path (str): root directory path.

    returns:
        None.
    """

    dictionary = read_json_file(f"{root_path}/C/SharedDictionary.json")

    # Clear before update.
    dictionary["unhandled-types"] = []

    for node_type in types:
        if node_type not in dictionary["handled-types"]:
            dictionary["unhandled-types"].append(node_type)

    out = open(f"{root_path}/C/SharedDictionary.json", "w")
    json.dump(dictionary, out, indent=4)

def main():

    directory_path = argument_parser()

    collect_asts(directory_path)

    types = node_types_identifier(directory_path, {}, {})

    update_types(types, parentdir)

if __name__ == "__main__":
    main()
