from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input OE, CLK1, CLK2, CLK3, output O);"
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK1': pinout[device['clocks']['1']['pad']],
                        'CLK2': pinout[device['clocks']['2']['pad']],
                        'CLK3': pinout[device['clocks']['3']['pad']],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            f_clk1 = run("DFF ff(.CLK(CLK1), .D(CLK3), .Q(Q));")
            f_clk2 = run("DFF ff(.CLK(CLK2), .D(CLK3), .Q(Q));") # also happens to be 00
            f_clk3 = run("DFF ff(.CLK(CLK3), .D(CLK3), .Q(Q));")
            # 1 unused fuse combination

            # http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-3614-CPLD-ATF15-Overview.pdf
            macrocell.update({
                'gclk_mux':
                    bitdiff.describe(2, {'gclk2': f_clk2, 'gclk3': f_clk3, 'gclk1': f_clk1})
            })
