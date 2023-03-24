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

from manjuu_base import define, _get_width
import math

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

def tl_ul_csr_ep(csr_list, csr_prefix, tl_prefix):
    # RW registers should be "i", RO registers should be "o"
    signals = len(csr_list)
    signal_bits = math.ceil(math.log2(signals))
    if csr_prefix != "":
        csr_prefix = csr_prefix + "_"

    input_fifos = []
    output_fifos = []

    print(f"""    reg reg_stalled;

    reg [31:0] r_readout;
    reg [31:0] r_writeback;
    reg [31:0] r_bitmask;
    always @(*) begin
        case ({tl_prefix}_a_address[{signal_bits+1}:2])""")
    for i in range(signals):
        csr_name = f"{csr_prefix}{csr_list[i][1]}"
        if csr_name.endswith("ready") and csr_list[i][0] == "i":
            # Only needs to read input VALID, ready is write-only
            input_fifos.append(i)
            continue
        if csr_name.endswith("ready") and csr_list[i][0] == "o":
            # Only needs to read output VALID, ready is automatically controlled
            # If valid is cleared, it's ready to send additional data
            output_fifos.append(i)
            continue
        if (not csr_name.endswith("valid")) and csr_list[i][0] == "o":
            # Ignore write only
            continue
        if (_get_width(csr_list[i]) != 32):
            csr_name = f"{{{_get_width(csr_list[i])}'b0, {csr_name}}}"
        print(f"{signal_bits}'d{i}: r_readout = {csr_name};")
    print(f"""            default: r_readout = 32'bx;
        endcase
        r_bitmask = {{{{8{{{tl_prefix}_a_mask[3]}}}}, {{8{{{tl_prefix}_a_mask[2]}}}},
                {{8{{{tl_prefix}_a_mask[1]}}}}, {{8{{{tl_prefix}_a_mask[0]}}}}}};
        r_writeback = r_readout & r_bitmask | tl_a_data;
        tl_a_ready = reg_stalled;
    end

    always @(posedge clk) begin""")
    for i in input_fifos:
        csr_name = f"{csr_prefix}{csr_list[i][1][:-6]}"
        print(f"if ({csr_name}_valid && {csr_name}_ready) {csr_name}_ready <= 1'b0;");
    for i in output_fifos:
        csr_name = f"{csr_prefix}{csr_list[i][1][:-6]}"
        print(f"if ({csr_name}_valid && {csr_name}_ready) {csr_name}_valid <= 1'b0;");
    print(f"""        if (!reg_stalled) begin
            if (tl_a_valid && (tl_a_opcode == `TL_OP_Get)) begin
                tl_d_data <= r_readout;
                tl_d_opcode <= `TL_OP_AccessAckData;
            end
            else if (tl_a_valid && ((tl_a_opcode == `TL_OP_PutFullData) ||
                    (tl_a_opcode == `TL_OP_PutPartialData))) begin
                tl_d_opcode <= `TL_OP_AccessAck;
                case ({tl_prefix}_a_address[{signal_bits+1}:2])""")
    for i in range(signals):
        if (csr_list[i][0] == "o"):
            continue # Read only register, does not generate anything
        print(f"{signal_bits}'d{i}: {csr_prefix}{csr_list[i][1]} <= r_writeback[{_get_width(csr_list[i])-1}:0];")
    print("""                endcase
            end
            tl_d_valid <= tl_a_valid;
        end
        reg_stalled <= tl_d_valid && !tl_d_ready;
    end""")
        