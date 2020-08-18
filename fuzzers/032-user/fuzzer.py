import bitarray

from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        user_fuse_range = range(*device['ranges']['user'])

        def run(**kwargs):
            return toolchain.run(
                f"module top(input A, output Q); "
                f"wire A, Q; BUF b(A, Q); "
                f"endmodule",
                {},
                f"{device_name}-{package}", **kwargs)

        f_0000 = run()
        f_0000[user_fuse_range.start:user_fuse_range.stop] = \
            bitarray.bitarray([0]*16) # or 2nd byte is garbage
        f_0100 = run(strategy={'ues': b'\x01'.decode('windows-1252')})
        f_0200 = run(strategy={'ues': b'\x02'.decode('windows-1252')})
        f_0400 = run(strategy={'ues': b'\x04'.decode('windows-1252')})
        f_0800 = run(strategy={'ues': b'\x08'.decode('windows-1252')})
        f_1000 = run(strategy={'ues': b'\x10'.decode('windows-1252')})
        f_3000 = run(strategy={'ues': b'\x30'.decode('windows-1252')})
        f_2000 = f_3000 ^ (f_0000 ^ f_1000) # \x20 is space
        f_4000 = run(strategy={'ues': b'\x40'.decode('windows-1252')})
        f_8000 = run(strategy={'ues': b'\x80'.decode('windows-1252')})

        f_ff00 = run(strategy={'ues': b'\xff'.decode('windows-1252')})
        f_ff01 = run(strategy={'ues': b'\xff\x01'.decode('windows-1252')})
        f_ff02 = run(strategy={'ues': b'\xff\x02'.decode('windows-1252')})
        f_ff04 = run(strategy={'ues': b'\xff\x04'.decode('windows-1252')})
        f_ff08 = run(strategy={'ues': b'\xff\x08'.decode('windows-1252')})
        f_ff10 = run(strategy={'ues': b'\xff\x10'.decode('windows-1252')})
        f_ff21 = run(strategy={'ues': b'\xff\x21'.decode('windows-1252')})
        f_ff20 = f_ff21 ^ (f_ff00 ^ f_ff01) # \x20 is space
        f_ff40 = run(strategy={'ues': b'\xff\x40'.decode('windows-1252')})
        f_ff80 = run(strategy={'ues': b'\xff\x80'.decode('windows-1252')})

        device['user'] = [
            bitdiff.describe(8, {
                'bit0': f_0100,
                'bit1': f_0200,
                'bit2': f_0400,
                'bit3': f_0800,
                'bit4': f_1000,
                'bit5': f_2000,
                'bit6': f_4000,
                'bit7': f_8000,
            }),
            bitdiff.describe(8, {
                'bit0': f_ff01,
                'bit1': f_ff02,
                'bit2': f_ff04,
                'bit3': f_ff08,
                'bit4': f_ff10,
                'bit5': f_ff20,
                'bit6': f_ff40,
                'bit7': f_ff80,
            }),
        ]
