# Manjū

Manjuu is a python preprocessor module library for verilog. It allows python code to be inserted and evaluated as preprocessor code inside verilog module, for generating ports, wires, etc. Note Manjuu is not an HDL: Compare to other python-based HDLs, Manjuu provides python inside verilog, not verilog-like functionalities inside python.

The project is inspired by similar usage in OpenPiton. It's currently used in several of my projects such as RISu*64 RISC-V processors and the Servaru GPU. It's still under active development.

## Introduction

The basic idea is that the Manjuu allows embedding python code inside verilog code. For example:

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
- Prefix: add prefix to signal names

Note the handshake always add the signal from the perspective of receiver: valid is an input and ready is a output.

Prefix is typically only used in building nested bundles. 

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

### Data array

In parameterized designs, it's common for a module to have a configurable signal list. For example, a multi-ported RAM or a bus arbiter, would have parameterized port count. A straight-forward implementation would be to use an array in the module signal list:

```verilog
module dual_port_ram(
    input wire [63:0] wdata [0:1],
    output wire [63:0] rdata [0:1],
    input wire [4:0] addr [0:1],
    input wire wen [0:1]
);
```

However not all tools support such syntax. For example, Vivado doesn't support using array inside port signal list. A common workaround is to concat things into a wider signal:

```verilog
module dual_port_ram(
    input wire [127:0] wdata,
    output wire [127:0] rdata,
    input wire [9:0] addr,
    input wire [1:0] wen
);
```

Which is a bit confusing and not particularly easy to work with. Manjuu supports turning bundles into an array directly as a parameter inside previously mentioned functions. For example, the following is a dual-port RAM model:

```verilog
module dual_port_ram(
    input wire clk,
    <% gen_port("ram", ram_req_t, reg=False, count=NR_PORTS, last_comma=False) %>
);
    reg [63:0] ram [31:0];
    always @(posedge clk) begin
        <%
        for i in range(NR_PORTS):
            print(f"if (ram_wen{i}) begin")
            print(f"    ram[ram_addr{i}] <= ram_wdata{i};")
            print(f"end")
            print(f"ram_rdata{i} <= ram[ram_addr{i}];")
        %>
    end
endmodule
```

It gets expanded to:

```verilog
module dual_port_ram (
    input wire clk,
    input wire [63:0] ram_wdata0,
    output wire [63:0] ram_rdata0,
    input wire [4:0] ram_addr0,
    input wire ram_wen0,
    input wire [63:0] ram_wdata1,
    output wire [63:0] ram_rdata1,
    input wire [4:0] ram_addr1,
    input wire ram_wen1
);
    reg [63:0] ram[31:0];
    always @(posedge clk) begin
        if (ram_wen0) begin
            ram[ram_addr0] <= ram_wdata0;
        end
        ram_rdata0 <= ram[ram_addr0];
        if (ram_wen1) begin
            ram[ram_addr1] <= ram_wdata1;
        end
        ram_rdata1 <= ram[ram_addr1];

    end
endmodule
```

It gets a bit ugly, and connecting multiple ports could ended up being a daunting task. Luckily, generating and connecting wire for arrays can be done similarly as well:

```verilog
<% gen_wire("ram", ram_req_t, count=NR_PORTS) %>

dual_port_ram dual_port_ram(
    .clk(clk),
    <% gen_connect("ram", ram_req_t, count=NR_PORTS, last_comma=False) %>
);
```

It would then be expanded accordingly.

### Packing and unpacking

Verilog doesn't really offer much support for generics. While it may be possible to use the port list generation to create copies of the same module with different post signal type, it's a lot of duplicated code. In some cases, it is simply easier to pack stuff into a big bit vector and later unpack them.

For example, to buffer a RGB565 signal through a FIFO:

```python
rgb_t = [["o", "r", 5], ["o", "g", 6], ["o", "b", 5]]
```

```verilog
fifo #(.WIDTH(<% count_bits(rgb_t) %>)) rgb_fifo (
    .clk(clk),
    .a_data(<% gen_cat(rgb_t, "in") %>),
    .a_valid(in_valid),
    .a_ready(in_ready),
    .b_data(<% gen_cat(rgb_t, "out") %>),
    .b_valid(out_valid),
    .b_ready(out_ready)
);
```

It gets expanded to:

```
fifo #(
    .WIDTH(16)
) rgb_fifo (
    .clk(clk),
    .a_data({in_r, in_g, in_b}),
    .a_valid(in_valid),
    .a_ready(in_ready),
    .b_data({out_r, out_g, out_b}),
    .b_valid(out_valid),
    .b_ready(out_ready)
);
```

Note how `count_bits()` is used to determine the width of the resulting bit vector and sets the width of the fifo.

### Defines

Sometimes there are some constants that's needed in both python code and verilog code, Manjuu provides a way to easily define them in both sides:

```python
define("CMD_INVALID", "3'd1")
```

Or, if the number is only intended to be used in python environment, a simple assignment is good enough:

```python
DATA_WIDTH = 64
```

Then by calling the function `gen_defines()` it gets expanded to:

```verilog
`define CMD_INVALID 3'd1
```

And use the defined const (either by direct assignment or using the `define()` function):

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
- Easy to extend and modify: it's based on a very simple model so it's easy to pick up and add features as needed

## License

Unless otherwise specified, the source code is licensed under MIT.

The PyHP code preprocessor (pyhp.py) is licensed under GPLv2. The code processor is provided in the repo for convenience, but shouldn't be considered as part of the project (It's not dynamically or statically linked into other part of the program, rather functions as a text processor to consume other files.)
