import argparse
from bitarray import bitarray

from .jesd3 import JESD3Parser
from .svf import SVFParser, SVFEventHandler


def read_jed(file):
    parser = JESD3Parser(file.read())
    parser.parse()
    return parser.fuse, parser.design_spec


def write_jed(file, jed_bits, comment):
    assert '*' not in comment
    file.write("\x02{}*\n".format(comment))
    file.write("QF{}* F0*\n".format(len(jed_bits)))
    chunk_size = 64
    for start in range(0, len(jed_bits), chunk_size):
        file.write("L{:05d} {}*\n".format(start, jed_bits[start:start+chunk_size].to01()))
    file.write("\x030000\n")


class ATFSVFEventHandler(SVFEventHandler):
    def ignored(self, *args, **kwargs):
        pass
    svf_frequency = ignored
    svf_trst = ignored
    svf_state = ignored
    svf_endir = ignored
    svf_enddr = ignored
    svf_hir = ignored
    svf_sir = ignored
    svf_tir = ignored
    svf_hdr = ignored
    svf_sdr = ignored
    svf_tdr = ignored
    svf_runtest = ignored
    svf_piomap = ignored
    svf_pio = ignored

    def __init__(self):
        self.instr  = None
        self.addr   = 0
        self.data   = b''
        self.writes = {}

    def svf_sir(self, tdi, smask, tdo, mask):
        instr = int.from_bytes(tdi.tobytes(), "little")
        if instr == 0x2a1: # index
            self.instr = 'index'
        elif instr in (0x290, 0x291, 0x292, 0x293): # data
            self.instr = 'data'
        elif instr == 0x29e: # write
            self.instr = 'write'
        else:
            self.instr = None

    def svf_sdr(self, tdi, smask, tdo, mask):
        if self.instr == 'index':
            self.addr = int.from_bytes(tdi.tobytes(), "little")
        elif self.instr == 'data':
            self.data = tdi

    def svf_runtest(self, run_state, run_count, run_clock, min_time, max_time, end_state):
        if self.instr == 'write':
            self.writes[self.addr] = self.data


def read_svf(file):
    handler = ATFSVFEventHandler()
    parser = SVFParser(file.read(), handler)
    parser.parse_file()
    return handler.writes, ""


def write_svf(file, svf_bits, comment):
    raise NotImplementedError


def jed_to_svf(jed_bits):
    raise NotImplementedError


def svf_to_jed(svf_bits):
    raise NotImplementedError


class ATFFileType(argparse.FileType):
    def __call__(self, value):
        file = super().__call__(value)
        filename = file.name.lower()
        if not (filename.endswith('.jed') or filename.endswith('.svf')):
            raise argparse.ArgumentTypeError('{} is not a JED or SVF file'.format(filename))
        return file


def main():
    parser = argparse.ArgumentParser(description='Convert between ATF15xx JED and SVF files.')
    parser.add_argument(
        'input', metavar='INPUT', type=ATFFileType('r'),
        help='input file')
    parser.add_argument(
        'output', metavar='OUTPUT', type=ATFFileType('w'),
        help='output file')
    args = parser.parse_args()

    jed_bits = svf_bits = None
    if args.input.name.lower().endswith('.jed'):
        jed_bits, comment = read_jed(args.input)
    elif args.input.name.lower().endswith('.svf'):
        svf_bits, comment = read_svf(args.input)
    else:
        assert False

    if args.output.name.lower().endswith('.jed'):
        if jed_bits is None:
            jed_bits = svf_to_jed(svf_bits)
        write_jed(args.output, jed_bits, comment)
    elif args.output.name.lower().endswith('.svf'):
        if svf_bits is None:
            svf_bits = jed_to_svf(jed_bits)
        write_svf(args.output, svf_bits, comment)
    else:
        assert False


if __name__ == "__main__":
    main()
