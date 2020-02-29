//OPT: -device TQFP44
//OPT: -strategy JTAG=on
//PIN: CHIP "top" ASSIGNED TO TQFP44
//PIN: I : 2
//PIN: O : 22
module top(input I, output O);
  INV n(.A(I), .QN(O));
endmodule
