module BUF(input A, output Q);
  assign Q = A;
endmodule

module OUTBUF(input A, output Q);
  assign Q = A;
endmodule

module INBUF(input A, output Q);
  assign Q = A;
endmodule

module IBUF(input A, output Q);
  assign Q = A;
endmodule

// module NOT(input A, output QN);
//   assign QN = ~A;
// endmodule

module INV(input A, output QN);
  assign QN = ~A;
endmodule

module XOR(input A, B, output Q);
  assign Q = A ^ B;
endmodule

module XOR2(input A, B, output Q);
  assign Q = A ^ B;
endmodule

module AND2(input A, B, output Q);
  assign Q = A & B;
endmodule

module AND3(input A, B, C, output Q);
  assign Q = A & B & C;
endmodule

module AND4(input A, B, C, D, output Q);
  assign Q = A & B & C & D;
endmodule

module AND5(input A, B, C, D, E, output Q);
  assign Q = A & B & C & D & E;
endmodule

module AND6(input A, B, C, D, E, F, output Q);
  assign Q = A & B & C & D & E & F;
endmodule

module AND7(input A, B, C, D, E, F, G, output Q);
  assign Q = A & B & C & D & E & F & G;
endmodule

module AND8(input A, B, C, D, E, F, G, H, output Q);
  assign Q = A & B & C & D & E & F & G & H;
endmodule

module AND9(input A, B, C, D, E, F, G, H, I, output Q);
  assign Q = A & B & C & D & E & F & G & H & I;
endmodule

module AND10(input A, B, C, D, E, F, G, H, I, J, output Q);
  assign Q = A & B & C & D & E & F & G & H & I & J;
endmodule

module AND11(input A, B, C, D, E, F, G, H, I, J, K, output Q);
  assign Q = A & B & C & D & E & F & G & H & I & J & K;
endmodule

module AND12(input A, B, C, D, E, F, G, H, I, J, K, L, output Q);
  assign Q = A & B & C & D & E & F & G & H & I & J & K & L;
endmodule

module AND2I1(input A, BN, output Q);
  assign Q = A & ~BN;
endmodule

module AND2I2(input AN, BN, output Q);
  assign Q = ~AN & ~BN;
endmodule

module AND3I1(input A, B, CN, output Q);
  assign Q = A & B & ~CN;
endmodule

module AND3I2(input A, BN, CN, output Q);
  assign Q = A & ~BN & ~CN;
endmodule

module AND3I3(input AN, BN, CN, output Q);
  assign Q = ~AN & ~BN & ~CN;
endmodule

module AND4I1(input A, B, C, DN, output Q);
  assign Q = A & B & C & ~DN;
endmodule

module AND4I2(input A, B, CN, DN, output Q);
  assign Q = A & B & ~CN & ~DN;
endmodule

module AND4I3(input A, BN, CN, DN, output Q);
  assign Q = A & ~BN & ~CN & ~DN;
endmodule

module AND4I4(input AN, BN, CN, DN, output Q);
  assign Q = ~AN & ~BN & ~CN & ~DN;
endmodule

module NAND2(input A, B, output QN);
  assign QN = ~(A & B);
endmodule

module NAND3(input A, B, C, output QN);
  assign QN = ~(A & B & C);
endmodule

module NAND4(input A, B, C, D, output QN);
  assign QN = ~(A & B & C & D);
endmodule

module NAND5(input A, B, C, D, E, output QN);
  assign QN = ~(A & B & C & D & E);
endmodule

module NAND6(input A, B, C, D, E, F, output QN);
  assign QN = ~(A & B & C & D & E & F);
endmodule

module NAND7(input A, B, C, D, E, F, G, output QN);
  assign QN = ~(A & B & C & D & E & F & G);
endmodule

module NAND8(input A, B, C, D, E, F, G, H, output QN);
  assign QN = ~(A & B & C & D & E & F & G & H);
endmodule

module NAND9(input A, B, C, D, E, F, G, H, I, output QN);
  assign QN = ~(A & B & C & D & E & F & G & H & I);
endmodule

module NAND10(input A, B, C, D, E, F, G, H, I, J, output QN);
  assign QN = ~(A & B & C & D & E & F & G & H & I & J);
endmodule

module NAND11(input A, B, C, D, E, F, G, H, I, J, K, output QN);
  assign QN = ~(A & B & C & D & E & F & G & H & I & J & K);
endmodule

module NAND12(input A, B, C, D, E, F, G, H, I, J, K, L, output QN);
  assign QN = ~(A & B & C & D & E & F & G & H & I & J & K & L);
endmodule

module NAND2I1(input A, BN, output QN);
  assign QN = ~(A & ~BN);
endmodule

module NAND2I2(input AN, BN, output QN);
  assign QN = ~(~AN & ~BN);
