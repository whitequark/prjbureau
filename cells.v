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
module XOR(input A, B, output Q);
  assign Q = A ^ B;
endmodule

(* blackbox *)
module XOR2(input A, B, output Q);
  assign Q = A ^ B;
endmodule

(* blackbox *)
module AND2(input A, B, output Q);
  assign Q = A & B;
endmodule

(* blackbox *)
module AND3(input A, B, C, output Q);
  assign Q = A & B & C;
endmodule

(* blackbox *)
module AND4(input A, B, C, D, output Q);
  assign Q = A & B & C & D;
endmodule

(* blackbox *)
module AND5(input A, B, C, D, E, output Q);
  assign Q = A & B & C & D & E;
endmodule

(* blackbox *)
module AND6(input A, B, C, D, E, F, output Q);
  assign Q = A & B & C & D & E & F;
endmodule

(* blackbox *)
module AND7(input A, B, C, D, E, F, G, output Q);
  assign Q = A & B & C & D & E & F & G;
endmodule

(* blackbox *)
module AND8(input A, B, C, D, E, F, G, H, output Q);
  assign Q = A & B & C & D & E & F & G & H;
endmodule

(* blackbox *)
module AND9(input A, B, C, D, E, F, G, H, I, output Q);
  assign Q = A & B & C & D & E & F & G & H & I;
endmodule

(* blackbox *)
module AND10(input A, B, C, D, E, F, G, H, I, J, output Q);
  assign Q = A & B & C & D & E & F & G & H & I & J;
endmodule

(* blackbox *)
module AND11(input A, B, C, D, E, F, G, H, I, J, K, output Q);
  assign Q = A & B & C & D & E & F & G & H & I & J & K;
endmodule

(* blackbox *)
module AND12(input A, B, C, D, E, F, G, H, I, J, K, L, output Q);
  assign Q = A & B & C & D & E & F & G & H & I & J & K & L;
endmodule

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
module NAND2(input A, B, output Q);
  assign Q = ~(A & B);
endmodule

(* blackbox *)
module NAND3(input A, B, C, output Q);
  assign Q = ~(A & B & C);
endmodule

(* blackbox *)
module NAND4(input A, B, C, D, output Q);
  assign Q = ~(A & B & C & D);
endmodule

(* blackbox *)
module NAND5(input A, B, C, D, E, output Q);
  assign Q = ~(A & B & C & D & E);
endmodule

(* blackbox *)
module NAND6(input A, B, C, D, E, F, output Q);
  assign Q = ~(A & B & C & D & E & F);
endmodule

(* blackbox *)
module NAND7(input A, B, C, D, E, F, G, output Q);
  assign Q = ~(A & B & C & D & E & F & G);
endmodule

(* blackbox *)
module NAND8(input A, B, C, D, E, F, G, H, output Q);
  assign Q = ~(A & B & C & D & E & F & G & H);
endmodule

(* blackbox *)
module NAND9(input A, B, C, D, E, F, G, H, I, output Q);
  assign Q = ~(A & B & C & D & E & F & G & H & I);
endmodule

(* blackbox *)
module NAND10(input A, B, C, D, E, F, G, H, I, J, output Q);
  assign Q = ~(A & B & C & D & E & F & G & H & I & J);
endmodule

(* blackbox *)
module NAND11(input A, B, C, D, E, F, G, H, I, J, K, output Q);
  assign Q = ~(A & B & C & D & E & F & G & H & I & J & K);
endmodule

(* blackbox *)
module NAND12(input A, B, C, D, E, F, G, H, I, J, K, L, output Q);
  assign Q = ~(A & B & C & D & E & F & G & H & I & J & K & L);
endmodule

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
module OR2(input A, B, output Q);
  assign Q = A | B;
endmodule

(* blackbox *)
module OR3(input A, B, C, output Q);
  assign Q = A | B | C;
endmodule

(* blackbox *)
module OR4(input A, B, C, D, output Q);
  assign Q = A | B | C | D;
endmodule

(* blackbox *)
module OR5(input A, B, C, D, E, output Q);
  assign Q = A | B | C | D | E;
endmodule

(* blackbox *)
module OR6(input A, B, C, D, E, F, output Q);
  assign Q = A | B | C | D | E | F;
endmodule

(* blackbox *)
module OR7(input A, B, C, D, E, F, G, output Q);
  assign Q = A | B | C | D | E | F | G;
endmodule

(* blackbox *)
module OR8(input A, B, C, D, E, F, G, H, output Q);
  assign Q = A | B | C | D | E | F | G | H;
endmodule

(* blackbox *)
module OR9(input A, B, C, D, E, F, G, H, I, output Q);
  assign Q = A | B | C | D | E | F | G | H | I;
endmodule

(* blackbox *)
module OR10(input A, B, C, D, E, F, G, H, I, J, output Q);
  assign Q = A | B | C | D | E | F | G | H | I | J;
endmodule

(* blackbox *)
module OR11(input A, B, C, D, E, F, G, H, I, J, K, output Q);
  assign Q = A | B | C | D | E | F | G | H | I | J | K;
