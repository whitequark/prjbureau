# UIM muxes are fuzzed in three stages. This third stage is a depth fuzzer: it discovers all
# remaining UIM mux choices by recursively searching the routing state space with a highly
# randomized algorithm based on Knuth's "Algorithm X". (This is the only nondeterministic fuzzer
# in the project.)

import random
import subprocess

from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        blocks = device['blocks']

        uim_mux_range = range(*device['ranges']['uim_muxes'])
        uim_mux_size  = len(uim_mux_range) // len(device['uim_muxes'])

        def run(nets, probe_macrocell):
            pads = [net[:-4] for net in nets if net.endswith("_PAD")]
            fbs  = [net[:-3] for net in nets if net.endswith("_FB")]
            sigs = pads + fbs

            ins  = [f"input {pad}" for pad in pads]
            bffs = [f"wire {fb}; DFF fb_{fb}(1'b0, 1'b0, {fb}); " for fb in fbs]
            ands = []

            # We need way too many inputs to rely on existing primitives.
            ands.append(f"wire Y0; BUF b(1'b1, Y0); ")
            y_wire = "Y0"
            for n, off in enumerate(range(0, len(sigs), 3)):
                chunk = sigs[off:off + 3]
                last  = (off + 3 >= len(sigs))
                ands.append(f"wire Y{n+1}; AND{len(chunk) + 1} "
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

        uim_muxes = device['uim_muxes']

        uim_fuses_total = len(uim_mux_range)
        uim_fuses_known = None

        # Obtained through celestial rituals.
        if device_name.startswith("ATF1502"):
            gnd_per_block = 32
        elif device_name.startswith("ATF1504"):
            gnd_per_block = 28
        elif device_name.startswith("ATF1508"):
            gnd_per_block = 36
        else:
            assert False

        extra = 0
        visited = set()
        while (uim_fuses_known is None or
                    uim_fuses_known + len(device['blocks']) * gnd_per_block < uim_fuses_total):
            uim_fuses_known = sum(len(mux['values']) - 1 for mux in device['uim_muxes'].values())
            progress(2)
            progress((uim_fuses_known, uim_fuses_total))

            all_blocks_failed = True
            for block_name, block in device['blocks'].items():
                block_uim_muxes = {uim_name: uim_muxes[uim_name]
                                   for uim_name in block['uim_muxes']}
                block_uim_nets = set(sum((list(net_name
                                               for net_name in uim_muxes[uim_name]['values']
                                               if not net_name.startswith('GND'))
                                          for uim_name in block['uim_muxes']), []))

                dead_branches = 0
                dull_reduces = 0

                def extract_fuses(net_set):
                    assert len(net_set) < 40

                    for probe_macrocell_name, probe_macrocell in device['macrocells'].items():
                        if probe_macrocell['block'] != block_name: continue
                        if f"{probe_macrocell_name}_FB" in net_set: continue
                        if f"{probe_macrocell['pad']}_PAD" in net_set: continue
                        break
                    else:
                        assert False

                    return run(net_set, probe_macrocell)

                def find_muxes(net_set, fuses):
                    nets = set(net_set)

                    found = 0
                    found_uim_name = found_uim_value = None
                    for new_uim_name, new_uim_mux in block_uim_muxes.items():
                        new_uim_value = sum(fuses[fuse] << n_fuse
                                            for n_fuse, fuse in enumerate(new_uim_mux['fuses']))
                        if new_uim_value == new_uim_mux['values']['GND1']: continue
                        for new_uim_net, new_uim_net_value in new_uim_mux['values'].items():
                            if new_uim_net_value == new_uim_value:
                                nets.remove(new_uim_net)
                                break
                        else:
                            found += 1
                            found_uim_name = new_uim_name
                            found_uim_value = new_uim_value

                    if found == 1:
                        assert len(nets) == 1, f"expected a single net, not {nets}"
                        found_uim_net = nets.pop()
                        found_uim_mux = device['uim_muxes'][found_uim_name]
                        assert found_uim_net not in found_uim_mux['values']
                        assert found_uim_value not in found_uim_mux['values'].values()
                        found_uim_mux['values'][found_uim_net] = found_uim_value

                    return found

                def reduce_leaf(net_set):
                    global dull_reduces

                    try:
                        fuses = extract_fuses(net_set)
                    except toolchain.FitterError:
                        return False
                    except subprocess.CalledProcessError as err:
                        if err.returncode == 245:
                            return False
                        raise

                    found = find_muxes(net_set, fuses)
                    if found == 0:
                        return False
                    elif found == 1:
                        return True
                    else: # found > 1
                        progress(1)

                        for net_name in random.sample(net_set, len(net_set)):
                            if dull_reduces > 10:
                                break

                            if reduce_leaf(net_set.difference({net_name})):
                                found = find_muxes(net_set, fuses)
                                if found <= 1:
                                    break
                            else:
                                dull_reduces += 1
                        return True

                def search_tree(uims, nets, net_set=frozenset(), extra=0):
                    global dead_branches, live_leaves, dull_reduces
                    if dead_branches > 20:
                        return False

                    if len(uims) == 0 or len(nets) == 0:
                        net_set = net_set.union(random.sample(block_uim_nets - net_set, extra))
                        while len(net_set) > 35:
                            net_set.pop()

                        if net_set in visited:
                            return False
                        else:
                            visited.add(net_set)
                            dull_reduces = 0
                            if reduce_leaf(net_set):
                                dead_branches = 0
                                return True
                            else:
                                dead_branches += 1
                                return False

                    uim_name  = random.choice(list(uims))
                    net_names = [name for name in uim_muxes[uim_name]['values']
                                 if name in nets]
                    for net_name in random.sample(net_names, len(net_names)):
                        removed_uims = set(uim_name for uim_name in block_uim_muxes
                                           if net_name in uim_muxes[uim_name]['values'])
                        removed_nets = set(sum((list(uim_muxes[uim_name]['values'])
                                                for uim_name in removed_uims), []))
                        if search_tree(uims=uims - removed_uims,
                                       nets=nets - removed_nets,
                                       net_set=net_set.union({net_name}),
                                       extra=extra):
                            return True

                    return False

                uims=set(block_uim_muxes)
                nets=set(sum((list(name for name in uim_muxes[uim_name]['values']
                                  if not name.startswith('GND'))
                              for uim_name in block_uim_muxes), []))
                if search_tree(uims, nets, extra=extra):
                    all_blocks_failed = False

            if all_blocks_failed:
                progress(3)
                extra += 1

        for mux_name, mux in device['uim_muxes'].items():
            if 'GND0' in mux['values']: continue
            # Some UIM muxes have one fuse which is never used by the fitter. Hardware testing
            # and celestial rituals demonstrate that this fuse drives the PT input network low.
            assert (len(mux['values']) - 1) in (len(mux['fuses']) - 1, len(mux['fuses'])), \
                   f"UIM mux {mux_name} should have zero or one unused values"
            # Setting the mux to all-ones (erased state) has the exact same result, so call the GND
            # with all-ones "GND1" and the GND with one fuse set to 0 "GND0".
            erased_value = (1 << len(mux['fuses'])) - 1
            mux['values']['GND1'] = erased_value
            for n_fuse in range(len(mux['fuses'])):
                value = erased_value ^ (1 << n_fuse)
                if value not in mux['values'].values():
                    mux['values']['GND0'] = value
