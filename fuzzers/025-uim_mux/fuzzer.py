# UIM muxes are fuzzed in three stages. This first stage is a seed fuzzer: it discovers one
# UIM mux for every signal on the global bus, and that's it.

from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device['pins'].items()))

        uim_mux_range = range(*device['ranges']['uim_muxes'])
        assert len(uim_mux_range) % len(device['uim_muxes']) == 0
        uim_mux_size  = len(uim_mux_range) // len(device['uim_muxes'])
        for uim_index, (uim_name, uim_mux) in enumerate(device['uim_muxes'].items()):
            uim_mux['fuses'] = list(range(uim_mux_range.start + uim_mux_size * uim_index,
                                          uim_mux_range.start + uim_mux_size * (uim_index + 1)))
            uim_mux['values'] = {'GND1': (1 << uim_mux_size) - 1}

        def run_pad(code, object, probe_macrocell):
            return toolchain.run(
                f"module top(input I, output Q); "
                f"{code} "
                f"endmodule",
                {
                    'I': pinout[object['pad']],
                    'Q': pinout[probe_macrocell['pad']],
                },
                f"{device_name}-{package}")

        def run_pad_pos(object, probe_macrocell):
            return run_pad(f"DFF ff(1'b0, I, Q); ",
                           object, probe_macrocell)

        def run_pad_neg(object, probe_macrocell):
            return run_pad(f"wire IN; INV inv(I, IN); DFF ff(1'b0, IN, Q); ",
                           object, probe_macrocell)

        def run_fb(code, macrocell, probe_macrocell):
            return toolchain.run(
                f"module top(output Q); "
                f"wire I; DFF bff(1'b0, 1'b0, I);"
                f"{code} "
                f"endmodule",
                {
                    'bff': str(600 + int(macrocell['pad'][1:])),
                    'Q': pinout[probe_macrocell['pad']],
                },
                f"{device_name}-{package}")

        def run_fb_pos(macrocell, probe_macrocell):
            return run_fb(f"DFF ff(1'b0, I, Q); ",
                          macrocell, probe_macrocell)

        def run_fb_neg(macrocell, probe_macrocell):
            return run_fb(f"wire IN; INV inv(I, IN); DFF ff(1'b0, IN, Q); ",
                          macrocell, probe_macrocell)

        def run_task(object, probe_macrocell, probe_macrocell_name,
                     node_name, xpoint_kind, run_fn):
            pt1_fuse_range = range(
                *device['pterms'][probe_macrocell_name]['PT1']['fuse_range'])

            fuses = run_fn(object, probe_macrocell)

            # Exactly one UIM mux feeding exactly one product term must be active.
            pt1_zeros = fuses[pt1_fuse_range.start:pt1_fuse_range.stop].count(0)
            assert pt1_zeros == 1
            pt1_zero_index = fuses[pt1_fuse_range.start:pt1_fuse_range.stop].index(0)

            uim_zeros = fuses[uim_mux_range.start:uim_mux_range.stop].count(0)
            assert uim_zeros == 1
            uim_zero_index = fuses[uim_mux_range.start:uim_mux_range.stop].index(0)

            # Find the UIM mux.
            for uim_name, uim_mux in device['uim_muxes'].items():
                if uim_mux_range.start + uim_zero_index in uim_mux['fuses']:
                    break
            else:
                assert False
            if uim_name not in block['uim_muxes']:
                block['uim_muxes'].append(uim_name)
                block['uim_muxes'].sort(key=lambda x: int(x[3:]))
                for other_block_name, other_block in device['blocks'].items():
                    if other_block_name != block_name:
                        assert uim_name not in other_block['uim_muxes']

            # Find the value of the UIM mux.
            uim_value = sum(fuses[fuse] << n_fuse
                            for n_fuse, fuse in enumerate(uim_mux['fuses']))
            if node_name in uim_mux['values']:
                assert uim_mux['values'][node_name] == uim_value
            else:
                uim_mux['values'][node_name] = uim_value

            # Find the PT cross point.
            xpoint_name = f"{uim_name}_{xpoint_kind}"
            if xpoint_name in block['pterm_points']:
                assert block['pterm_points'][xpoint_name] == pt1_zero_index
            else:
                block['pterm_points'][xpoint_name] = pt1_zero_index

        for block_name, block in device['blocks'].items():
            block['uim_muxes'].clear()

            for macrocell_name, macrocell in device['macrocells'].items():
                for probe_macrocell_name, probe_macrocell in device['macrocells'].items():
                    if probe_macrocell['block'] != block_name: continue
                    if probe_macrocell['pad'] not in pinout: continue
                    if probe_macrocell['pad'] == macrocell['pad']: continue
                    break
                else:
                    assert False

                if macrocell['pad'] not in pinout:
                    print(f"Skipping {macrocell_name}_PAD on {device_name} because it is "
                          f"not bonded out")
                else:
                    run_task(macrocell, probe_macrocell, probe_macrocell_name,
                             f"{macrocell['pad']}_PAD", 'P', run_pad_pos)
                    run_task(macrocell, probe_macrocell, probe_macrocell_name,
                             f"{macrocell['pad']}_PAD", 'N', run_pad_neg)
                run_task(macrocell, probe_macrocell, probe_macrocell_name,
                         f"{macrocell_name}_FB", 'P', run_fb_pos)
                run_task(macrocell, probe_macrocell, probe_macrocell_name,
                         f"{macrocell_name}_FB", 'N', run_fb_neg)

            for node in (*device['clocks'].values(), *device['enables'].values(), device['clear']):
                for probe_macrocell_name, probe_macrocell in device['macrocells'].items():
                    if probe_macrocell['block'] != block_name: continue
                    if probe_macrocell['pad'] not in pinout: continue
                    if probe_macrocell['pad'] == node['pad']: continue
                    break
                else:
                    assert False

                run_task(node, probe_macrocell, probe_macrocell_name,
                         f"{node['pad']}_PAD", 'P', run_pad_pos)
                run_task(node, probe_macrocell, probe_macrocell_name,
                         f"{node['pad']}_PAD", 'N', run_pad_neg)

