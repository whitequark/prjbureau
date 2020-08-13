from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_name, macrocell in device['macrocells'].items():
            progress(1)

            if macrocell['pad'] not in pinout:
                print(f"Skipping {macrocell_name} on {device_name} because it is not bonded out")
                continue

            def run(code):
                return toolchain.run(
                    f"module top(input CLK2, CLR, output Q); {code} endmodule",
                    {
                        'CLK2': pinout[device['clocks']['2']['pad']],
                        'CLR': pinout[device['clear']['pad']],
                        'Q': pinout[macrocell['pad']],
                    },
                    f"{device_name}-{package}")

            f_as = run(f"DFFAS x(.CLK(CLK2), .AS(CLR), .D(CLR), .Q(Q));")
            f_oe = run(f"wire X; DFF x(.CLK(CLK2), .D(CLR), .Q(X)); "
                       f"BUFTH t(.A(X), .ENA(CLR), .Q(Q));")

            # http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-3614-CPLD-ATF15-Overview.pdf
            macrocell.update({
                'pt5_func':
                    bitdiff.describe(1, {'as': f_as, 'oe': f_oe})
            })
