//OPT: -device TQFP44
//PIN: CHIP "top" ASSIGNED TO TQFP44
//PIN: I : 2
//PIN: O : 3
module top(input I, output O);
  INV n(.A(I), .QN(O));
endmodule
