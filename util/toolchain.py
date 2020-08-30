import os, os.path, ntpath
import subprocess
import hashlib
import struct
import pickle
import json
from contextlib import contextmanager
from bitarray import bitarray

from . import root_dir, progress
from .jesd3 import JESD3Parser


vendor_dir = os.path.join(root_dir, "vendor")
work_dir   = os.path.join(root_dir, "work")
cache_dir  = os.path.join(root_dir, "cache")
has_cache  = os.path.exists(cache_dir)

fitter_env = {
    **os.environ,
    "WINEPREFIX": f"{os.getenv('HOME')}/.wine_atf"
}
subprocess.call([
    "wineserver", "-p"
], env=fitter_env)
fitter_env["FITTERDIR"] = subprocess.check_output([
    "winepath", "-w", vendor_dir
], env=fitter_env, text=True).strip()


class FitterError(Exception):
    pass


def run_uncached(input, pins, device, *, strategy={}, options=[], name="work", format="v"):
    progress(0)

    assert format in ("v", "tt", "edif")
    series, package = device.split("-") # eg ATF1502AS-TQFP44

    with open(os.path.join(work_dir, f"{name}.{format}"), "w") as f:
        f.write(input)

    if format == "v":
        subprocess.check_call([
            "yosys",
            "-q",
            "-p", f"read_verilog -lib {os.path.join(root_dir, 'cells.v')}",
            "-p", f"read_verilog {name}.v",
            "-p", f"hierarchy",
            "-p", f"write_edif -attrprop {name}.edif",
        ], cwd=work_dir)
        format = "edif"

    if pins is not None:
        with open(os.path.join(work_dir, f"{name}.pin"), "w") as f:
            f.write(f"CHIP \"{name}\" ASSIGNED TO AN {package}\n")
            for net, pin in pins.items():
                f.write(f"{net} : {pin}\n")

    # When the fitter fails (e.g. due to routing congestion), it does not produce a JED file.
    # Make sure there isn't a stale one.
    try:
        os.unlink(os.path.join(work_dir, f"{name}.jed"))
    except FileNotFoundError:
        pass

    strategy = {
        "ifmt": format,
        "optimize": "off",
        "DEBUG": "on",
        "output_fast": "off",
        "JTAG": "off",
        **strategy
    }
    if series == 'ATF1504BE' and 'no_tff' not in strategy:
        strategy['no_tff'] = 'on'
    strategy_options = []
    for strategy_option in strategy.items():
        strategy_options += ["-strategy", *strategy_option]
    subprocess.check_output([
        "wine", ntpath.join(fitter_env["FITTERDIR"], f"fit{series[3:7]}.exe"),
        "-silent",
        "-i", f"{name}.{format}",
        "-o", f"{name}.jed",
        "-tech", series,
        "-device", package,
        "-preassign", "keep",
        *options,
        *strategy_options,
    ], cwd=work_dir, env=fitter_env)

    with open(os.path.join(work_dir, f"{name}.fit"), encoding='windows-1252') as f:
        fitter_log = f.read()
        if "Warning : Routing fail" in fitter_log:
            raise FitterError("Routing fail")
        if "Warning : Conflict" in fitter_log:
            raise FitterError("Conflict")

    with open(os.path.join(work_dir, f"{name}.jed")) as f:
        parser = JESD3Parser(f.read())
        parser.parse()
        return parser.fuse


def run(input, pins, device, *, strategy={}, options=[], name="work", format="v"):
    if not has_cache:
        return run_uncached(input, pins, device, strategy=strategy, options=options,
                            name=name, format=format)

    cache_key = hashlib.sha1(json.dumps({
        'input': input,
        'format': format,
        'pins': None if pins is None else dict(sorted(pins.items())),
        'device': device,
        'strategy': strategy,
        'options': options,
    }).encode('ascii')).hexdigest()

    # quick and dirty caching code; i didn't bother making this properly portable because bitarray
    # will screw it up anyway
    try:
        with open(os.path.join(cache_dir, cache_key), 'rb') as f:
            length, = struct.unpack('i', f.read(struct.calcsize('i')))
            if length != 0:
                fuses = bitarray(endian='little')
                fuses.fromfile(f)
                del fuses[length:]
                return fuses
            else:
                raise pickle.load(f)

    except FileNotFoundError:
        @contextmanager
        def write_atomic():
            with open(os.path.join(cache_dir, cache_key + '.new'), 'wb') as f:
                yield f
            os.rename(os.path.join(cache_dir, cache_key + '.new'),
                      os.path.join(cache_dir, cache_key))

        try:
            fuses = run_uncached(input, pins, device, strategy=strategy, options=options,
                                 name=name, format=format)
            with write_atomic() as f:
                f.write(struct.pack('i', len(fuses)))
                fuses.tofile(f)
            return fuses

        except (subprocess.CalledProcessError, FitterError) as exn:
            with write_atomic() as f:
                f.write(struct.pack('i', 0))
                pickle.dump(exn, f)
            raise
