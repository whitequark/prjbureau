import subprocess
from collections import defaultdict

from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))

        goe_names = [name for name in device['globals'] if name.startswith("GOE")]
        goe_mux_range = range(*device['ranges']['goe_muxes'])
        assert len(goe_mux_range) % len(goe_names) == 0
        goe_mux_size  = len(goe_mux_range) // len(goe_names)
        for goe_index, goe_name in enumerate(goe_names):
            device['globals'][goe_name]['mux'] = {
                'fuses': list(range(goe_mux_range.start + goe_mux_size * goe_index,
                                    goe_mux_range.start + goe_mux_size * (goe_index + 1))),
                'values': {}
            }
        goe_muxes = {name: device['globals'][name]['mux'] for name in goe_names}

        def run_pads(pad_names):
            ports = []
            cells = []
            pins  = {}

            used_pads = set(pad_names)
            for n, pad_name in enumerate(pad_names):
                for other_macrocell_name, other_macrocell in device['macrocells'].items():
                    if (other_macrocell['pad'] not in used_pads and
                            other_macrocell['pad'] in pinout):
                        used_pads.add(other_macrocell['pad'])
                        break
                else:
                    assert False

                ports += [f"input OE{n}", f"output O{n}"]
                cells += [f"wire Q{n}; DFFAS dff{n}(1'b0, O{n}, 1'b0, Q{n}); ",
                          f"TRI t{n}(Q{n}, OE{n}, O{n}); "]
                pins.update({
                    f"O{n}": pinout[other_macrocell['pad']],
                    f"OE{n}": pinout[pad_name],
                })

            return toolchain.run(
                f"module top({', '.join(ports)}); "
                f"{' '.join(cells)} "
                f"endmodule",
                pins,
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
                f"OEA+:{pinout['C1']}",
                f"OEB+:{pinout['C2']}",
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

        def has_mux_value(node_name, fuses):
            for mux_name, mux in goe_muxes.items():
                gnd_value = (1 << len(mux['fuses'])) - 1
                value = sum(fuses[fuse] << n_fuse for n_fuse, fuse in enumerate(mux['fuses']))
                if value == gnd_value: continue

                if node_name in mux['values']:
                    assert mux['values'][node_name] == value
                    return True

            return False

        def add_mux_value(node_name, fuses, *, reserved=()):
            for mux_name, mux in goe_muxes.items():
                if mux_name in reserved:
                    continue

                gnd_value = (1 << len(mux['fuses'])) - 1
                value = sum(fuses[fuse] << n_fuse for n_fuse, fuse in enumerate(mux['fuses']))
                if value == gnd_value: continue

                assert node_name not in mux['values'], \
                       f"GOE mux {mux_name} already has a value for {node_name}"
                mux['values'][node_name] = value
                return mux_name

            assert False, f"all GOE muxes unprogrammed"

        worklist = {'C1', 'C2', 'E1'}
        for macrocell in device['macrocells'].values():
            worklist.add(macrocell['pad'])

        depth = 0
        pad_muxes = defaultdict(lambda: set())
        mux_pads = defaultdict(lambda: set())
        while worklist:
            progress(3)

            updates = []
            for pad in worklist:
                if pad not in pinout:
                    continue
                progress(2)

                reserved_muxes = []
                reserved_pads = []
                if depth > 0:
                    for _, pad_mux_name in zip(range(depth), pad_muxes[pad]):
                        reserved_muxes.append(pad_mux_name)
                        for other_pad in mux_pads[pad_mux_name]:
                            if other_pad == pad or other_pad in reserved_pads:
                                continue
                            if pad_muxes[other_pad].intersection(pad_muxes[pad]) != {pad_mux_name}:
                                continue
                            reserved_pads.append(other_pad)
                            break
                    if len(reserved_pads) != len(reserved_muxes):
                        continue

                try:
                    fuses = run_pads((pad, *reserved_pads))
                except subprocess.CalledProcessError as err:
                    if err.returncode != 250:
                        raise
                    # Design constrained so that inability to use GOE is a total failure.
                    continue

                mux_name = add_mux_value(f"{pad}_PAD", fuses, reserved=reserved_muxes)
                updates.append((pad, mux_name))

            worklist.clear()
            for pad, mux_name in updates:
                worklist.add(pad)
                pad_muxes[pad].add(mux_name)
                mux_pads[mux_name].add(pad)
            depth += 1

        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            fuses = run_fb(macrocell_idx, macrocell_name)
            if fuses[macrocell['fb_mux']['fuses'][0]] != macrocell['fb_mux']['values']['sync']:
                # Cannot constrain design by using AS with CUPL (fitter always rejects), so instead
                # verify that the only cell that should have sync feedback, has it.
                continue
            if has_mux_value(f"{macrocell['pad']}_PAD", fuses):
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
            add_mux_value(f"{macrocell_name}_FB", fuses)

        for mux_name, mux in goe_muxes.items():
            # Each GOE mux has exactly one fuse which is never used by the fitter. Hardware testing
            # and celestial rituals demonstrate that this fuse drives the GOE network low.
            assert len(mux['values']) == len(mux['fuses']) - 1, \
                   f"GOE mux {mux_name} should have exactly one unused value"
            # Setting the mux to all-ones (erased state) has the exact same result, so call the GND
            # with all-ones "GND1" and the GND with one fuse set to 0 "GND0".
            erased_value = (1 << len(mux['fuses'])) - 1
            mux['values']['GND1'] = erased_value
            for n_fuse in range(len(mux['fuses'])):
                value = erased_value ^ (1 << n_fuse)
                if value not in mux['values'].values():
                    mux['values']['GND0'] = value
