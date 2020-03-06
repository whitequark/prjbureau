//OPT: -device PLCC84
//OPT: -strategy pin_keep on
//PIN: CHIP "top" ASSIGNED TO PLCC84
module top(input I, output O);
  INV n(.A(I), .QN(O));
endmodule
