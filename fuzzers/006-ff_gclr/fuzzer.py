from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device["pins"].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input CLK, GCLR, output O); "
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"{code} "
                    f"endmodule",
                    {
                        "CLK": pinout[device["clocks"]["1"]["pad"]],
                        "GCLR": pinout[device["clear"]["pad"]],
                        "ff": str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            f_dff   = run("DFF   ff(.CLK(CLK), .D(1'b0), .Q(Q));")
            f_dffar = run("DFFAR ff(.CLK(CLK), .AR(GCLR), .D(1'b0), .Q(Q));")

            # According to the diagram, there is a 3:1 mux driving AR, allowing to choose between
            # GCLR/(GCLR|PT3)/PT3. This is likely implemented as (GCLR&GCLRen)|(PT3&PT3en), where
            # the latter is decided by pt3_mux. The fitter seems to reject all attempts to OR
            # dedicated GCLR routing with a product term, however it does work on hardware the way
            # it is described in datasheet. "No reset" is a choice supported by the fitter and
            # the datasheet text but the diagram implies it's impossible (without losing PT3).

            # https://www.dataman.com/media/datasheet/Atmel/ATF15xxAE_doc2398.pdf
            macrocell.update({
                "gclr_mux":
                    bitdiff.describe(1, {"gnd": f_dff, "gclr": f_dffar})
            })
