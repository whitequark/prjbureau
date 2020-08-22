from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_name, macrocell in device['macrocells'].items():
            has_sstl = False
            if device_name.endswith("BE") and device_name != "ATF1502BE":
                if macrocell['pad'] not in (device['specials']['VREFA'],
                                            device['specials']['VREFB']):
                    has_sstl = True

            if macrocell['pad'] not in pinout:
                progress()
                print(f"Skipping {macrocell_name} on {device_name} because it is not bonded out")
                continue
            else:
                progress(1)

            for other_macrocell_name, other_macrocell in device['macrocells'].items():
                if other_macrocell['block'] != macrocell['block']: continue
                if other_macrocell_name != macrocell_name and other_macrocell['pad'] in pinout:
                    break
            else:
                assert False

            def run_o(**kwargs):
                return toolchain.run(
                    f"module top(output O); assign O = 1'b0; endmodule",
                    {'O': pinout[macrocell['pad']]},
                    f"{device_name}-{package}",
                    strategy=kwargs)

            def run_i(**kwargs):
                return toolchain.run(
                    f"module top(input I1, I2, output O); OR2 o(I1, I2, O); endmodule",
                    {
                        'I1': pinout[macrocell['pad']],
                        'I2': pinout[other_macrocell['pad']],
                    },
                    f"{device_name}-{package}",
                    strategy=kwargs)

            f_out  = run_o()
            f_fast = run_o(output_fast='O')
            f_oc   = run_o(open_collector='O')
            if device_name.endswith('AS'):
                f_lp   = run_o(MC_power='O')
            if device_name.endswith('BE'):
                f_hyst = run_o(schmitt_trigger='O')
                f_pu   = run_o(pull_up='O')
                f_pk   = run_o(pin_keep='O') # overrides pull-up
            if has_sstl:
                f_ttl  = run_i(voltage_level_A='3.3', voltage_level_B='3.3', SSTL_input='I2')
                f_sstl = run_i(voltage_level_A='3.3', voltage_level_B='3.3', SSTL_input='I1,I2')

            macrocell.update({
                'slow_output':
                    bitdiff.describe(1, {'off': f_fast, 'on': f_out}),
                'open_collector':
                    bitdiff.describe(1, {'off': f_out, 'on': f_oc}),
            })
            if device_name.endswith('AS'):
                macrocell.update({
                    'low_power':
                        bitdiff.describe(1, {'off': f_out, 'on': f_lp}),
                })
            if device_name.endswith('BE'):
                macrocell.update({
                    'termination': bitdiff.describe(2, {
                        'high_z': f_out,
                        'pull_up': f_pu,
                        'bus_keeper': f_pk,
                    }),
                    'schmitt_trigger':
                        bitdiff.describe(1, {'off': f_out, 'on': f_hyst}),
                })
            if has_sstl:
                macrocell.update({
                    'io_standard':
                        bitdiff.describe(1, {'ttl': f_ttl, 'sstl': f_sstl}),
                })
