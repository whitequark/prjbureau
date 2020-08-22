from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        if device_name.endswith("BE") and device_name != "ATF1502BE":
            has_tff = True
        else:
            has_tff = False

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            def run(code, **kwargs):
                return toolchain.run(
                    f"module top(input CLK, output O); "
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK': pinout['C1'],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}", **kwargs)

            f_dff   = run("DFF   ff(.CLK(CLK), .D(1'b0), .Q(Q));")
            f_latch = run("LATCH ff(.EN(CLK),  .D(1'b0), .Q(Q));")
            if has_tff:
                f_tff = run("TFF ff(.CLK(CLK), .T(1'b0), .Q(Q));", strategy={'no_tff':'off'})

            if has_tff:
                macrocell.update({
                    'storage': bitdiff.describe(2, {
                        'dff':   f_dff,
                        'tff':   f_tff,
                        'latch': f_latch
                    })
                })
            else:
                macrocell.update({
                    'storage': bitdiff.describe(1, {
                        'dff':   f_dff,
                        'latch': f_latch
                    })
                })
