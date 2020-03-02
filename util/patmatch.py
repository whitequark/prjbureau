# See patgen.py for the concept.

import math
import argparse

from .bitconv import read_svf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'count', metavar='COUNT', type=int,
        help='match patterns for COUNT fuses')
    parser.add_argument(
        'basename', metavar='BASENAME', type=str,
        help='read patterns from BASENAME_N.svf where N is 0..log2(COUNT)')
    parser.add_argument(
        'jed_to_svf', metavar='JED2SVF', type=argparse.FileType('w'),
        help='write JED to SVF mapping to a CSV file JED2SVF')
    parser.add_argument(
        'svf_to_jed', metavar='SVF2JED', type=argparse.FileType('w'),
        help='write SVF to JED mapping to a CSV file SVF2JED')
    args = parser.parse_args()

    n_patterns = math.ceil(math.log2(args.count))
    patterns = []
    print('reading', end='')
    for n_pattern in range(n_patterns):
        print('.', end='', flush=True)
        with open("{}_{}.svf".format(args.basename, n_pattern)) as f:
            svf_bits, _ = read_svf(f)
            patterns.append(svf_bits)
    print()

    svf_to_jed = {}
    jed_to_svf = {}
    print('mapping', end='')
    for n_block, block in patterns[0].items():
        print('.', end='', flush=True)
        for n_bit in range(len(block)):
            index = sum(patterns[n_pattern][n_block][n_bit] << n_pattern
                        for n_pattern in range(n_patterns))
            svf_to_jed[(n_block, n_bit)] = index
            if index not in jed_to_svf:
                jed_to_svf[index] = []
            jed_to_svf[index].append((n_block, n_bit))
    print()

    args.svf_to_jed.write("SVF ROW,SVF COL,JED\n")
    for svf_index, jed_index in sorted(svf_to_jed.items()):
        args.svf_to_jed.write("{},{},{}\n".format(*svf_index, jed_index))

    args.jed_to_svf.write("JED,SVF ROW,SVF COL\n")
    for jed_index, svf_indexes in sorted(jed_to_svf.items()):
        for svf_index in svf_indexes:
            args.jed_to_svf.write("{},{},{}\n".format(jed_index, *svf_index))


if __name__ == "__main__":
    main()
