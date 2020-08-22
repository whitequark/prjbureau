from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input CLK2, OE1, output O); "
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK2': pinout['C2'],
                        'OE1': pinout['E1'],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            f_mux_1   = run("DFF ff(.CLK(1'b1), .D(1'b0), .Q(Q));")
            f_mux_pt4 = run("DFF ff(.CLK(1'b0), .D(1'b0), .Q(Q));")

            # PT4 can be either a part of the sum term, or serve as clock/clock enable.
            macrocell.update({
                'pt4_mux':
                    bitdiff.describe(1, {'clk_ce': f_mux_pt4, 'sum': f_mux_1}),
            })
