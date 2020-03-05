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


def run(input, pins, device, *, strategy={}, options=[], name="work", format="v"):
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

    strategy = {
        "ifmt": format,
        "optimize": "off",
        "DEBUG": "on",
        "output_fast": "off",
        "JTAG": "off",
        **strategy
    }
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

    with open(os.path.join(work_dir, f"{name}.jed")) as f:
        parser = JESD3Parser(f.read())
        parser.parse()
        return parser.fuse
