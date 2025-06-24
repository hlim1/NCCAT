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

## Copyright

Copyright (2025) HeuiChan Lim

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
