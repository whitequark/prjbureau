from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        config = device['global']['config']

        all_goe_choices = set()
        unique_goe_choices = set()
        for goe_name, goe_mux in device['goe_muxes'].items():
            for goe_choice in goe_mux['values']:
                if goe_choice in unique_goe_choices:
                    unique_goe_choices.remove(goe_choice)
                elif goe_choice not in all_goe_choices:
                    unique_goe_choices.add(goe_choice)
                all_goe_choices.add(goe_choice)

        goe_pads = []
        for goe_name, goe_mux in device['goe_muxes'].items():
            for goe_choice in goe_mux['values']:
                if not goe_choice.endswith('_PAD'): continue
                if goe_choice not in unique_goe_choices: continue
                goe_pads.append(goe_choice)
                break

        def run(code, **kwargs):
            return toolchain.run(
                f"module top(input R, C1, C2, C3, E1, "
                f"           input GOE1, GOE2, GOE3, GOE4, GOE5, GOE6, "
                f"           output Q); "
                f"{code} "
                f"endmodule",
                {
                    'R':  pinout[device['clear']['pad']],
                    'C1': pinout[device['clocks']['1']['pad']],
                    'C2': pinout[device['clocks']['2']['pad']],
                    'C3': pinout[device['clocks']['3']['pad']],
                    'E1': pinout[device['enables']['1']['pad']],
                    **{
                        f"GOE{1+n}": pinout[pad[:-4]]
                        for n, pad in enumerate(goe_pads)
                    },
                },
                f"{device_name}-{package}", **kwargs)

        f_gclr_pos = run(f"DFFAR ff(.CLK(1'b0), .AR(R), .D(1'b0), .Q(Q));")
        f_gclr_neg = run(f"wire Rn; INV in(R, Rn); "
                         f"DFFAR ff(.CLK(1'b0), .AR(Rn), .D(1'b0), .Q(Q));")
        config.update({
            'gclr_invert': bitdiff.describe(1, {
                'off': f_gclr_pos,
                'on':  f_gclr_neg,
            }),
        })

        for gclk, gclk_pin in (('gclk1', 'C1'), ('gclk2', 'C2'), ('gclk3', 'C3')):
            f_gclk_pos = run(f"DFF ff(.CLK({gclk_pin}), .D(1'b0), .Q(Q));")
            f_gclk_neg = run(f"wire Cn; INV in({gclk_pin}, Cn); "
                             f"DFF ff(.CLK(Cn), .D(1'b0), .Q(Q));")
            config.update({
                f"{gclk}_invert": bitdiff.describe(1, {
                    'off': f_gclk_pos,
                    'on':  f_gclk_neg,
                }),
            })

        for index, goe_pad in enumerate(goe_pads):
            goe_n = index + 1

            f_goe_pos = run(f"TRI t(R, GOE{goe_n}, Q);",
                            strategy={"Global_OE": goe_pad})
            f_goe_neg = run(f"wire GOE{goe_n}n; INV in(GOE{goe_n}, GOE{goe_n}n); "
                            f"TRI t(R, GOE{goe_n}n, Q);",
                            strategy={"Global_OE": goe_pad})
            config.update({
                f"goe{goe_n}_invert": bitdiff.describe(1, {
                    'off': f_goe_pos,
                    'on':  f_goe_neg,
                }),
            })

