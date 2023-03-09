# manjuu

Manjuu is a python preprocessor module library for Verilog. It allows python code to be inserted and evaluated as preprocessor code inside Verilog module, for generating ports, wires, etc. Note Manjuu is not an HDL.

It's currently used in several of my projects such as RISu*64 RISC-V processors and the Servaru GPU. It's still under active development.

## License

Unless otherwise specified, the source code is licensed under MIT.

The PyHP code preprocessor (pyhp.py) is licensed under GPLv2. The code processor is provided in the repo for convenience, but shouldn't be considered as part of the project (It's not dynamically or statically linked into other part of the program, rather functions as a text processor to consume other files.)
