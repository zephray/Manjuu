# Manjū

Manjuu is a python preprocessor module library for verilog. It allows python code to be inserted and evaluated as preprocessor code inside verilog module, for generating ports, wires, etc. Note Manjuu is not an HDL: Compare to other python-based HDLs, Manjuu provides python inside verilog, not verilog-like functionalities inside python.

The project is inspired by similar usage in OpenPiton. It's currently used in several of my projects such as RISu*64 RISC-V processors and the Servaru GPU. It's still under active development.

## Introduction

The Manjuu allows embedding python code inside verilog code. For example:

```verilog
    reg [31:0] counter;
    always @(posedge clk) begin
        <% print("counter <= counter + 1;") %>
    end
```

Would be expanded to

```verilog
    reg [31:0] counter;
    always @(posedge clk) begin
        counter <= counter + 1;
    end
```

Obviously this is not very interesting or useful by its own. Usually, the Manjuu libraries are used together.

## Data structures

The library works with several custom data structures. Usually the user would define some project specific data structures along with using provided ones.

### Bundle

The bundle type is a bundle of a bunch of wires. It's similar to struct in SystemVerilog or bundle in Chisel. For example, to define a UART bundle:

```python
req_t = [
    ["i", "data", 8],
    ["i", "cmd", 4]
]
```

As you could see it's really just a python list with special meanings. The general structure is

```python
    [
        [direction, name, width], # Entry with explict width
        [direction, name], # Entry with width = 1
        ... # More entries
    ]
```

The direction is a string, can be `i`, `o`, or `io`. The width is the width of the signal in bits. For example `input [7:0] data` becomes `["i", "data", 8]`.

## Base library

The base libraries provides several useful functions for generating Verilog code.

### Bundle operation

There are 2 common bundle operations that allows modifying the bundle:

- Reverse: reverse the direction of all signals in a bundle
- Handshake: add ready valid handshaking signal to a bundle

Note the handshake always add the signal from the perspective of receiver: valid is an input and ready is a output.

### Port, wire, and connections

Manually defining ports and connecting them is often a very repetitive and error-prone work in verilog. Manjuu could generate these with one single definition of the bundle.

For example, the following code (assuming previous `uart_t` definition):

```verilog
module A(<% gen_port("in", handshake(req_t), last_comma = False) %>);
    <% gen_reg("cur", req_t) %>
    always @(posedge clk) begin
        if (in_valid) begin
            <% gen_capture("cur", req_t, "in") %>
        end
    end
    /* Module implementation */
endmodule

module B(<% gen_port("out", reverse(handshake(req_t)), last_comma = False) %>);
    /* Module implementation */
endmodule

module Top();
    <% gen_wire("b_a", handshake(req_t)) %>
    A a(<% gen_connect("in", req_t, "b_a") %>);
    B b(<% gen_connect("out", req_t, "b_a") %>);
endmodule
```

It gets expanded to:

```verilog
module A (
    input wire [7:0] in_data,
    input wire [3:0] in_cmd,
    input wire in_valid,
    output reg in_ready
);
    reg [7:0] cur_data;
    reg [3:0] cur_cmd;

    always @(posedge clk) begin
        if (in_valid) begin
            cur_data <= in_data;
            cur_cmd <= in_cmd;

        end
    end
    /* Module implementation */
endmodule

module B (
    output reg [7:0] out_data,
    output reg [3:0] out_cmd,
    output reg out_valid,
    input wire out_ready
);
    /* Module implementation */
endmodule

module Top ();
    wire [7:0] b_a_data;
    wire [3:0] b_a_cmd;
    wire b_a_valid;
    wire b_a_ready;

    A a (
        .in_data(b_a_data),
        .in_cmd(b_a_cmd),
    );
    B b (
        .out_data(b_a_data),
        .out_cmd(b_a_cmd),
    );
endmodule
```

### Defines

Sometimes there are some constants that's needed in both python code and verilog code, Manjuu provides a way to easily define them in both sides:

```python
define("CMD_INVALID", "3'd1")
define("DATA_WIDTH", "64")
```

Then by calling the function `gen_defines()` it gets expanded to:

```verilog
`define CMD_INVALID 3'd1
`define DATA_WIDTH 64
```

And they are available to use inside python code as well:

```python
port = [["i", "dat", DATA_WIDTH]]
```

## Why not xxx

There are tons of alternatives solutions that provides similar functionalities as the Manjuu, suiting different needs. Manjuu doesn't aim to replace any of these, and I won't say Manjuu is a good choice for everyone. Here is just a list of few differences comparing Manjuu to other alternatives:

- Gradual adoption: start using Manjuu doesn't require rewriting any of the existing codebase, not even individual modules
- Very little to learn: it doesn't introduce any extension to either Verilog or Python
- Clear sepearation between circuit and generator: It's always clear if the code is describing a circuit (verilog code) or generator (python code)
- It's dumb: it doesn't try to be smart to fill in any gaps, it only does what explicitly told to do, to avoid covering up bugs
- Clean and human-readable generated code: the output is clean, with no random-ish generated labels or any directives
- Pre-processing always gets run during build: avoid bugs caused by old dangling generated code

## License

Unless otherwise specified, the source code is licensed under MIT.

The PyHP code preprocessor (pyhp.py) is licensed under GPLv2. The code processor is provided in the repo for convenience, but shouldn't be considered as part of the project (It's not dynamically or statically linked into other part of the program, rather functions as a text processor to consume other files.)
