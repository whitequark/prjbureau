#!/bin/sh

for pin in 42 43 44 1 2 3 5 6 7 8 10  11 12 13 14 15; do
  cat <<END >pin${pin}.v
//OPT: -device TQFP44
//PIN: CHIP "top" ASSIGNED TO TQFP44
//PIN: O : ${pin}
module top(output O);
  assign O = 1'b0;
endmodule
END
done
