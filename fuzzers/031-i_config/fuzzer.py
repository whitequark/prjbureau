from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        if not device_name.endswith("BE"): continue

        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        specials = device['specials']
        config = device['config']

        def run_used(pin, **kwargs):
            return toolchain.run(
                f"module top(input I, output Q); "
                f"assign Q = I; "
                f"endmodule",
                {'I': pinout[specials[pin]]},
                f"{device_name}-{package}", **kwargs)

        def run_unused(except_pin, **kwargs):
            ins  = []
            outs = []
            code = []
            pins = {}

            index = 0
            code.append(f"wire Y{index};")
            for pad, pin in pinout.items():
                if pad == specials[except_pin]: continue
                pins[pad] = pin
                if pad.startswith("M"):
                    outs.append(pad)
                    code.append(f"OR2 o{index}(1'b0, Y{index}, {pad}); "
                                f"wire Y{index+1} = {pad}; ")
                else:
                    ins .append(pad)
                    code.append(f"wire Y{index+1}; "
                                f"OR2 o{index}(Y{index}, {pad}, Y{index+1}); ")
                index += 1
            code.append(f"DFF dff(1'b0, Y{index}, Y0); ")

            return toolchain.run(
                f"module top(input {', '.join(ins)}, output {', '.join(outs)}); "
                f"{' '.join(code)} "
                f"endmodule",
                pins,
                f"{device_name}-{package}", **kwargs)

        for pin in ('CLK1', 'CLK2', 'OE1', 'CLR'):
            f_norm    = run_used(pin)
            f_hyst    = run_used(pin, strategy={'schmitt_trigger':'I'})

            # The fitter contains an atrocious bug that causes it to be unable to distinguish
            # between termination on pins 38 and 40 (TQFP-44). We work around that by setting
            # the termination for all unused pins, and making sure exactly one pin is unused.
            #
            # Depressing.
            f_highz   = run_unused(pin)
            f_pullup  = run_unused(pin, strategy={'pull_up_Unused':'on'})
            f_pulldn  = run_unused(pin, strategy={'unused_To_Ground':'on'})
            f_pinkeep = run_unused(pin, strategy={'unused_To_PinKeeper':'on'})

            config['pins'][pin] = {
                'hysteresis': bitdiff.describe(1, {
                    'off': f_norm,
                    'on':  f_hyst,
                }),
                'termination': bitdiff.describe(2, {
                    'high_z':     f_highz,
                    'pull_up':    f_pullup,
                    'pull_down':  f_pulldn,
                    'bus_keeper': f_pinkeep
                })
            }
