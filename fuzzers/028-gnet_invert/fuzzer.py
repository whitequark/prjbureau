from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        gclk3_pad = device['macrocells'][device['specials']['GCLK3']]['pad']
        gclr_switch = device['globals']['GCLR']
        gclk_switches = {name: switch for name, switch in device['globals'].items()
                         if name.startswith('GCLK')}
        goe_switches = {name: switch for name, switch in device['globals'].items()
                        if name.startswith('GOE')}

        all_goe_choices = set()
        unique_goe_choices = set()
        for goe_name, goe_switch in goe_switches.items():
            for goe_choice in goe_switch['mux']['values']:
                if goe_choice in unique_goe_choices:
                    unique_goe_choices.remove(goe_choice)
                elif goe_choice not in all_goe_choices:
                    unique_goe_choices.add(goe_choice)
                all_goe_choices.add(goe_choice)
        unique_goe_choices.difference_update({
            f"R_PAD",
            f"C1_PAD",
            f"C2_PAD",
            f"{gclk3_pad}_PAD",
            f"E1_PAD",
        })

        goe_pads = []
        for goe_name, goe_switch in goe_switches.items():
            for goe_choice in goe_switch['mux']['values']:
                if not goe_choice.endswith('_PAD'): continue
                if goe_choice not in unique_goe_choices: continue
                goe_pads.append(goe_choice)
                break

        def run(code, **kwargs):
            return toolchain.run(
                f"module top(input GCLR, GCLK1, GCLK2, GCLK3, "
                f"           input GOE1, GOE2, GOE3, GOE4, GOE5, GOE6, "
                f"           output Q); "
                f"{code} "
                f"endmodule",
                {
                    'GCLR':  pinout['R'],
                    'GCLK1': pinout['C1'],
                    'GCLK2': pinout['C2'],
                    'GCLK3': pinout[gclk3_pad],
                    **{
                        f"GOE{1+n}": pinout[pad[:-4]]
                        for n, pad in enumerate(goe_pads)
                    },
                    'Q': pinout[device['macrocells']['MC1']['pad']],
                },
                f"{device_name}-{package}", **kwargs)

        f_gclr_pos = run(f"DFFAR ff(.CLK(1'b0), .AR(GCLR),  .D(1'b0), .Q(Q));")
        f_gclr_neg = run(f"wire GCLRn; INV in(GCLR, GCLRn); "
                         f"DFFAR ff(.CLK(1'b0), .AR(GCLRn), .D(1'b0), .Q(Q));")
        gclr_switch.update({
            'invert': bitdiff.describe(1, {
                'off': f_gclr_pos,
                'on':  f_gclr_neg,
            }),
        })

        for gclk_name, gclk_switch in gclk_switches.items():
            f_gclk_pos = run(f"DFF ff(.CLK({gclk_name}),  .D(1'b0), .Q(Q));")
            f_gclk_neg = run(f"wire {gclk_name}n; INV in({gclk_name}, {gclk_name}n); "
                             f"DFF ff(.CLK({gclk_name}n), .D(1'b0), .Q(Q));")

            macrocell = device['macrocells']['MC1']
            gclk_mux_option = macrocell['gclk_mux']
            gclk_mux_value = 0
            for n_fuse, fuse in enumerate(gclk_mux_option['fuses']):
                gclk_mux_value += f_gclk_pos[fuse] << n_fuse
            for gclk_mux_net, gclk_mux_net_value in gclk_mux_option['values'].items():
                if gclk_mux_value == gclk_mux_net_value:
                    break
            else:
                assert False
            assert gclk_mux_net == gclk_name

            gclk_switch.update({
                'invert': bitdiff.describe(1, {
                    'off': f_gclk_pos,
                    'on':  f_gclk_neg,
                }),
            })

        for (goe_name, goe_switch), goe_pad in zip(goe_switches.items(), goe_pads):
            f_goe_pos = run(f"TRI t(GCLR, {goe_name}, Q);",
                            strategy={"Global_OE": goe_pad})
            f_goe_neg = run(f"wire {goe_name}n; INV in({goe_name}, {goe_name}n); "
                            f"TRI t(GCLR, {goe_name}n, Q);",
                            strategy={"Global_OE": goe_pad})
            goe_switch.update({
                'invert': bitdiff.describe(1, {
                    'off': f_goe_pos,
                    'on':  f_goe_neg,
                }),
            })
