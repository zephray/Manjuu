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

from manjuu_base import define

define("TL_OP_Get",             "3'd4")
define("TL_OP_PutFullData",     "3'd0")
define("TL_OP_PutPartialData",  "3'd1")
define("TL_OP_ArithmeticData",  "3'd2")
define("TL_OP_LogicalData",     "3'd3")
define("TL_OP_Intent",          "3'd5")

define("TL_OP_AccessAck",       "3'd0")
define("TL_OP_AccessAckData",   "3'd1")
define("TL_OP_HintAck",         "3'd2")

def tl_uh_t(addr = 32, data = 32, source = 1, sink = 1):
    return [
        ["i", "a_opcode", 3],
        ["i", "a_param", 3],
        ["i", "a_size", 3],
        ["i", "a_source", source],
        ["i", "a_address", addr],
        ["i", "a_mask", data // 8],
        ["i", "a_data", data],
        ["i", "a_corrupt"],
        ["i", "a_valid"],
        ["o", "a_ready"],
        ["o", "d_opcode", 3],
        ["o", "d_param", 2],
        ["o", "d_size", 3],
        ["o", "d_denied"],
        ["o", "d_data", data],
        ["o", "d_corrupt"],
        ["o", "d_valid"],
        ["i", "d_ready"]
    ]

def tl_ul_t(addr = 32, data = 32):
    return [
        ["i", "a_opcode", 3],
        ["i", "a_address", addr],
        ["i", "a_mask", data // 8],
        ["i", "a_data", data],
        ["i", "a_valid"],
        ["o", "a_ready"],
        ["o", "d_opcode", 3],
        ["o", "d_data", data],
        ["o", "d_valid"],
        ["i", "d_ready"]
    ]
