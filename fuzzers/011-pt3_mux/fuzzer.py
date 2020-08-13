from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input CLK1, CLK2, OE1, CLR, output O); "
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"wire Y1, Y2, Y3; "
                    f"AND2 a1(CLK1, CLK2, Y1); "
                    f"AND2 a2(CLK2, OE1, Y2); "
                    f"AND2 a3(OE1, CLR, Y3); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK1': pinout[device['clocks']['1']['pad']],
                        'CLK2': pinout[device['clocks']['2']['pad']],
                        'OE1': pinout[device['enables']['1']['pad']],
                        'CLR': pinout[device['clear']['pad']],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}",
                    strategy={'xor_synthesis': 'on'})

            f_sum = run("wire Y4; OR3 o1(Y2, Y1, Y3, Y4); DFF ff(1'b0, Y4, Q);")
            f_ar  = run("wire Y4; OR2 o1(Y1, Y2, Y4); DFFAR ff(1'b0, Y3, Y4, Q);")

            # PT3 can be either a part of the sum term, or serve as async reset.
            macrocell.update({
                'pt3_mux':
                    bitdiff.describe(1, {'ar': f_ar, 'sum': f_sum}),
            })
