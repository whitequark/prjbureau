#!/bin/sh -ex

export ROOT=$(dirname $0)
export WINEPREFIX=$HOME/.wine_atf
export FITTERDIR=$(winepath -w ${ROOT}/vendor)

NAME=$1; shift
OPTS=$(grep '//OPT:' ${NAME}.v | cut -d' ' -f2-)
yosys -p "read_verilog -lib ${ROOT}/cells.v; read_verilog ${NAME}.v" -o ${NAME}.edif
grep '//PIN:' ${NAME}.v | cut -d' ' -f2- >${NAME}.pin
wine ${FITTERDIR}\\fit1502.exe -i ${NAME}.edif -o ${NAME}.jed -strategy ifmt=edif -strategy optimize=off -strategy JTAG=off ${OPTS}
