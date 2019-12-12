#!/bin/sh -ex

(cd $1 && sh gen.sh)
for file in $1/*.v; do
  rm -f work/*
  cp ${file} work/work.v
  (cd work && ../v2jed.sh work)
  cp work/work.jed ${file%.v}.jed
done
