from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            if macrocell['pad'] not in pinout:
                print(f"Skipping {macrocell_name} on {device_name} because it is not bonded out")
                continue

            def run(code):
                return toolchain.run(
                    f"module top(input CLK1, CLK2, OE1, CLR, output Q); "
                    f"wire Y1, Y2; "
                    f"AND2 a1(CLK1, CLK2, Y1); "
                    f"AND2 a2(OE1, CLR, Y2); "
                    f"{code}; "
                    f"endmodule",
                    {
                        "CLK1": pinout[device["clocks"]["1"]["pad"]],
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "OE1": pinout[device["enables"]["1"]["pad"]],
                        "CLR": pinout[device["clear"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}",
                    strategy={"xor_synthesis": "on"})

            f_nor  = run("NOR2  n(Y1, Y2, Q)")
            f_xnor = run("XNOR2 x(Y1, Y2, Q)")

            # According to the diagram, both PT1 and PT2 can be, in principle, connected to either
            # of the XOR gate inputs. In reality, it is PT2 that is switched between the OR gate
            # and the XOR gate, which is expected because that's the non-enhanced path. This can
            # be shown by considering a bitstream produced for the expression (A&B)^((C&D)|(E&F)).
            # Fitter does not invert any terms and places the (C&D)|(E&F) term into PT1 and PT3.
            #
            # The reason NOR/XNOR are used rather than OR/XOR is quite interesting. By comparing
            # OR/NOR it can be seen that only bit S11 (output invert) differs. But, by comparing
            # NOR/XNOR it can be seen that the only difference is that PT1/PT2 are swapped. This
            # is a toolchain bug (for some reason S11 is set in both cases, not only for XNOR),
            # verified on hardware.

            # https://www.dataman.com/media/datasheet/Atmel/ATF15xxAE_doc2398.pdf
            macrocell.update({
                "pt2_mux":
                    bitdiff.describe(1, {"xor": f_xnor, "sum": f_nor}),
            })
