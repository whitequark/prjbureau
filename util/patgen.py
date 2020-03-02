# Suppose we have N fuses. Let's write log2(N) JED bitstreams that look like, in N=8 case:
#
#   01010101
#   00110011
#   00001111
#
# If we look at it in "time domain" (top to bottom) then one could imagine every bit transmitting
# its own position in the bitstream in straight binary. If, then, we rearrange the bits using
# an unknown but fixed permutation and put them in the SVF file, we can determine the position of
# every bit by once again looking at it in "time domain".

import math
import argparse
from bitarray import bitarray

from .bitconv import write_jed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'count', metavar='COUNT', type=int,
        help='generate patterns for COUNT fuses')
    parser.add_argument(
        'basename', metavar='BASENAME', type=str,
        help='write patterns to BASENAME_N.jed where N is 0..log2(COUNT)')
    args = parser.parse_args()

    n_patterns = math.ceil(math.log2(args.count))
    fuses = bitarray(args.count)
    for n_pattern in range(n_patterns):
        for n_fuse in range(len(fuses)):
            fuses[n_fuse] = (n_fuse >> n_pattern) & 1
        with open("{}_{}.jed".format(args.basename, n_pattern), "w") as f:
            write_jed(f, fuses, comment="")


if __name__ == "__main__":
    main()
