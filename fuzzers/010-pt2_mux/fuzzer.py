from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            if macrocell['pad'] not in pinout:
                progress()
                print(f"Skipping {macrocell_name} on {device_name} because it is not bonded out")
                continue
            else:
                progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input C1, C2, E1, R, output Q); "
                    f"wire Y1, Y2; "
                    f"AND2 a1(C1, C2, Y1); "
                    f"AND2 a2(E1, R, Y2); "
                    f"{code}; "
                    f"endmodule",
                    {
                        'C1': pinout['C1'],
                        'C2': pinout['C2'],
                        'E1': pinout['E1'],
                        'R': pinout['R'],
                        'Q': pinout[macrocell["pad"]],
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
