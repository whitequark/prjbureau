from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(gate):
                return toolchain.run(
                    f"module top(input CLK1, CLK2, OE1, output Q);"
                    f"    {gate} g(CLK1, CLK2, OE1, Q);"
                    f"endmodule",
                    {
                        "CLK1": pinout[device["clocks"]["1"]["pad"]],
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "OE1": pinout[device["enables"]["1"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    }, f"{device_name}-{package}")

            f_n = run("OR3")
            f_p = run("AND3I3")

            # http://ww1.microchip.com/downloads/en/Appnotes/DOC0424.PDF
            macrocell.update({
                "invert_output":
                    bitdiff.describe(1, {"on": f_n, "off": f_p})
            })
