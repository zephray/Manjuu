#
# Manjuu
# Copyright 2023 Wenting Zhang
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import math
import copy
import builtins

defines = {}

def reverse(type):
    reversed = copy.deepcopy(type)
    for entry in reversed:
        if entry[0] == "i":
            entry[0] = "o"
        elif entry[0] == "o":
            entry[0] = "i"
        # Don't touch io
    return reversed

def handshake(type):
    result = copy.deepcopy(type)
    result.append(["i", "valid"])
    result.append(["o", "ready"])
    return result

def prefix(prefix, type):
    result = copy.deepcopy(type)
    for entry in result:
        entry[1] = prefix + "_" + entry[1]
    return result

def _get_width(entry):
    if len(entry) == 3:
        return entry[2]
    else:
        return 1

def _get_pin(entry):
    if len(entry) == 3:
        direction, name, size = entry
        width = f" [{size-1}:0] "
    else:
        direction, name = entry
        width = " "
    return direction, width, name

def gen_port(prefix, type, reg=True, last_comma=True, count=1):
    for i in range(count):
        postfix = "" if count == 1 else str(i)
        out = "" # Save into string so last comma could be easily stripped
        dir_map = {
            "i": "input",
            "o": "output",
            "io": "inout"
        }
        for entry in type:
            direction, width, name = _get_pin(entry)
            if reg and direction == "o":
                vartype = " reg"
            else:
                vartype = " wire"
            out += dir_map[direction] + vartype + width + prefix + "_" + name + postfix + ",\n"
        if i == count - 1:
            if not last_comma:
                out = out[:-2]
            else:
                out = out[:-1] # Remove trailing new line
        print(out, end="")

def gen_wire(prefix, type, count=1):
    for i in range(count):
        postfix = "" if count == 1 else str(i)
        for entry in type:
            _, width, name = _get_pin(entry)
            print("wire" + width + prefix + "_" + name + postfix + ";")

def gen_reg(prefix, type, count=1):
    for i in range(count):
        postfix = "" if count == 1 else str(i)
        for entry in type:
            _, width, name = _get_pin(entry)
            print("reg" + width + prefix + "_" + name + postfix + ";")

def gen_connect(port_prefix, type, wire_prefix="", last_comma=True, count=1):
    if wire_prefix == "":
        wire_prefix = port_prefix
    for i in range(count):
        postfix = "" if count == 1 else str(i)
        out = ""
        for entry in type:
            _, width, name = _get_pin(entry)
            out += "." + port_prefix + "_" + name + postfix + "(" + wire_prefix + "_" + name + postfix + "),\n"
        if i == count - 1:
            if not last_comma:
                out = out[:-2]
            else:
                out = out[:-1] # Remove trailing new line
        print(out, end="")
    
def gen_capture(dst_prefix, type, src_prefix="", count=1):
    if src_prefix == "":
        src_prefix = dst_prefix
    for i in range(count):
        postfix = "" if count == 1 else str(i)
        for entry in type:
            _, width, name = _get_pin(entry)
            print(dst_prefix + "_" + name + postfix + " <= " + src_prefix + "_" + name + postfix + ";")

def gen_cat(type, prefix):
    out = "{"
    for entry in type:
        _, _, name = _get_pin(entry)
        out += prefix + "_" + name + ","
    out = out[:-1] + "}"
    print(out, end="")

def count_bits(type):
    bits = 0
    for entry in type:
        if len(entry) == 3:
            _, _, size = entry
        else:
            size = 1
        bits += size
    print(bits, end="")

def parse_value(value):
    number = ""
    if value[0] == "'": # number without bitwidth
        number = value[1:]
    elif value[0].isdigit(): # number with bitwidth or without format
        br = value.find("'")
        if br == -1: # Without format
            number = value
        else:
            number = value[br+1:]
    else: # treat as a string literal
        return value
    if number[0] == "d":
        return int(number[1:])
    elif number[0] == "h":
        return int(number[1:], 16)
    elif number[0] == "b":
        return int(number[1:], 2)
    else:
        return int(number)

def define(name, value):
    builtins.__dict__[name] = parse_value(value)
    defines[name] = value

def gen_defines():
    for key, value in defines.items():
        print("`define", key, value)
