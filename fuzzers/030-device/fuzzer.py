from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        config     = device['config']
        pin_config = device['config']['pins']

        gclk3_pad  =  device['specials']['CLK3']
        jtag_pads  = [device['specials'][net] for net in ('TCK','TMS','TDI','TDO')]
        pwrdn_pads = [device['specials'][net] for net in ('PD1','PD2')]

        def set_mc_option(fuses, macrocell_name, option_name, value_name):
            option = device['macrocells'][macrocell_name][option_name]
            value = option['values'][value_name]
            for n_fuse, fuse in enumerate(option['fuses']):
                fuses[fuse] = (value >> n_fuse) & 1

        def set_mc_input(fuses, macrocell_name):
            set_mc_option(fuses, macrocell_name, 'pt3_mux', 'sum')
            set_mc_option(fuses, macrocell_name, 'pt4_mux', 'sum')
            set_mc_option(fuses, macrocell_name, 'pt5_mux', 'sum')
            if device_name.endswith("AS"):
                set_mc_option(fuses, macrocell_name, 'pt5_func', 'as')
                set_mc_option(fuses, macrocell_name, 'xor_a_mux', 'sum')
                set_mc_option(fuses, macrocell_name, 'cas_mux', 'GND')
            set_mc_option(fuses, macrocell_name, 'storage', 'latch')
            if device_name.endswith("BE"):
                set_mc_option(fuses, macrocell_name, 'oe_mux', 'VCC_pt5')

        def run(code="wire A, Q; BUF b(A, Q);", **kwargs):
            return toolchain.run(
                f"module top(input C1, C2, C3, A, output Q); "
                f"{code} "
                f"endmodule",
                {
                    'C1': pinout['C1'],
                    'C2': pinout['C2'],
                    'C3': pinout[gclk3_pad],
                },
                f"{device_name}-{package}", **kwargs)

        if device_name.endswith("AS"):
            f_pin_keep_off = run(strategy={'pin_keep':'off'})
            f_pin_keep_on  = run(strategy={'pin_keep':'on'})
            config.update({
                'termination': bitdiff.describe(1, {
                    'high_z':     f_pin_keep_off,
                    'bus_keeper': f_pin_keep_on,
                }),
            })

        for index, pin in enumerate(('pd1', 'pd2')):
            f_pwrdn_n_off = run(strategy={pin:'off'})
            f_pwrdn_n_on  = run(strategy={pin:'on'})
            set_mc_input(f_pwrdn_n_on, f"MC{pwrdn_pads[index][1:]}")
            config.update({
                f"{pin}_pin_func": bitdiff.describe(1, {
                    'user': f_pwrdn_n_off,
                    'pd':   f_pwrdn_n_on,
                }),
            })

        if device_name.endswith("AS"):
            f_gclk_itd_off = run(strategy={'gclk_itd':'off'})
            for pin in ('CLK1', 'CLK2', 'CLK3'):
                f_gclk_itd_gclk_n = run(strategy={'gclk_itd':f"G{pin}"})
                pin_config[pin] = {
                    'standby_wakeup': bitdiff.describe(1, {
                        'off': f_gclk_itd_off,
                        'on':  f_gclk_itd_gclk_n,
                    }),
                }

        for pin in ('TMS', 'TDI'):
            f_pullup_off = run(strategy={'JTAG':'on', f"{pin}_pullup":'off'})
            f_pullup_on  = run(strategy={'JTAG':'on', f"{pin}_pullup":'on'})
            pin_config[pin] = {
                'termination': bitdiff.describe(1, {
                    'high_z':  f_pullup_off,
                    'pull_up': f_pullup_on,
                }),
            }

        if device_name.endswith("AS"):
            f_power_reset_off = run(strategy={'power_reset':'off'})
            f_power_reset_on  = run(strategy={'power_reset':'on'})
            config.update({
                'reset_hysteresis': bitdiff.describe(1, {
                    'small': f_power_reset_off,
                    'large': f_power_reset_on,
                }),
            })

        f_jtag_off = run(strategy={'JTAG':'off'})
        f_jtag_on  = run(strategy={'JTAG':'on'})
        for jtag_pad in jtag_pads:
            set_mc_input(f_jtag_on, f"MC{jtag_pad[1:]}")
        config.update({
            'jtag_pin_func': bitdiff.describe(1, {
                'user': f_jtag_off,
                'jtag': f_jtag_on,
            }),
        })
