import subprocess

from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device['pins'].items()))

        goe_mux_range = range(*device['ranges']['goe_muxes'])
        assert len(goe_mux_range) % len(device['goe_muxes']) == 0
        goe_mux_size  = len(goe_mux_range) // len(device['goe_muxes'])
        for goe_index, (goe_name, goe_mux) in enumerate(device['goe_muxes'].items()):
            goe_mux['fuses'] = list(range(goe_mux_range.start + goe_mux_size * goe_index,
                                          goe_mux_range.start + goe_mux_size * (goe_index + 1)))

        def run_pad(pad_name):
            for other_macrocell_name, other_macrocell in device['macrocells'].items():
                if other_macrocell['pad'] != pad_name and other_macrocell['pad'] in pinout:
                    break
            else:
                assert False
            return toolchain.run(
                f"module top(input OE, output O); "
                f"wire Q; DFFAS dff(1'b0, O, 1'b0, Q); TRI t(Q, OE, O); "
                f"endmodule",
                {
                    'O': pinout[other_macrocell['pad']],
                    'OE': pinout[pad_name],
                },
                f"{device_name}-{package}")

        # So, GOE mux feedback inputs. Where do I start...
        # This CUPL works and does what I expect:
        #
        #    Name      top;
        #    Device    f1502tqfp44;
        #    PIN = OEA;
        #    PIN = OEB;
        #    PIN = Y0;
        #    PIN = Y1;
        #    PIN = I0;
        #    PIN = I1;
        #    [Y1..Y0] = [I1..I0].io;
        #    [Y1..Y0].oe = !OEA & !OEB;
        #    PROPERTY ATMEL {JTAG=OFF};
        #    PROPERTY ATMEL {Global_OE=Y0};
        #
        # This Verilog, which produces EDIF -completely equivalent in every aspect-, does not:
        #
        #    //OPT: -strategy JTAG off
        #    //OPT: -strategy Global_OE Y0
        #    module top(input I0,I1, input OEA,OEB, output Y0,Y1);
        #        wire OE; AND2I2 a1(OEA,OEB,OE);
        #        wire OEL; LATCH l(.EN(1'b1), .D(OE), .Q(OEL));
        #        TRI t1(I0,OEL,Y0);
        #        TRI t2(I1,OEL,Y1);
        #    endmodule
        #
        # It looks like, for some completely incomprehensible reason, with TT2 input, the fitter
        # generates a latch for the buried node that is always enabled, which lets it use
        # the buried node for GOE, even though there's no latch in the input netlist, and also
        # it's useless. Whether this latch is present or not in the EDIF, EDIF input will never
        # cause buried nodes to be used for GOE.
        def run_fb(macrocell_idx, macrocell_name):
            for other1_macrocell_name, other1_macrocell in device['macrocells'].items():
                if other1_macrocell_name != macrocell_name:
                    break
            else:
                assert False
            for other2_macrocell_name, other2_macrocell in device['macrocells'].items():
                if (other2_macrocell_name != macrocell_name and
                        other2_macrocell_name != other1_macrocell_name):
                    break
            else:
                assert False
            pins = [
                f"OEA+:{pinout[device['clocks']['1']['pad']]}",
                f"OEB+:{pinout[device['clocks']['2']['pad']]}",
                f"Y0+:{pinout[device['macrocells'][other1_macrocell_name]['pad']]}",
                f"Y1+:{pinout[device['macrocells'][other2_macrocell_name]['pad']]}"
            ]
            return toolchain.run(f"""
                #$ PINS 4 {' '.join(pins)}
                #$ PROPERTY ATMEL Global_OE = Y0
                #$ PROPERTY ATMEL OE_node = {str(601 + macrocell_idx)}
                .i 2
                .o 4
                .type f
                .ilb  OEA OEB
                .ob   Y0 Y0.OE Y1 Y1.OE
                .phase 1111
                .p 2
                -- 0000
                00 0101
                .e
                """,
                None,
                f"{device_name}-{package}",
                strategy={'logic_doubling':'on'},
                format='tt')

        nodes = {}

        for node_type in ('clocks', 'enables', 'macrocells'):
            for node_name, node in device[node_type].items():
                if node['pad'] not in pinout:
                    continue
                try:
                    fuses = run_pad(node['pad'])
                except subprocess.CalledProcessError as err:
                    if err.returncode != 250:
                        raise
                    # Design constrained so that inability to use GOE is a total failure.
                    continue
                nodes[f"{node['pad']}_PAD"] = fuses

        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            fuses = run_fb(macrocell_idx, macrocell_name)
            if fuses[macrocell['fb_mux']['fuses'][0]] != macrocell['fb_mux']['values']['sync']:
                # Cannot constrain design by using AS with CUPL (fitter always rejects), so instead
                # verify that the only cell that should have sync feedback, has it.
                continue
            if f"{macrocell['pad']}_PAD" in nodes:
                # Due to a fitter bug, if a combinatorial node that is not itself a legal GOE
                # driver is constrained using OE_node, and the pad of the macrocell where the node
                # is placed, conversely, is a legal GOE driver, a miscompilation happens:
                # the fitter legalizes the node by inserting an always-transparent latch and
                # setting fb_mux to sync.
                #
                # Hardware testing and celestial rituals demonstrate that this is a miscompilation
                # (i.e. the GOE driver is not affected by fb_mux setting); the legalized node is
                # ignored, and GOE is driven simply by the pad.
                #
                # To account for this bug, ignore any FB mux drivers if a PAD mux driver exists
                # that refers to the same macrocell.
                continue
            nodes[f"{macrocell_name}_FB"] = fuses

        # The code above discovers 80% of choices on ATF1502. Where did 5 more go? I don't know.
        # It does not look like the fitter can route OE1 and OE2 anywhere other than GOE5 and GOE2,
        # and I didn't check the rest.

        found = 0
        for mux_name, mux in device['goe_muxes'].items():
            gnd_value = (1 << len(mux['fuses'])) - 1
            mux['values'] = {'GND': gnd_value}
            for node, fuses in nodes.items():
                value = sum(fuses[fuse] << n_fuse for n_fuse, fuse in enumerate(mux['fuses']))
                if value == gnd_value: continue
                # print(mux_name, node.ljust(8), "{:05b}".format(value))
                if value not in mux['values'].values():
                    found += 1
                mux['values'][node] = value

        total = sum(len(mux['fuses']) for mux in device['goe_muxes'].values())
        print("Fuzzed {}/{} ({:.0f}%) GOE muxes in device {}-{}"
              .format(found, total, found / total * 100, device_name, package))
