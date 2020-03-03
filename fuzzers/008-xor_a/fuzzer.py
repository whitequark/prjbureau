from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(code):
                return toolchain.run(
                    f"module top(input CLK, output Q); {code}; endmodule",
                    {
                        "CLK": pinout[device["clocks"]["1"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}")

            f_dff0 = run("DFF x(.CLK(CLK), .D(1'b0), .Q(Q))")
            f_dff1 = run("DFF x(.CLK(CLK), .D(1'b1), .Q(Q))")
            f_tff0 = run("TFF x(.CLK(CLK), .T(1'b0), .Q(Q))")
            f_tff1 = run("TFF x(.CLK(CLK), .T(1'b1), .Q(Q))")

            # According to the diagram, there is a 6:1 mux feeding the 1st (top) input of the XOR;
            # this mux is used for implementing post-sum inversion and TFFs. It is not clear yet
            # what is the construction of the mux, e.g. whether it actually is a (n>4):1 mux of
            # 1/Q/!Q/0/? or whether it has a 0/Q/? mux for an intermediate value and a programmable
            # inverter of that intermediate value. (Depending on this, PT1/PT2 may be invertible
            # or not.) For now it is represented as a pair of 2:1 muxes: Z=0/Q; A=Z/!Z.

            # http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-3614-CPLD-ATF15-Overview.pdf
            # https://www.dataman.com/media/datasheet/Atmel/ATF15xxSE_doc2401.pdf
            macrocell.update({
                "xor_a_func":
                    bitdiff.describe(1, {"zero": f_dff0, "ff_q": f_tff0}),
                "xor_a_invert":
                    bitdiff.describe(1, {"off": f_dff0, "on": f_dff1})
            })
