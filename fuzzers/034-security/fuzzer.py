from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        if device_name.endswith('AS'):
            # This isn't really a fuzzer (it doesn't even run the fitter); the identity of
            # the security fuse was determined by comparing ATMISP output.
            config_range = range(*device['ranges']['config'])
            device['config']['read_protection'] = {
                'fuses': [config_range.start + 32],
                'values': {
                    'on':  0,
                    'off': 1,
                }
            }
        elif device_name.endswith('BE'):
            progress()
            print(f"Skipping {device_name} because the JTAG protocol of ATF15xxBE is not known")
        else:
            assert False
