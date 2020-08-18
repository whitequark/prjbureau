from bitarray import bitarray

from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        config = device['global']['config']

        if device_name.startswith('ATF1502'):
            pwrdn_macrocells = {1:'MC7', 2:'MC31'}
            jtag_macrocells  = {'TCK':'MC25', 'TMS':'MC9', 'TDI':'MC4', 'TDO':'MC20'}
        elif device_name.startswith('ATF1504'):
            pwrdn_macrocells = {1:'MC3', 2:'MC35'}
            jtag_macrocells  = {'TCK':'MC48', 'TMS':'MC32', 'TDI':'MC8', 'TDO':'MC56'}
        elif device_name.startswith('ATF1508'):
            pwrdn_macrocells = {1:'MC3', 2:'MC67'}
            jtag_macrocells  = {'TCK':'MC96', 'TMS':'MC48', 'TDI':'MC32', 'TDO':'MC112'}
        else:
            assert False

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
                set_mc_option(fuses, macrocell_name, 'cas_mux', 'gnd')
            set_mc_option(fuses, macrocell_name, 'storage', 'latch')
            if device_name.endswith("BE"):
                set_mc_option(fuses, macrocell_name, 'oe_mux', 'vcc_pt5')

        def run(code="wire A, Q; BUF b(A, Q);", **kwargs):
            return toolchain.run(
                f"module top(input C1, C2, C3, A, output Q); "
                f"{code} "
                f"endmodule",
                {
                    'C1': pinout[device['clocks']['1']['pad']],
                    'C2': pinout[device['clocks']['2']['pad']],
                    'C3': pinout[device['clocks']['3']['pad']],
                },
                f"{device_name}-{package}", **kwargs)

        if device_name.endswith("AS"):
            f_pin_keep_off = run(strategy={'pin_keep':'off'})
            f_pin_keep_on  = run(strategy={'pin_keep':'on'})
            config.update({
                'bus_keeper': bitdiff.describe(1, {
                    'off': f_pin_keep_off,
                    'on':  f_pin_keep_on,
                }),
            })

        for index in (1, 2):
            f_pwrdn_n_off = run(strategy={f"pd{index}":'off'})
            f_pwrdn_n_on  = run(strategy={f"pd{index}":'on'})
            set_mc_input(f_pwrdn_n_on, pwrdn_macrocells[index])
            config.update({
                f"power_down_{index}": bitdiff.describe(1, {
                    'off': f_pwrdn_n_off,
                    'on':  f_pwrdn_n_on,
                }),
            })

        if device_name.endswith("AS"):
            f_gclk_itd_off = run(strategy={'gclk_itd':'off'})
            for gclk in ('gclk1', 'gclk2', 'gclk3'):
                f_gclk_itd_gclk_n = run(strategy={'gclk_itd':gclk})
                set_mc_input(f_pwrdn_n_on, pwrdn_macrocells[index])
                config.update({
                    f"{gclk}_itd": bitdiff.describe(1, {
                        'off': f_gclk_itd_off,
                        'on':  f_gclk_itd_gclk_n,
                    }),
                })

        for pin in ('tdi', 'tms'):
            f_pullup_off = run(strategy={'JTAG':'on', f"{pin}_pullup":'off'})
            f_pullup_on  = run(strategy={'JTAG':'on', f"{pin}_pullup":'on'})
            config.update({
                f"{pin}_pull_up": bitdiff.describe(1, {
                    'off': f_pullup_off,
                    'on':  f_pullup_on,
                }),
            })

        if device_name.endswith("AS"):
            f_power_reset_off = run(strategy={'power_reset':'off'})
            f_power_reset_on  = run(strategy={'power_reset':'on'})
            config.update({
                'power_reset': bitdiff.describe(1, {
                    'off': f_power_reset_off,
                    'on':  f_power_reset_on,
                }),
            })

        f_jtag_off = run(strategy={'JTAG':'off'})
        f_jtag_on  = run(strategy={'JTAG':'on'})
        for jtag_macrocell_name in jtag_macrocells.values():
            set_mc_input(f_jtag_on, jtag_macrocell_name)
        config.update({
            'jtag_pin_func': bitdiff.describe(1, {
                'user': f_jtag_off,
                'jtag': f_jtag_on,
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
