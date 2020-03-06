from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            def run(code):
                return toolchain.run(
                    f"module top(input CLK, output O); "
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK': pinout[device['clocks']['1']['pad']],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            f_dff   = run("DFF   ff(.CLK(CLK), .D(1'b0), .Q(Q));")
            f_latch = run("LATCH ff(.EN(CLK),  .D(1'b0), .Q(Q));")

            macrocell.update({
                'storage':
                    bitdiff.describe(1, {'ff': f_dff, 'latch': f_latch})
            })
