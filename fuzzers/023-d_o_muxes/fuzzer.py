from bitarray import bitarray

from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            if macrocell['pad'] not in pinout:
                progress()
                print(f"Skipping {macrocell_name} on {device_name} because it is not bonded out")
                continue
            elif 'oe_mux' not in macrocell:
                progress()
                print(f"Skipping {macrocell_name} on {device_name} because it lacks OE mux fuses")
                continue
            else:
                progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input CLK1, OE1, ...); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK1': pinout['C1'],
                        'OE1': pinout['E1'],
                        'IO': pinout[macrocell['pad']],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}",
                    strategy={"logic_doubling":"on", "fast_inlatch":"on"})

            # The diagram in the datasheet shows a 3:1 FF input mux and 2:1 output buffer mux, but
            # the reality is a bit different. The output buffer mux works as described and is
            # controlled by a single bit (S3). The FF input mux selects between a normal source
            # (combinatrial function) and a fast source (PT2 or IO pin), controlled by another
            # bit (S4). The way this happens is alluded to in the datasheet: it proposes to
            # "Bury Either Register or COM while Using the Other for Output", describes
            # "Fast Registered Input from Product Term", and the diagram shows the fast registered
            # I/O path.
            #
            # It works as follows. If the FF input mux selects the normal source, that's what
            # always feeds the FF. If, however, the FF input mux selects the fast source,
            # the output buffer mux selection also controls the particular source: selecting
            # combinatorial output on IO pad connects the PT2 term to FF input directly (*without*
            # affecting the sum term and independently of pt2_mux), selecting synchronous output
            # on IO pad connects the IO pad to FF input directly.
            #
            # Although a bit odd at first, the choice of shared encoding is in fact the only one
            # that makes sense here. The problem is the fitter; three different issues with
            # the fitter make fuzzing these bits fairly complicated:
            #   1. Although O=D=XT is a perfectly sensible choice, the fitter never uses it,
            #      and crashes if pressed (e.g. using XOR term, FF and buffer constraint).
            #   2. It will, however, use it by mistake if a buried DFFAS is constrained to
            #      a macrocell with no output. (Report shows OE as --, but the hardware enables
            #      the output buffer, so it's clearly a bug.)
            #   3. Although IO=Q, D=IO(fast) is a degenerate construct (if used with OE, it
            #      implements a sort of bus holder), it could be supported by the fitter still.
            #
            # These issues (especially (1)) make constructing minimal bitstreams challenging.
            # The following bitstreams -are- simple and minimal, but they work by coincidence;
            # they exploit a redundant logic loop to bury a FF without applying a pin constraint
            # to it, and the first one also invokes a fitter bug. In principle only the first
            # three are necessary to fuzz bits, but all four are used to verify for consistency.
            #
            # The behavior of the actual muxes has been extensively verified in hardware using
            # manual bitstream editing; this fuzzer only exists to discover fuse indexes.
            # The bus holder construct is particularly amusing because it works as expected even
            # without OE, just shorting the pin to the power rail and clocking it works.
            f_o_comb_d_comb = run(f"wire Q, X, Y; OR2 qo1(Q, X, Y); BUF qb1(Y, X); "
                                  f"                  DFFAS ff(CLK1, OE1, 1'b0,  Q);") # 11
            f_o_sync_d_comb = run(f"output IO;        DFFAS ff(CLK1, OE1, 1'b0, IO);") # 01
            f_o_comb_d_pt2  = run(f"wire Q, X, Y; OR2 qo1(Q, X, Y); BUF qb1(Y, X); "
                                  f"output IO = 1'b0; DFFAS ff(CLK1, OE1, 1'b0,  Q);") # 10
            f_o_sync_d_fast = run(f"wire Q, X, Y; OR2 qo1(Q, X, Y); BUF qb1(Y, X); "
                                  f"input  IO;        DFFAS ff(CLK1, OE1,   IO,  Q);") # 00

            # There is no way to enable OE with fast inlatch also enabled, so do this ourselves.
            oe_mux_fuses = macrocell['oe_mux']['fuses']
            oe_mux_gnd = macrocell['oe_mux']['values']['gnd']
            oe_mux_vcc = macrocell['oe_mux']['values']['vcc_pt5']
            for offset, oe_mux_fuse in enumerate(oe_mux_fuses):
                assert f_o_sync_d_fast[oe_mux_fuse] == (oe_mux_gnd >> offset) & 1
                f_o_sync_d_fast[oe_mux_fuse] = (oe_mux_vcc >> offset) & 1

            # Do bitdiff on all four bitstreams just for consistency checking.
            bitdiff.describe(2, {
                'o_comb_d_comb': f_o_comb_d_comb,
                'o_sync_d_comb': f_o_sync_d_comb,
                'o_comb_d_pt2':  f_o_comb_d_pt2,
                'o_sync_d_fast': f_o_sync_d_fast,
            })

            # Do final bitdiff.
            macrocell.update({
                'o_mux':
                    bitdiff.describe(1, {'comb': f_o_comb_d_comb, 'sync': f_o_sync_d_comb}),
                'd_mux':
                    bitdiff.describe(1, {'comb': f_o_comb_d_comb, 'fast': f_o_comb_d_pt2 }),
                'dfast_mux':
                    bitdiff.describe(1, {'pt2':  f_o_comb_d_pt2,  'pad':  f_o_sync_d_fast}),
            })