endmodule

(* blackbox *)
module OR12(input A, B, C, D, E, F, G, H, I, J, K, L, output Q);
  assign Q = A | B | C | D | E | F | G | H | I | J | K | L;
endmodule

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
module NOR2(input A, B, output Q);
  assign Q = ~(A | B);
endmodule

(* blackbox *)
module NOR3(input A, B, C, output Q);
  assign Q = ~(A | B | C);
endmodule

(* blackbox *)
module NOR4(input A, B, C, D, output Q);
  assign Q = ~(A | B | C | D);
endmodule

(* blackbox *)
module NOR5(input A, B, C, D, E, output Q);
  assign Q = ~(A | B | C | D | E);
endmodule

(* blackbox *)
module NOR6(input A, B, C, D, E, F, output Q);
  assign Q = ~(A | B | C | D | E | F);
endmodule

(* blackbox *)
module NOR7(input A, B, C, D, E, F, G, output Q);
  assign Q = ~(A | B | C | D | E | F | G);
endmodule

(* blackbox *)
module NOR8(input A, B, C, D, E, F, G, H, output Q);
  assign Q = ~(A | B | C | D | E | F | G | H);
endmodule

(* blackbox *)
module NOR9(input A, B, C, D, E, F, G, H, I, output Q);
  assign Q = ~(A | B | C | D | E | F | G | H | I);
endmodule

(* blackbox *)
module NOR10(input A, B, C, D, E, F, G, H, I, J, output Q);
  assign Q = ~(A | B | C | D | E | F | G | H | I | J);
endmodule

(* blackbox *)
module NOR11(input A, B, C, D, E, F, G, H, I, J, K, output Q);
  assign Q = ~(A | B | C | D | E | F | G | H | I | J | K);
endmodule

(* blackbox *)
module NOR12(input A, B, C, D, E, F, G, H, I, J, K, L, output Q);
  assign Q = ~(A | B | C | D | E | F | G | H | I | J | K | L);
endmodule

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
module MUX2(input S0, M0, M1, output Q);
  assign Q = S0 ? M1 : M0;
endmodule

// TODO: MUX4
// TODO: MUX8

(* blackbox *)
module XNOR2(input A, B, output Q);
  assign Q = ~(A ^ B);
endmodule

(* blackbox *)
module DFF(input CLK, D, output reg Q);
  always @(posedge CLK)
    Q <= D;
endmodule

(* blackbox *)
module DFFE(input CLK, CE, D, output reg Q);
  always @(posedge CLK)
    if(CE) Q <= D;
endmodule

(* blackbox *)
module DFFAR(input CLK, AR, D, output reg Q);
  always @(posedge CLK, posedge AR)
    if(AR) Q <= 1'b0;
    else Q <= D;
endmodule

(* blackbox *)
module DFFAS(input CLK, AS, D, output reg Q);
  always @(posedge CLK, posedge AS)
    if(AS) Q <= 1'b1;
    else Q <= D;
endmodule

(* blackbox *)
module DFFARS(input CLK, AR, AS, D, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else Q <= D;
endmodule

(* blackbox *)
module DFFEARS(input CLK, AR, AS, CE, D, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else if(CE) Q <= D;
endmodule

(* blackbox *)
module LATCH(input EN, AR, AS, CE, D, output reg Q);
  // TODO: LATCH
endmodule

(* blackbox *)
module JKFFEARS(input CLK, /*!*/AR, /*!*/AS, CE, J, K, output reg Q);
  // TODO: JKFFEARS
endmodule

(* blackbox *)
module TFF(input CLK, T, output reg Q);
  always @(posedge CLK)
    Q <= Q ^ T;
endmodule

(* blackbox *)
module TFFE(input CLK, CE, T, output reg Q);
  always @(posedge CLK)
    if(CE) Q <= Q ^ T;
endmodule

(* blackbox *)
module TFFAR(input CLK, AR, T, output reg Q);
  always @(posedge CLK, posedge AR)
    if(AR) Q <= 1'b0;
    else Q <= Q ^ T;
endmodule

(* blackbox *)
module TFFAS(input CLK, AS, T, output reg Q);
  always @(posedge CLK, posedge AS)
    if(AS) Q <= 1'b1;
    else Q <= Q ^ T;
endmodule

(* blackbox *)
module TFFARS(input CLK, AR, AS, T, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else Q <= Q ^ T;
endmodule

(* blackbox *)
module TFFEARS(input CLK, AR, AS, CE, T, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else if(CE) Q <= Q ^ T;
endmodule

(* blackbox *)
module BUFTH(input A, ENA, output Q);
  assign Q = ENA ? A : 1'bz;
endmodule

(* blackbox *)
module TRI(input A, ENA, output Q);
  assign Q = ENA ? A : 1'bz;
endmodule

(* blackbox *)
module BIBUF(input A, EN, output Q, inout PAD);
  assign PAD = EN ? A : 1'bz;
  assign Q = PAD;
endmodule
