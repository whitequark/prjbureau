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
                        'CLK2': pinout[device['clocks']['2']['pad']],
                        'OE1': pinout[device['enables']['1']['pad']],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            # Use CLK2 because it has the same bit pattern as the global clock mux default.
            f_pt4_clk = run("DFFE ff(.CLK(OE1),  .CE(1'b1), .D(1'b0), .Q(Q));")
            f_pt4_ce  = run("DFFE ff(.CLK(CLK2), .CE(OE1),  .D(1'b0), .Q(Q));")

            # If PT4 is not used in the sum term it can be routed to exactly one of clock or
            # clock enable. If it is routed to clock, clock enable is fixed at 1. If it is routed
            # to clock enable, clock is selected according to the global clock mux.

            # http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-3614-CPLD-ATF15-Overview.pdf
            macrocell.update({
                'pt4_func':
                    bitdiff.describe(1, {'clk': f_pt4_clk, 'ce': f_pt4_ce}),
            })
