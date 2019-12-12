#!/bin/sh -ex

export ROOT=$(dirname $0)
export WINEPREFIX=$HOME/.wine_atf
export FITTERDIR=$(winepath -w ${ROOT}/vendor)

NAME=$1; shift
yosys -p "read_verilog -lib ${ROOT}/cells.v; read_verilog ${NAME}.v" -o ${NAME}.edif
wine ${FITTERDIR}\\fit1502.exe -i ${NAME}.edif -o ${NAME}.jed -strategy ifmt=edif $*
