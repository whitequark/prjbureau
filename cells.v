(* blackbox *)
module BUF(input A, output Q);
  assign Q = A;
endmodule

(* blackbox *)
module OUTBUF(input A, output Q);
  assign Q = A;
endmodule

(* blackbox *)
module INBUF(input A, output Q);
  assign Q = A;
endmodule

(* blackbox *)
module IBUF(input A, output Q);
  assign Q = A;
endmodule

// (* blackbox *)
// module NOT(input A, output QN);
//   assign QN = A;
// endmodule

(* blackbox *)
module INV(input A, output QN);
  assign QN = A;
endmodule

(* blackbox *)
module XOR(input A, input B, output Q);
  assign Q = A ^ B;
endmodule

// TODO: XOR2

(* blackbox *)
module AND2(input A, input B, output Q);
  assign Q = A & B;
endmodule

// TODO: AND3
// TODO: AND4
// TODO: AND5
// TODO: AND6
// TODO: AND7
// TODO: AND8
// TODO: AND9
// TODO: AND10
// TODO: AND11
// TODO: AND12
// TODO: AND2I1
// TODO: AND2I2
// TODO: AND3I1
// TODO: AND3I2
// TODO: AND3I3
// TODO: AND4I1
// TODO: AND4I2
// TODO: AND4I3
// TODO: AND4I4

(* blackbox *)
module NAND2(input A, input B, output Q);
  assign Q = ~(A & B);
endmodule

// TODO: NAND3
// TODO: NAND4
// TODO: NAND5
// TODO: NAND6
// TODO: NAND7
// TODO: NAND8
// TODO: NAND9
// TODO: NAND10
// TODO: NAND11
// TODO: NAND12
// TODO: NAND2I1
// TODO: NAND2I2
// TODO: NAND3I1
// TODO: NAND3I2
// TODO: NAND3I3
// TODO: NAND4I1
// TODO: NAND4I2
// TODO: NAND4I3
// TODO: NAND4I4

(* blackbox *)
module OR2(input A, input B, output Q);
  assign Q = A | B;
endmodule

// TODO: OR3
// TODO: OR4
// TODO: OR5
// TODO: OR6
// TODO: OR7
// TODO: OR8
// TODO: OR9
// TODO: OR10
// TODO: OR11
// TODO: OR12
// TODO: OR2I1
// TODO: OR2I2
// TODO: OR3I1
// TODO: OR3I2
// TODO: OR3I3
// TODO: OR4I1
// TODO: OR4I2
// TODO: OR4I3
// TODO: OR4I4

(* blackbox *)
module NOR2(input A, input B, output Q);
  assign Q = ~(A | B);
endmodule

// TODO: NOR3
// TODO: NOR4
// TODO: NOR5
// TODO: NOR6
// TODO: NOR7
// TODO: NOR8
// TODO: NOR9
// TODO: NOR10
// TODO: NOR11
// TODO: NOR12
// TODO: NOR2I1
// TODO: NOR2I2
// TODO: NOR3I1
// TODO: NOR3I2
// TODO: NOR3I3
// TODO: NOR4I1
// TODO: NOR4I2
// TODO: NOR4I3
// TODO: NOR4I4

(* blackbox *)
module MUX2(input S0, input M0, input M1, output Q);
  assign Q = S0 ? M1 : M0;
endmodule

// TODO: MUX4
// TODO: MUX8

(* blackbox *)
module XNOR2(input A, input B, output Q);
  assign Q = ~(A ^ B);
endmodule

(* blackbox *)
module DFF(input CLK, input D, output reg Q);
  always @(posedge CLK)
    Q <= D;
endmodule

(* blackbox *)
module DFFE(input CLK, input CE, input D, output reg Q);
  always @(posedge CLK)
    if(CE) Q <= D;
endmodule

// TODO: DFF
// TODO: DFFE
// TODO: DFFAR
// TODO: DFFAS
// TODO: DFFARS
// TODO: DFFEARS
// TODO: LATCH
// TODO: JKFFEARS
// TODO: TFF
// TODO: TFFE
// TODO: TFFAR
// TODO: TFFAS
// TODO: TFFARS
// TODO: TFFEARS

(* blackbox *)
module BUFTH(input A, input ENA, output Q);
  assign Q = ENA ? A : 1'bz;
endmodule

(* blackbox *)
module TRI(input A, input ENA, output Q);
  assign Q = ENA ? A : 1'bz;
endmodule

// TODO: BI_BUF
