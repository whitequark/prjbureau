from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run_normal(clk):
                return toolchain.run(
                    # using GCLK3 always configures an MC as input, so always use it
                    f"module top(input OE, CLK1, CLK2, CLK3, output Q);"
                    f"    DFF x(.CLK({clk}), .D(CLK3), .Q(Q));"
                    f"endmodule",
                    {
                        "CLK1": pinout[device["clocks"]["1"]["pad"]],
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "CLK3": pinout[device["clocks"]["3"]["pad"]],
                        "OE": pinout[device["clear"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}")

            def run_gclk3_mc(clk):
                return toolchain.run(
                    f"module top(input OE, CLK1, CLK2, inout PAD);"
                    f"    wire Q, CLK3;"
                    f"    BIBUF b(.A(Q), .Q(CLK3), .EN(1'b0), .PAD(PAD));"
                    f"    DFF f(.CLK({clk}), .D(CLK3), .Q(Q));"
                    f"endmodule",
                    {
                        "CLK1": pinout[device["clocks"]["1"]["pad"]],
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "PAD": pinout[device["clocks"]["3"]["pad"]],
                        "OE": pinout[device["clear"]["pad"]],
                    },
                    f"{device_name}-{package}")

            def run(clk):
                if device["clocks"]["3"]["pad"] == macrocell["pad"]:
                    return run_gclk3_mc(clk)
                else:
                    return run_normal(clk)

            f_clk1 = run("CLK1")
            f_clk2 = run("CLK2")
            f_clk3 = run("CLK3")
            # 1 unused fuse combination

            macrocell.update({
                "global_clock":
                    bitdiff.describe(2, {"gclk1": f_clk1, "gclk2": f_clk2, "gclk3": f_clk3})
            })
