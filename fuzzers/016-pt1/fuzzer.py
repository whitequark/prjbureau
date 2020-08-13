from bitarray import bitarray

from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_name, macrocell in device['macrocells'].items():
            if macrocell['pad'] not in pinout:
                progress()
                print(f"Skipping {macrocell_name} on {device_name} because it is not bonded out")
                continue
            else:
                progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input CLK1, CLK2, output O); "
                    f"{code} "
                    f"endmodule",
                    {
                        "CLK1": pinout[device['clocks']['1']['pad']],
                        "CLK2": pinout[device['clocks']['2']['pad']],
                        "O": pinout[macrocell['pad']],
                    },
                    f"{device_name}-{package}")

            # Inactive bits of an active PT are 1, so ORing two different bitstreams that each
            # have two different inputs active in one PT produces an all-ones pattern in that PT.
            f_pta = run(f"assign O = CLK1;")
            f_ptb = run(f"assign O = CLK2;")
            f_pt = f_pta | f_ptb

            pt_range = range(*device['ranges']['pterms'])
            pt_fuses = f_pt[pt_range.start:pt_range.stop].search(bitarray([1]))
            assert len(pt_fuses) == 96, \
                   f"found {pt_fuses} PT fuses, expected 96"
            assert pt_fuses == list(range(min(pt_fuses), max(pt_fuses) + 1)), \
                   f"PT fuses not contiguous"

            device['pterms'][macrocell_name]['PT1']['fuse_range'] = \
                [min(pt_fuses), max(pt_fuses) + 1]