endmodule

module NAND3I1(input A, B, CN, output QN);
  assign QN = ~(A & B & ~CN);
endmodule

module NAND3I2(input A, BN, CN, output QN);
  assign QN = ~(A & ~BN & ~CN);
endmodule

module NAND3I3(input AN, BN, CN, output QN);
  assign QN = ~(~AN & ~BN & ~CN);
endmodule

module NAND4I1(input A, B, C, DN, output QN);
  assign QN = ~(A & B & C & ~DN);
endmodule

module NAND4I2(input A, B, CN, DN, output QN);
  assign QN = ~(A & B & ~CN & ~DN);
endmodule

module NAND4I3(input A, BN, CN, DN, output QN);
  assign QN = ~(A & ~BN & ~CN & ~DN);
endmodule

module NAND4I4(input AN, BN, CN, DN, output QN);
  assign QN = ~(~AN & ~BN & ~CN & ~DN);
endmodule

module OR2(input A, B, output Q);
  assign Q = A | B;
endmodule

module OR3(input A, B, C, output Q);
  assign Q = A | B | C;
endmodule

module OR4(input A, B, C, D, output Q);
  assign Q = A | B | C | D;
endmodule

module OR5(input A, B, C, D, E, output Q);
  assign Q = A | B | C | D | E;
endmodule

module OR6(input A, B, C, D, E, F, output Q);
  assign Q = A | B | C | D | E | F;
endmodule

module OR7(input A, B, C, D, E, F, G, output Q);
  assign Q = A | B | C | D | E | F | G;
endmodule

module OR8(input A, B, C, D, E, F, G, H, output Q);
  assign Q = A | B | C | D | E | F | G | H;
endmodule

module OR9(input A, B, C, D, E, F, G, H, I, output Q);
  assign Q = A | B | C | D | E | F | G | H | I;
endmodule

module OR10(input A, B, C, D, E, F, G, H, I, J, output Q);
  assign Q = A | B | C | D | E | F | G | H | I | J;
endmodule

module OR11(input A, B, C, D, E, F, G, H, I, J, K, output Q);
  assign Q = A | B | C | D | E | F | G | H | I | J | K;
endmodule

module OR12(input A, B, C, D, E, F, G, H, I, J, K, L, output Q);
  assign Q = A | B | C | D | E | F | G | H | I | J | K | L;
endmodule

module OR2I1(input A, BN, output Q);
  assign Q = A | ~BN;
endmodule

module OR2I2(input AN, BN, output Q);
  assign Q = ~AN | ~BN;
endmodule

module OR3I1(input A, B, CN, output Q);
  assign Q = A | B | ~CN;
endmodule

module OR3I2(input A, BN, CN, output Q);
  assign Q = A | ~BN | ~CN;
endmodule

module OR3I3(input AN, BN, CN, output Q);
  assign Q = ~AN | ~BN | ~CN;
endmodule

module OR4I1(input A, B, C, DN, output Q);
  assign Q = A | B | C | ~DN;
endmodule

module OR4I2(input A, B, CN, DN, output Q);
  assign Q = A | B | ~CN | ~DN;
endmodule

module OR4I3(input A, BN, CN, DN, output Q);
  assign Q = A | ~BN | ~CN | ~DN;
endmodule

module OR4I4(input AN, BN, CN, DN, output Q);
  assign Q = ~AN | ~BN | ~CN | ~DN;
endmodule

module NOR2(input A, B, output QN);
  assign NQ = ~(A | B);
endmodule

module NOR3(input A, B, C, output QN);
  assign NQ = ~(A | B | C);
endmodule

module NOR4(input A, B, C, D, output QN);
  assign NQ = ~(A | B | C | D);
endmodule

module NOR5(input A, B, C, D, E, output QN);
  assign NQ = ~(A | B | C | D | E);
endmodule

module NOR6(input A, B, C, D, E, F, output QN);
  assign NQ = ~(A | B | C | D | E | F);
endmodule

module NOR7(input A, B, C, D, E, F, G, output QN);
  assign NQ = ~(A | B | C | D | E | F | G);
endmodule

module NOR8(input A, B, C, D, E, F, G, H, output QN);
  assign NQ = ~(A | B | C | D | E | F | G | H);
endmodule

module NOR9(input A, B, C, D, E, F, G, H, I, output QN);
  assign NQ = ~(A | B | C | D | E | F | G | H | I);
endmodule

module NOR10(input A, B, C, D, E, F, G, H, I, J, output QN);
  assign NQ = ~(A | B | C | D | E | F | G | H | I | J);
endmodule

module NOR11(input A, B, C, D, E, F, G, H, I, J, K, output QN);
  assign NQ = ~(A | B | C | D | E | F | G | H | I | J | K);
