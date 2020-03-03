from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(code):
                return toolchain.run(
                    f"module top(input CLK, GCLR, output Q); {code}; endmodule",
                    {
                        "CLK": pinout[device["clocks"]["1"]["pad"]],
                        "GCLR": pinout[device["clear"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}")

            f_dff   = run("DFF   x(.CLK(CLK), .D(1'b0), .Q(Q))")
            f_dffar = run("DFFAR x(.CLK(CLK), .AR(GCLR), .D(1'b0), .Q(Q))")

            # According to the diagram, there is a 3:1 mux driving AR, allowing to choose between
            # GCLR/(GCLR|PT3)/PT3. This is likely implemented as (GCLR&GCLRen)|(PT3&PT3en), where
            # the latter is decided by pt3_mux. The fitter seems to reject all attempts to OR
            # dedicated GCLR routing with a product term, however it does work on hardware the way
            # it is described in datasheet. Bizarrely, "no reset" is a choice supported by
            # the fitter but the datasheet implies it's impossible (without losing PT3).

            # https://www.dataman.com/media/datasheet/Atmel/ATF15xxAE_doc2398.pdf
            macrocell.update({
                "global_reset":
                    bitdiff.describe(1, {"off": f_dff, "on": f_dffar})
            })
