from bitarray import bitarray

from util import database, toolchain, bitdiff, progress


# For incomprehensible reasons, the fitter will apparently never derive foldback nodes from EDIF
# input (or at least I couldn't get it to). It is possible that using EDIF input force enables
# logic optimization (perhaps a roundtrip through AIG), breaking soft buffers as well as constructs
# that are delimited by redundant logic, like foldback nodes (which are specified using double
# inversion in CUPL). This is very annoying, and requires using CUPL and TT2 input.
#
# The monstrosity below has been generated from:
#
#   Name   foldback;
#   Device f1502tqfp44;
#   PINNODE [601..616] = [Y1..16];
#   [Y1..16].L = 'b'0;
#   [Y1..16].LE = 'b'1;
#   PINNODE = [FbY1..16];
#   [FbY1..16] = !(![Y1..16]);
#   PINNODE [617..632] = [FF1..16];
#   [FF1..16].D = 'd'0;
#   [FF1..16].CK = [FbY1..16];
#
# and then converted into an algebraic form for fun.
#
def foldback_tt2(src_nodes, dst_nodes):
    def names(fmt, iter=None):
        indexes = range(1, 17)
        return ' '.join(fmt.format(i=i, j=j) for i, j in zip(indexes, iter or indexes))

    fields = []
    for n in range(-1, 32):
        if n == -1:
            a = b = 0
        else:
            a = 1 << n
            if n < 16:
                b = 1 << (1 + n * 2)
            else:
                b = 1 << (16 + n)
        fields.append(("{:080b}".format(b) + ' ' + "{:032b}".format(a).replace('0', '-'))[::-1])
    table = '\n'.join(fields)

    return f"""\
#$ NODES 48 {names("FF{i}+:{j}", dst_nodes)} {names("FbY{i}+")} {names("Y{i}+:{j}", src_nodes)}
.i 32
.o 80
.type f
.ilb  {names("FbY{i}")} {names("Y{i}.Q")}
.ob   {names("FF{i}.REG FF{i}.C")} {names("FbY{i}")} {names("Y{i}.L Y{i}.LE")}
.phase {'1' * 80}
.p 33
{table}
.e"""


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))

        for block_name, block in device['blocks'].items():
            progress(1)

            for other_block_name, other_block in device['blocks'].items():
                if other_block_name != block_name:
                    break
            else:
                assert False

            macrocell_nodes = {macrocell_name: 601 + index
                               for index, macrocell_name in enumerate(device['macrocells'])}
            tt2 = foldback_tt2(src_nodes=[macrocell_nodes[macrocell_name]
                                          for macrocell_name in other_block['macrocells']],
                               dst_nodes=[macrocell_nodes[macrocell_name]
                                          for macrocell_name in block['macrocells']])

            # The fitter completely disregards any `PINNODE 3xx = net;` constraints, and instead
            # assigns foldbacks consistently from last to first macrocell in the block. However,
            # the actual routing is somewhat random, so we have to examine all related pterms.
            f_prev = toolchain.run(tt2, {}, f"{device_name}-{package}", format='tt')
            folds = []
            seen_pt1s = set()
            seen_pt4s = set()
            for index in range(len(block['macrocells'])):
                folds.append(f"FbY{1+index}")
                f_curr = toolchain.run(tt2, {}, f"{device_name}-{package}", format='tt',
                                       strategy={'Foldback_Logic':','.join(folds)})

                # The macrocell that gained a foldback now had PT1 enabled, find it.
                new_pt1s = set()
                for macrocell_name in block['macrocells']:
                    pt1_fuse_range = \
                        range(*device['macrocells'][macrocell_name]['pterm_ranges']['PT1'])
                    pt1_zeros = f_curr[pt1_fuse_range.start:pt1_fuse_range.stop].count(0)
                    if pt1_zeros == len(pt1_fuse_range):
                        pass # disabled
                    elif pt1_zeros == 1:
                        if macrocell_name not in seen_pt1s:
                            new_pt1s.add(macrocell_name)
                    else:
                        assert False
                seen_pt1s.update(new_pt1s)
                new_pt1, = new_pt1s

                # Now we know which macrocell to attribute the S9 flip to.
                #
                # One might wonder, what happens to the foldback net when PT1 is a part of the sum
                # ter? Based on hardware testing, pt1_mux routes PT1 to either foldback or sum
                # term, whichever is selected, and routes 0 to the other net. (This happens before
                # the inverter.) Note that foldback has a special case chosen by particular values
                # of xor_a_mux, xor_b_mux, and xor_invert.
                device['macrocells'][new_pt1].update({
                    'pt1_mux':
                        bitdiff.describe(1, {'flb': f_curr, 'sum': f_prev},
                                         scope=range(*device['ranges']['macrocells']))
                })

                # The macrocell that is driven by the foldback now had PT4 changed, find it.
                # But take into account that the fitter may have rearranged the foldback pterms
                # across macrocells.
                new_pt4s = set()
                for macrocell_name in block['macrocells']:
                    pt4_fuse_range = \
                        range(*device['macrocells'][macrocell_name]['pterm_ranges']['PT4'])
                    f_prev_pt4 = f_prev[pt4_fuse_range.start:pt4_fuse_range.stop]
                    f_curr_pt4 = f_curr[pt4_fuse_range.start:pt4_fuse_range.stop]
                    if f_prev_pt4 != f_curr_pt4:
                        assert f_curr_pt4.count(0) == 1
                        foldback_fuse = f_curr_pt4.index(0)
                        if foldback_fuse not in seen_pt4s:
                            new_pt4s.add(foldback_fuse)
                seen_pt4s.update(new_pt4s)
                new_pt4, = new_pt4s

                # Now we know which pterm fuse enables this foldback.
                block['pterm_points'][f"{new_pt1}_FLB"] = new_pt4

                f_prev = f_curr
