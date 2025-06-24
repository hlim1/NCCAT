"""
    This program will work as an oracle of C codes, i.e., it will compile & run
    the C code with the target C compiler then return the execution
    result.

    Author: Terrence J. Lim
"""

import json
import os, sys
import subprocess
import argparse

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Reference: https://www.nsnam.org/wiki/HOWTO_understand_and_find_cause_of_exited_with_code_-11_errors
ERRORCODE = {
        "-1":"SIGHUP",
        "-2":"SIGINT",
        "-3":"SIGQUIT",
        "-4":"SIGILL",
        "-5":"SIGTRAP",
        "-6":"SIGABRT/SIGIOT",
        "-7":"SIGBUS",
        "-8":"SIGFPE",
        "-9":"SIGKILL",
        "-10":"SIGUSR1",
        "-11":"SIGSEGV",
        "-12":"SIGUSR2",
        "-13":"SIGPIPE",
        "-14":"SIGALRM",
        "-15":"SIGTERM",
}

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

def get_cl(arguments: dict, enable: bool, file_path: str, is_bugloc=False):
    """This function is for creating a command-line list to run the input test program.

    args:
        arguments (dict): arguments dictionary.
        enable (bool): a flag for enabling or disabling jit compilation.
        file_path (str): path to the target C file to compile.

    returns:
        (list) constructed command-line.
    """

    if not is_bugloc:
        compiler = arguments["compiler-path"]
    else:
        compiler = arguments["compiler-gcov-path"]

    assert os.path.exists(compiler), f"ERROR: {compiler} is not valid."

    cl = [compiler]

    if arguments["linker"]:
        cl.extend(arguments["linker"])

    if enable:
        options = arguments["options"]
        cl.extend(options)
        cl.extend([file_path, "-o", "./enabled"])
    else:
        opt_off = arguments["opt-off"]
        cl.append(opt_off)
        cl.extend([file_path, "-o", "./disabled"])

    return cl

def is_diff(enabled_out, disabled_out):
    """This function checks if the two outputs are different or not.
    
    args:
        enabled_out (subprocess.CompletedProcess):
        disabled_out (subprocess.CompletedProcess):

    returns:
        (bool) true if the two outputs are different. Otherwise, false.
    """

    if (
            enabled_out.stdout == disabled_out.stdout and
            enabled_out.returncode == disabled_out.returncode
    ):
        # print ("enabled_out: ", enabled_out)
        # print ("disabled_out: ", disabled_out)
        return False

    return True

def run_binary(command: list):
    """This function runs the binary file using the pre-poluated command list.

    args:
        command (list): list of commands.

    returns:
        (out) subprocess's out object or None.
    """

    try:
        out = subprocess.run(command, capture_output=True, text=True, timeout=3)
        return out
    except subprocess.TimeoutExpired:
        print (f"   Timed out...")

    return None
    
def is_pass(arguments: dict, file_path: str):
    """This function checks if the code is a fail or pass with the
     user-specified compiler.

    args:
        arguments (dict): arguments dictionary.
        file_path (str): path to a code file to test.

    retunrs:
        (bool) true if it is a pass. Otherwise, false.
        (bool) true if the code was compiled and executed. Otherwise, false.
    """
    
    assert os.path.exists(file_path), f"ERROR: {file_path} does not exist."

    print (f"TESTING: {file_path}...")

    # First we compile the code with optimization disabled.
    disabled_cl = get_cl(arguments, False, file_path)

    disabled_compile = subprocess.run(disabled_cl, capture_output=True, text=True)

    if os.path.exists(file_path) and not os.path.exists("./disabled"):
        return False, False

    disabled_out = run_binary(["./disabled"])

    # os.remove("./disabled")

    # Then, we compile the code with optimization enabled.
    enabled_cl = get_cl(arguments, True, file_path)
    
    enabled_compile = subprocess.run(enabled_cl, capture_output=True, text=True)

    enabled_out = run_binary(["./enabled"])

    # os.remove("./enabled")
    
    # TODO: This may not work with certain bugs. Identify the specific bug, learn the behavior,
    # then fix this code accordingly.
    if disabled_out == None or enabled_out == None:
        return False, False

    return not is_diff(enabled_out, disabled_out), True

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-a",
            "--arguments",
            type=str,
            required=True,
            help="Requires the argument json file."
    )
    parser.add_argument(
            "-f",
            "--file",
            type=str,
            required=True,
            help="Requires C file to process."
    )
    args = parser.parse_args()

    return args.arguments, args.file

def main():
    arguments_path, file_path = argument_parser()
    
    arguments = read_json_file(arguments_path)

    stat, executed = is_pass(arguments, file_path)

    print (f"{file_path}:     {stat}, {executed}")

if __name__ == "__main__":
    main()
