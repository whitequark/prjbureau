from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input CLK, output O); "
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK': pinout['C1'],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            f_dff0 = run("DFF ff(.CLK(CLK), .D(1'b0), .Q(Q));")
            f_dff1 = run("DFF ff(.CLK(CLK), .D(1'b1), .Q(Q));")

            # The VCC choice of XOR A mux is shared with PT2 choice: if pt2_mux is sum, then it is
            # VCC, otherwise it is PT2. Further, the XOR A mux is linked to CASOUT: if xor_a_mux
            # is sum, then CASOUT is 0, otherwise CASOUT is ST.

            macrocell.update({
                'xor_a_mux':
                    bitdiff.describe(1, {
                        'sum':     f_dff0,
                        'VCC_pt2': f_dff1
                    }),
                'cas_mux':
                    bitdiff.describe(1, {
                        'GND':     f_dff0,
                        'sum':     f_dff1
                    })
            })
