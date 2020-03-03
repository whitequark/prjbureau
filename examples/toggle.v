//OPT: -device TQFP44
//OPT: -strategy pin_keep on
//PIN: CHIP "top" ASSIGNED TO TQFP44
//PIN: CLK : 2
//PIN: O : 22
module top(input CLK, output O);
  TFF tff(.CLK(CLK), .T(1'b1), .Q(O));
endmodule
