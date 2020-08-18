from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        # ATF15xx CPLDs include a safety feature that keeps the CPLD inactive unless programming
        # finishes completely:
        #
        #    The ATF1502AS(L) has a special feature which locks the device and prevents the inputs
        #    and I/O from driving if the programming process is interrupted for any reason.
        #
        # By observing the SVF programming vectors it is easy to see that programming always ends
        # with the 32-bit word that contains global device configuration, and that, unlike the rest
        # of the programming sequence, the address of this word is out of sequentially increasing
        # order. By observing that the first fuse of this word is always programmed by the fitter
        # and that it does not correspond to any other device feature (all of those having been
        # mapped out already), it is easy to deduce the function of this fuse.
        #
        # This isn't really a fuzzer (it doesn't even run the fitter), but there's no way to get
        # the vendor toolchain to reset this fuse because, well, it would be pointless. So this
        # is just verified to work on hardware.
        config_range = range(*device['ranges']['config'])
        device['config']['arming_switch'] = {
            'fuses': [config_range.start],
            'values': {
                'safe':  1,
                'armed': 0,
            }
        }
