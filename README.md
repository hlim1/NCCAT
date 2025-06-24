# NCCAT: Node Combination and Classification for AST Transformation

## Requirements:
- Latest Version of Python 3 (> 3.8)
    - `$sudo apt install python3.8`
- Latest Version of pip3
    - `$sudo apt install python3-pip`
- pycparser
    - Follow the instructions at https://github.com/eliben/pycparser.
    - All the rights of pycparser belongs to the developers of the software.

## Building NCCAT
If the above requirements are met, no additional building is required.
NCCAT can be run just like any other Python program.

## How to Run the Tool
- Prepare a directory, e.g., `test_root/`, where all the intermediate/result files will be stored.
  - Locate the original PoC code in the directory. 
  - Copy `arguments.json` file (under the `NCCAT/` directory) to this directory.
  - For example,
      ```
        test_root/
        |__ poc.c
        |__ arguments.json
      ```

- Populate each fields in `arguments.json` file. Description below:
    ```
    {
        "root":"",                 # Root directory where poc.c and arguments.json are stored.
        "filename":"",             # Name of the seed file.
        "compiler-path":"",        # Path to compiler executable to test.
        "options":[],              # Optimization options.
        "opt-off":"-O0",           # Compiler option to disable optimizations (default: -O0).
        "linker":[]                # Add any linker to for compiled code to execute.
    }
    ```

- `cd` to the directory.
  
  `$cd test_root`

- Execute the command below:

  `$python3 <path>/<to>/C/Main.py__ -f arguments.json`

## Output
The witness test programs for bug localization can be found under `witnesses/` directory.
