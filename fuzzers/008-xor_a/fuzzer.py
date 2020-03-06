from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            def run(code):
                return toolchain.run(
                    f"module top(input CLK, output O); "
                    f"wire Q; TRI tri(Q, 1'b0, O); "
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK': pinout[device['clocks']['1']['pad']],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            f_dff0 = run("DFF ff(.CLK(CLK), .D(1'b0), .Q(Q));")
            f_dff1 = run("DFF ff(.CLK(CLK), .D(1'b1), .Q(Q));")
            f_tff0 = run("TFF ff(.CLK(CLK), .T(1'b0), .Q(Q));")
            f_tff1 = run("TFF ff(.CLK(CLK), .T(1'b1), .Q(Q));")

            # According to the diagram, there is a 6:1 mux feeding the 1st (top) input of the XOR;
            # this mux is used for implementing post-sum inversion and TFFs. This fuzzer works
            # with the 4:1 part of that mux that generates 0/Q/!Q/1. The larger question is how
            # this part integrates into the 6:1 mux.
            #
            # The fitter sets the 4:1 mux to generate 0 in macrocells containing hard XOR gates.
            # Hardware testing shows that changing bits configuring the 4:1 mux when PT2 is used
            # as a XOR gate input results in quite strange behavior that affects both PT1 and PT2.
            # It is possible that these bits are reused to control the 3:1 mux feeding the 2nd
            # (bottom) input of the XOR.

            # http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-3614-CPLD-ATF15-Overview.pdf
            # https://www.dataman.com/media/datasheet/Atmel/ATF15xxSE_doc2401.pdf
            macrocell.update({
                'xor_a_input':
                    bitdiff.describe(2, {
                        'gnd':   f_dff0,
                        'ff_q':  f_tff0,
                        'ff_qn': f_tff1,
                        'vcc':   f_dff1
                    })
            })
