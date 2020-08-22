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
                    f"module top(input C2, R, output Q); {code} endmodule",
                    {
                        'C2': pinout['C2'],
                        'R': pinout['R'],
                        'Q': pinout[macrocell['pad']],
                    },
                    f"{device_name}-{package}")

            f_as = run(f"DFFAS x(.CLK(C2), .AS(R), .D(R), .Q(Q));")
            f_oe = run(f"wire X; DFF x(.CLK(C2), .D(R), .Q(X)); "
                       f"BUFTH t(.A(X), .ENA(R), .Q(Q));")

            # http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-3614-CPLD-ATF15-Overview.pdf
            macrocell.update({
                'pt5_func':
                    bitdiff.describe(1, {'as': f_as, 'oe': f_oe})
            })