endmodule

module NOR12(input A, B, C, D, E, F, G, H, I, J, K, L, output QN);
  assign NQ = ~(A | B | C | D | E | F | G | H | I | J | K | L);
endmodule

module NOR2I1(input A, BN, output Q);
  assign Q = ~(A | ~BN);
endmodule

module NOR2I2(input AN, BN, output Q);
  assign Q = ~(~AN | ~BN);
endmodule

module NOR3I1(input A, B, CN, output Q);
  assign Q = ~(A | B | ~CN);
endmodule

module NOR3I2(input A, BN, CN, output Q);
  assign Q = ~(A | ~BN | ~CN);
endmodule

module NOR3I3(input AN, BN, CN, output Q);
  assign Q = ~(~AN | ~BN | ~CN);
endmodule

module NOR4I1(input A, B, C, DN, output Q);
  assign Q = ~(A | B | C | ~DN);
endmodule

module NOR4I2(input A, B, CN, DN, output Q);
  assign Q = ~(A | B | ~CN | ~DN);
endmodule

module NOR4I3(input A, BN, CN, DN, output Q);
  assign Q = ~(A | ~BN | ~CN | ~DN);
endmodule

module NOR4I4(input AN, BN, CN, DN, output Q);
  assign Q = ~(~AN | ~BN | ~CN | ~DN);
endmodule

module MUX2(input S0, M0, M1, output Q);
  assign Q = S0 ? M1 : M0;
endmodule

module MUX4(input S0, S1, M0, M1, M2, M3, output Q);
  wire M10 = S0 ? M1 : M0;
  wire M32 = S0 ? M3 : M2;
  assign Q = S1 ? M32 : M10;
endmodule

module MUX8(input S0, S1, S2, M0, M1, M2, M3, M4, M5, M6, M7, output Q);
  wire M10 = S0 ? M1 : M0;
  wire M32 = S0 ? M3 : M2;
  wire M54 = S0 ? M5 : M4;
  wire M76 = S0 ? M7 : M6;
  wire M3210 = S1 ? M32 : M10;
  wire M7654 = S1 ? M76 : M54;
  assign Q = S2 ? M7654 : M3210;
endmodule

module XNOR2(input A, B, output Q);
  assign Q = ~(A ^ B);
endmodule

module DFF(input CLK, D, output reg Q);
  always @(posedge CLK)
    Q <= D;
endmodule

module DFFE(input CLK, CE, D, output reg Q);
  always @(posedge CLK)
    if(CE) Q <= D;
endmodule

module DFFAR(input CLK, AR, D, output reg Q);
  always @(posedge CLK, posedge AR)
    if(AR) Q <= 1'b0;
    else Q <= D;
endmodule

module DFFAS(input CLK, AS, D, output reg Q);
  always @(posedge CLK, posedge AS)
    if(AS) Q <= 1'b1;
    else Q <= D;
endmodule

module DFFARS(input CLK, AR, AS, D, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else Q <= D;
endmodule

module DFFEARS(input CLK, AR, AS, CE, D, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else if(CE) Q <= D;
endmodule

module LATCH(input EN, AR, AS, CE, D, output reg Q);
  // TODO: LATCH
endmodule

module JKFFEARS(input CLK, /*!*/AR, /*!*/AS, CE, J, K, output reg Q);
  // TODO: JKFFEARS
endmodule

module TFF(input CLK, T, output reg Q);
  always @(posedge CLK)
    Q <= Q ^ T;
endmodule

module TFFE(input CLK, CE, T, output reg Q);
  always @(posedge CLK)
    if(CE) Q <= Q ^ T;
endmodule

module TFFAR(input CLK, AR, T, output reg Q);
  always @(posedge CLK, posedge AR)
    if(AR) Q <= 1'b0;
    else Q <= Q ^ T;
endmodule

module TFFAS(input CLK, AS, T, output reg Q);
  always @(posedge CLK, posedge AS)
    if(AS) Q <= 1'b1;
    else Q <= Q ^ T;
endmodule

module TFFARS(input CLK, AR, AS, T, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else Q <= Q ^ T;
endmodule

module TFFEARS(input CLK, AR, AS, CE, T, output reg Q);
  always @(posedge CLK, posedge AR, posedge AS)
    if(AR) Q <= 1'b0;
    else if(AS) Q <= 1'b1;
    else if(CE) Q <= Q ^ T;
endmodule

module BUFTH(input A, ENA, output Q);
  assign Q = ENA ? A : 1'bz;
endmodule

module TRI(input A, ENA, output Q);
  assign Q = ENA ? A : 1'bz;
endmodule

module BIBUF(input A, EN, output Q, inout PAD);
  assign PAD = EN ? A : 1'bz;
  assign Q = PAD;
endmodule
