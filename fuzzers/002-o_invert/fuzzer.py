from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        if device_name.startswith('ATF1508'):
            print(f"Skipping {device_name} because the fuzzer is broken on it")
            continue

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_name, macrocell in device['macrocells'].items():
            if macrocell['pad'] not in pinout:
                continue

            def run(code):
                return toolchain.run(
                    f"module top(input CLK1, CLK2, OE1, output Q);"
                    f"{code}"
                    f"endmodule",
                    {
                        'CLK1': pinout[device['clocks']['1']['pad']],
                        'CLK2': pinout[device['clocks']['2']['pad']],
                        'OE1': pinout[device['enables']['1']['pad']],
                        'Q': pinout[macrocell['pad']],
                    },
                    f"{device_name}-{package}")

            f_n = run("OR3    o1 (CLK1, CLK2, OE1, Q);")
            f_p = run("AND3I3 ai1(CLK1, CLK2, OE1, Q);")

            # http://ww1.microchip.com/downloads/en/Appnotes/DOC0424.PDF
            macrocell.update({
                'output_invert':
                    bitdiff.describe(1, {'off': f_p, 'on': f_n})
            })
