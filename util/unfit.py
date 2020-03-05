import sys
import os.path
import re
import argparse

from . import database
from .jesd3 import JESD3Parser


def natural_sort_key(input):
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r'(\d+)', input)]


db = database.load()


def extract(fuses, field):
    value = sum(fuses[fuse] << n_fuse for n_fuse, fuse in enumerate(field['fuses']))
    for key, key_value in field['values'].items():
        if value == key_value:
            return key
    assert False, f"fuses {field['fuses']}: extracted {value}, known {field['values']}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--device', metavar='DEVICE', choices=db, default='ATF1502AS',
        help='device (one of: %(choices)s)')
    parser.add_argument(
        '-v', '--verbose', default=False, action='store_true',
        help='emit nets that have no effect (useful for equivalence checking)')
    parser.add_argument(
        'input', metavar='JED-FILE', type=argparse.FileType('r'),
        help='read JESD3-C fuses from JED-FILE')
    parser.add_argument(
        'output', metavar='VERILOG-FILE', type=argparse.FileType('w'), nargs='?',
        help='write behavioral Verilog to VERILOG-FILE')
    args = parser.parse_args()

    device = db[args.device]

    jed_parser = JESD3Parser(args.input.read())
    jed_parser.parse()
    fuses = jed_parser.fuse
    basename, _ = os.path.splitext(os.path.basename(args.input.name))

    output = args.output or sys.stdout
    output.write(f"// Decompiled from JED file {args.input.name}:\n")
    for comment_line in jed_parser.design_spec.splitlines():
        output.write(f"// {comment_line}\n")

    pads = set()
    for node_type in ('clocks', 'enables', 'macrocells'):
        for node_name, node in device[node_type].items():
            pads.add(f"PAD_{node['pad']}")
    pads = list(sorted(pads, key=natural_sort_key))

    output.write(f"module {basename}({', '.join(pads)});\n\n")
    output.write(f"    // Global inputs\n")
    # TOO: missing programmable inverters
    output.write(f"    assign GCLR = PAD_{device['clear']['pad']};\n")
    for gclk_name in ("1", "2", "3"):
        output.write(f"    assign GCLK{gclk_name} = PAD_{device['clocks'][gclk_name]['pad']};\n")
    output.write(f"\n")

    feedbacks = []
    for mc_name, macrocell in device['macrocells'].items():
        feedbacks.append(f"FB_{mc_name}")

    output.write(f"    // Macrocell feedbacks\n")
    output.write(f"    wire {', '.join(feedbacks)};\n")
    output.write(f"\n")

    output.write(f"    // Global OE muxes\n")
    for mux_name, mux in device['goe_muxes'].items():
        choice = extract(fuses, mux)
        if choice == 'GND':
            if args.verbose:
                output.write(f"    wire {mux_name} = 1'b0;\n")
        else:
            # TODO: figure out what is happening with PAD choices vs FB choices
            output.write(f"    wire {mux_name} = {choice};\n")
    output.write(f"\n")

    for mc_name, macrocell in device['macrocells'].items():
        output.write(f"    // Macrocell {mc_name}\n")
        output.write(f"    reg {mc_name}_Q = 1'b0;\n")
        sum_term = []
        sum_term.append(f"{mc_name}_PT1")
        pt2_mux = extract(fuses, macrocell['pt2_mux'])
        if pt2_mux == 'sum':
            sum_term.append(f"{mc_name}_PT2")
            xor_a_input = extract(fuses, macrocell['xor_a_input'])
            if xor_a_input == 'gnd':
                wire_xa = "1'b0"
            elif xor_a_input == 'vcc':
                wire_xa = "1'b1"
            elif xor_a_input == 'ff_q':
                wire_xa = f"{mc_name}_Q"
            elif xor_a_input == 'ff_qn':
                wire_xa = f"~{mc_name}_Q"
            else:
                assert False
        elif pt2_mux == 'xor':
            wire_xa = "{mc_name}_PT2"
            # TODO: xor_a_input bits mean something else here
        else:
            assert False
        pt3_mux = extract(fuses, macrocell['pt3_mux'])
        global_reset = extract(fuses, macrocell['global_reset'])
        if pt3_mux == 'sum':
            sum_term.append(f"{mc_name}_PT3")
            if global_reset == 'off':
                wire_ar = f"1'b0"
            elif global_reset == 'on':
                wire_ar = f"GCLR"
            else:
                assert False
        elif pt3_mux == 'ar':
            if global_reset == 'off':
                wire_ar = f"{mc_name}_PT3"
            elif global_reset == 'on':
                wire_ar = f"{mc_name}_PT3 | GCLR"
            else:
                assert False
        else:
            assert False
        pt4_mux = extract(fuses, macrocell['pt4_mux'])
        if pt4_mux == 'sum':
            sum_term.append(f"{mc_name}_PT4")
            wire_clk_ce = f"1'b1"
        elif pt4_mux == 'clk_ce':
            wire_clk_ce = f"{mc_name}_PT4"
        else:
            assert False
        pt5_mux = extract(fuses, macrocell['pt5_mux'])
        if pt5_mux == 'sum':
            sum_term.append(f"{mc_name}_PT5")
            wire_as_oe = f"1'b0"
        elif pt5_mux == 'as_oe':
            wire_as_oe = f"{mc_name}_PT5"
        else:
            assert False
        wire_xb = ' | '.join(sum_term) or "1'b0"
        if args.verbose:
            output.write(f"    wire {mc_name}_XA = {wire_xa};\n")
            output.write(f"    wire {mc_name}_XB = {wire_xb};\n")
            wire_x = f"{mc_name}_XA ^ {mc_name}_XB"
        elif wire_xa not in ("1'b0", "1'b1") and wire_xb not in ("1'b0", "1'b1"):
            wire_x = f"{wire_xa} ^ ({wire_xb})"
        elif wire_xa in ("1'b0", "1'b1") and wire_xb in ("1'b0", "1'b1"):
            wire_x = f"1'b{int(wire_xa[-1]) ^ int(wire_xb[-1])}"
        elif wire_xa in ("1'b0", "1'b1"):
            wire_x = wire_xb if wire_xa == "1'b0" else f"~({wire_xb})"
        elif wire_xb in ("1'b0", "1'b1"):
            wire_x = wire_xa if wire_xb == "1'b0" else f"~{wire_xa}"
        else:
            assert False
        output.write(f"    wire {mc_name}_X = {wire_x};\n");
        # TODO: missing mux
        output.write(f"    wire {mc_name}_D = {mc_name}_X;\n");
        storage = extract(fuses, macrocell['storage'])
        if storage == 'ff':
            clk_name = "CLK"
        elif storage == 'latch':
            clk_name = "EN"
        else:
            assert False
        pt4_func = extract(fuses, macrocell['pt4_func'])
        if pt4_func == 'clk':
            wire_clk = wire_clk_ce
            wire_ce = "1'b1"
        elif pt4_func == 'ce':
            global_clock = extract(fuses, macrocell['global_clock'])
            if global_clock == 'gclk1':
                wire_clk = 'GCLK1'
            elif global_clock == 'gclk2':
                wire_clk = 'GCLK2'
            elif global_clock == 'gclk3':
                wire_clk = 'GCLK3'
            else:
                assert False
            wire_ce = wire_clk_ce
        else:
            assert False
        pt5_func = extract(fuses, macrocell['pt5_func'])
        if pt5_func == 'as':
            wire_as = wire_as_oe
            wire_pt_oe = "1'b1"
        elif pt5_func == 'oe':
            wire_as = "1'b0"
            wire_pt_oe = wire_as_oe
        else:
            assert False
        events = []
        if args.verbose or wire_ce != "1'b1":
            output.write(f"    wire {mc_name}_CE = {wire_ce};\n")
        if args.verbose or wire_ar != "1'b0":
            events.append(f"{mc_name}_AR")
            output.write(f"    wire {mc_name}_AR = {wire_ar};\n")
        if args.verbose or wire_as != "1'b0":
            events.append(f"{mc_name}_AS")
            output.write(f"    wire {mc_name}_AS = {wire_as};\n")
        if args.verbose or storage == 'ff' or (storage == 'latch' and wire_clk != "1'b1"):
            events.append(f"{mc_name}_{clk_name}")
            output.write(f"    wire {mc_name}_{clk_name} = {wire_clk};\n")
        if storage == 'ff':
            event_expr = ' or '.join('posedge ' + event for event in events)
            output.write(f"    always @({event_expr})\n")
        elif storage == 'latch':
            output.write(f"    always @*\n")
        else:
            assert False
        if f"{mc_name}_AR" in events:
            output.write(f"        if({mc_name}_AR)\n")
            output.write(f"            {mc_name}_Q <= 1'b0;\n")
            if f"{mc_name}_AS" in events:
                output.write(f"        else if({mc_name}_AS)\n")
                output.write(f"            {mc_name}_Q <= 1'b1;\n")
        elif f"{mc_name}_AS" in events:
            output.write(f"        if({mc_name}_AS)\n")
            output.write(f"            {mc_name}_Q <= 1'b1;\n")
        if args.verbose or wire_ce != "1'b1" or (storage == 'latch' and wire_clk != "1'b1"):
            ce_exprs = []
            if args.verbose or (storage == 'latch' and wire_clk != "1'b1"):
                ce_exprs.append(f"{mc_name}_EN")
            if args.verbose or wire_ce != "1'b1":
                ce_exprs.append(f"{mc_name}_CE")
            if f"{mc_name}_AR" in events or f"{mc_name}_AS" in events:
                output.write(f"        else if({' && '.join(ce_exprs)})\n")
            else:
                output.write(f"        if({' && '.join(ce_exprs)})\n")
            output.write(f"            {mc_name}_Q <= {mc_name}_D;\n")
        else:
            if f"{mc_name}_AR" in events or f"{mc_name}_AS" in events:
                output.write(f"        else\n")
                output.write(f"            {mc_name}_Q <= {mc_name}_D;\n")
            else:
                output.write(f"        {mc_name}_Q <= {mc_name}_D;\n")
        fb_mux = extract(fuses, macrocell['fb_mux'])
        if fb_mux == 'comb':
            output.write(f"    assign FB_{mc_name} = {mc_name}_X;\n")
        elif fb_mux == 'sync':
            output.write(f"    assign FB_{mc_name} = {mc_name}_Q;\n")
        else:
            assert False
        # TODO: missing mux
        output_invert = extract(fuses, macrocell["output_invert"])
        if output_invert == 'off':
            output.write(f"    wire {mc_name}_O = {mc_name}_Q;\n")
        elif output_invert == 'on':
            output.write(f"    wire {mc_name}_O = ~{mc_name}_Q;\n")
        else:
            assert False
        oe_mux = extract(fuses, macrocell['oe_mux'])
        if oe_mux == 'gnd':
            wire_oe = "1'b0"
        elif oe_mux == 'vcc_pt5':
            wire_oe = wire_pt_oe
        elif oe_mux in ('goe1', 'goe2', 'goe3', 'goe4', 'goe5'):
            wire_oe = oe_mux.upper()
        else:
            assert False
        if args.verbose or wire_oe not in ("1'b0", "1'b1"): # inout
            output.write(f"    wire {mc_name}_OE = {wire_oe};\n")
            output.write(f"    assign PAD_{macrocell['pad']} = "
                                    f"{mc_name}_OE ? {mc_name}_O : 1'bz;\n")
        elif wire_oe == "1'b1": # output only
            output.write(f"    assign PAD_{macrocell['pad']} = {mc_name}_O;\n")
        elif wire_oe == "1'b0": # input only
            output.write(f"    assign PAD_{macrocell['pad']} = 1'bz;\n")
        else:
            assert False
        output.write(f"\n")

    output.write(f"endmodule\n")


if __name__ == '__main__':
    main()
