from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))

        def run(**kwargs):
            return toolchain.run(
                f"module top(input A, output Q); "
                f"wire A, Q; BUF b(A, Q); "
                f"endmodule",
                {},
                f"{device_name}-{package}", **kwargs)

        f_jtag_on  = run(strategy={'JTAG':'on'})
        f_jtag_off = run(strategy={'JTAG':'off'})

        # It is not yet clear whether the reconfiguration of the macrocells corresponding to
        # JTAG pins (which requires specifying scope= here) is incidental or necessary for
        # JTAG operation.
        device['global']['jtag'].update({
            'pin_func': bitdiff.describe(1, {
                'jtag': f_jtag_on,
                'user': f_jtag_off,
            }, scope=range(*device['ranges']['jtag'])),
        })
