from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(code):
                return toolchain.run(
                    f"module top(input CLK2, OE1, output Q); {code}; endmodule",
                    {
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "OE1": pinout[device["enables"]["1"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}")

            f_mux_1   = run("DFF  x(.CLK(1'b1), .D(1'b0), .Q(Q))")
            f_mux_pt4 = run("DFF  x(.CLK(1'b0), .D(1'b0), .Q(Q))")
            # Use CLK2 because it has the same bit pattern as the global clock mux default.
            f_pt4_ena = run("DFFE x(.CLK(CLK2), .CE(OE1),  .D(1'b0), .Q(Q))")
            f_pt4_clk = run("DFFE x(.CLK(OE1),  .CE(1'b1), .D(1'b0), .Q(Q))")

            # This case is a bit complicated: the hardware implements a function like:
            #
            #     case (S5, S12)
            #         0, 0: CLK = GCLKn; CE  = 1;
            #         0, 1: CLK = GCLKn; CE  = PT4;
            #         1, 0: CLK = 1;     CE  = 1;
            #         1, 1: CLK = PT4;   CE  = 1;
            #
            # or equivalently (which is how I assume it's implemented, in spite of the diagram
            # in the datasheet):
            #
            #     case (S12)
            #         0: pt4mux = 1;
            #         1: pt4mux = PT4;
            #     case (S5)
            #         0: CLK = GCLKn;  CE = pt4mux;
            #         1: CLK = pt4mux; CE = 1;
            #
            # The case with CLK=1;CE=1; has dubious utility, but one could implement an SR latch
            # based on a DFF with it, without losing a product term.

            macrocell.update({
                "pt4_gate":
                    bitdiff.describe(1, {"off": f_mux_1, "on": f_mux_pt4}),
                "pt4_func":
                    bitdiff.describe(1, {"clock_enable": f_pt4_ena, "clock": f_pt4_clk}),
            })
