# UIM muxes are fuzzed in three stages. This second stage is a breadth fuzzer: it discovers new
# UIM mux choices and new UIM muxes by attempting, for every UIM mux, to simultaneously route all
# of the signals that are known inputs to the mux. It discovers every UIM mux (and PT cross point),
# simplifying the implementation of the third stage.

import itertools

from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        blocks = device['blocks']

        uim_mux_range = range(*device['ranges']['uim_muxes'])
        uim_mux_size  = len(uim_mux_range) // len(device['uim_muxes'])

        def run(nets, probe_macrocell, *, invert=False):
            pads = [net[:-4] for net in nets if net.endswith("_PAD")]
            fbs  = [net[:-3] for net in nets if net.endswith("_FB")]
            sigs = pads + fbs

            ins  = [f"input {pad}" for pad in pads]
            bffs = [f"wire {fb}; DFF fb_{fb}(1'b0, 1'b0, {fb}); " for fb in fbs]
            ands = []

            # AND8 is advertised as a primitive but doesn't actually work in EDIF...
            ands.append(f"wire Y0; BUF b(1'b1, Y0); ")
            y_wire = "Y0"
            for n, off in enumerate(range(0, len(sigs), 3)):
                chunk = sigs[off:off + 3]
                last  = (off + 3 >= len(sigs))
                ands.append(f"wire Y{n+1}; AND{len(chunk) + 1}{'I1' if invert and last else ''} "
                            f"a_{n+1}(Y{n}, {', '.join(chunk)}, Y{n+1}); ")
                y_wire = f"Y{n+1}"

            return toolchain.run(
                f"module top(output Q, {', '.join(ins)}); "
                f"{' '.join(bffs)} "
                f"{' '.join(ands)} "
                f"DFF ff(1'b0, {y_wire}, Q); "
                f"endmodule",
                {
                    'Q': pinout[probe_macrocell['pad']],
                    **{
                        pad: pinout[pad]
                        for pad in pads
                    },
                    **{
                        f"fb_{fb}": str(600 + int(fb[2:]))
                        for fb in fbs
                    },
                },
                f"{device_name}-{package}")

        for block_name, block in device['blocks'].items():
            progress(4)
            progress((sum(len(mux['values']) - 1 for mux in device['uim_muxes'].values()),
                      len(uim_mux_range)))

            # We only set up non-inverting xpoints while fuzzing because it is not straightforward
            # to invert all inputs (or any specific input) in an expression. This can be easily
            # done if the term to be inverted comes from a feedback node, and, conveniently,
            # fuzzing happens to produce expressions where the newly discovered xpoint is connected
            # to a buried register. Once we're done fuzzing, it's straightforward to discover all
            # of the inverting xpoints.
            neg_uim_nets = dict()

            # Make sure we get no more than one previously unknown UIM mux at a time.
            limit = 2

            visited = set()
            while len(block['uim_muxes']) < 40 or not all(neg_uim_nets.values()):
                net_sets = set()
                block_uim_muxes = {uim_name: device['uim_muxes'][uim_name]
                                   for uim_name in block['uim_muxes']}
                for uim_name, uim_mux in block_uim_muxes.items():
                    if len(uim_mux['values']) == uim_mux_size + 1: continue
                    uim_net_set = set(uim_mux['values']) - {'GND1'}
                    net_sets.update(map(frozenset, itertools.combinations(uim_net_set, limit)))
                net_sets.difference_update(visited)
                if not net_sets: break

                found = False
                for net_set in net_sets:
                    visited.add(net_set)
                    nets = set(net_set)

                    for probe_macrocell_name, probe_macrocell in device['macrocells'].items():
                        if probe_macrocell['block'] != block_name: continue
                        if f"{probe_macrocell_name}_FB" in net_set: continue
                        if f"{probe_macrocell['pad']}_PAD" in net_set: continue
                        break
                    else:
                        assert False
                    pt1_fuse_range = range(
                        *device['pterms'][probe_macrocell_name]['PT1']['fuse_range'])

                    fuses = run(sorted(net_set), probe_macrocell)

                    found_uim_name = found_uim_value = None
                    for new_uim_name, new_uim_mux in device['uim_muxes'].items():
                        new_uim_value = sum(fuses[fuse] << n_fuse
                                            for n_fuse, fuse in enumerate(new_uim_mux['fuses']))
                        if new_uim_value == new_uim_mux['values']['GND1']: continue
                        for new_uim_net, new_uim_net_value in new_uim_mux['values'].items():
                            # We know about this mux choice, ignore it
                            if new_uim_net_value == new_uim_value:
                                # Forget about this net
                                assert new_uim_net in nets
                                nets.remove(new_uim_net)

                                # Mask UIM mux
                                for fuse in new_uim_mux['fuses']:
                                    fuses[fuse] = 1

                                # Mask PT xpoint
                                xpoint_fuse = pt1_fuse_range.start + \
                                    block['pterm_points'][new_uim_name + '_P']
                                assert fuses[xpoint_fuse] == 0
                                fuses[xpoint_fuse] = 1

                                if (new_uim_name in neg_uim_nets and
                                        new_uim_net.endswith('_FB')):
                                    neg_uim_nets[new_uim_name] = [
                                        *[net for net in net_set if net != new_uim_net],
                                        new_uim_net
                                    ]

                                break

                        else: # This is a new mux choice!
                            assert found_uim_name is None
                            found_uim_name = new_uim_name
                            found_uim_value = new_uim_value

                    if found_uim_name is not None:
                        progress(1)
                        assert len(nets) == 1
                        found_uim_mux = device['uim_muxes'][found_uim_name]
                        found_uim_mux['values'][nets.pop()] = found_uim_value
                        if found_uim_name not in block['uim_muxes']:
                            block['uim_muxes'].append(found_uim_name)
                            block['uim_muxes'].sort(key=lambda x: int(x[3:]))
                            for other_block_name, other_block in device['blocks'].items():
                                if other_block_name != probe_macrocell['block']:
                                    assert found_uim_name not in other_block['uim_muxes']

                        pt1_zeros = fuses[pt1_fuse_range.start:pt1_fuse_range.stop].count(0)
                        assert pt1_zeros == 1
                        pt1_zero_index = fuses[pt1_fuse_range.start:pt1_fuse_range.stop].index(0)

                        xpoint_name = f"{found_uim_name}_P"
                        if xpoint_name in block['pterm_points']:
                            assert block['pterm_points'][xpoint_name] == pt1_zero_index
                        else:
                            block['pterm_points'][xpoint_name] = pt1_zero_index
                            neg_uim_nets[found_uim_name] = None
                        found = True

                if not found:
                    progress(3)
                    limit += 1
                else:
                    progress(2)
                    progress((sum(len(mux['values']) - 1 for mux in device['uim_muxes'].values()),
                              len(uim_mux_range)))

            # Earlier we only set up non-inverting xpoints. Set up inverting ones now.
            for uim_name, uim_net_set in neg_uim_nets.items():
                progress(1)

                for probe_macrocell_name, probe_macrocell in device['macrocells'].items():
                    if probe_macrocell['block'] != block_name: continue
                    if f"{probe_macrocell_name}_FB" in uim_net_set: continue
                    if f"{probe_macrocell['pad']}_PAD" in uim_net_set: continue
                    break
                else:
                    assert False
                pt1_fuse_range = range(
                    *device['pterms'][probe_macrocell_name]['PT1']['fuse_range'])

                f_pos = run(uim_net_set, probe_macrocell, invert=False)
                f_neg = run(uim_net_set, probe_macrocell, invert=True)
                f_xor = f_pos ^ f_neg
                assert f_xor.count(1) == 2, "Expected one bit to move between pos/neg"
                # One of the bits is the UIMn_P xpoint we already know...
                assert f_xor[pt1_fuse_range.start + block['pterm_points'][f"{uim_name}_P"]]
                f_xor[pt1_fuse_range.start + block['pterm_points'][f"{uim_name}_P"]] = 0
                # ... the other is the UIMn_N xpoint we want to know.
                assert f_xor.count(1) == 1 and f_xor.index(1) in pt1_fuse_range
                block['pterm_points'][f"{uim_name}_N"] = f_xor.index(1) - pt1_fuse_range.start

            # Make chipdb deterministic.
            block['pterm_points'] = {
                key: value for key, value in sorted(block['pterm_points'].items(),
                                                    key=lambda kv: kv[1])
            }

            assert len(block['uim_muxes']) == 40
            assert len(block['pterm_points']) == 96
