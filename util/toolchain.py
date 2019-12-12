import os, os.path, ntpath
import subprocess

from . import root_dir
from .jesd3 import JESD3Parser


vendor_dir = os.path.join(root_dir, "vendor")
work_dir   = os.path.join(root_dir, "work")

fitter_env = {
    **os.environ,
    "WINEPREFIX": f"{os.getenv('HOME')}/.wine_atf"
}
fitter_env["FITTERDIR"] = subprocess.check_output([
    "winepath", "-w", vendor_dir
], env=fitter_env, text=True).strip()


def run(verilog, pins, device, options=[], name="work"):
    series, package = device.split("-") # eg ATF1502AS-TQFP44

    with open(os.path.join(work_dir, f"{name}.v"), "w") as f:
        f.write(verilog)
    with open(os.path.join(work_dir, f"{name}.pin"), "w") as f:
        f.write(f"CHIP \"{name}\" ASSIGNED TO AN {package}\n")
        for net, pin in pins.items():
            f.write(f"{net} : {pin}\n")

    subprocess.check_call([
        "yosys",
        "-q",
        "-p", f"read_verilog -lib {os.path.join(root_dir, 'cells.v')}",
        "-p", f"read_verilog {name}.v",
        "-o", f"{name}.edif",
    ], cwd=work_dir)

    subprocess.check_call([
        "wine", ntpath.join(fitter_env["FITTERDIR"], f"fit{series[3:7]}.exe"),
        "-silent",
        "-i", f"{name}.edif",
        "-o", f"{name}.jed",
        "-tech", series,
        "-device", package,
        "-preassign", "keep",
        "-strategy", "ifmt", "edif",
        "-strategy", "optimize", "off",
        "-strategy", "JTAG", "off",
        *options
    ], cwd=work_dir, env=fitter_env)

    with open(os.path.join(work_dir, f"{name}.jed")) as f:
        parser = JESD3Parser(f.read())
        parser.parse()
        return parser.fuse
