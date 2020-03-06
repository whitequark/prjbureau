#!/bin/sh -ex

root=$(dirname $0)
export PYTHONPATH=${root}
for fuzzer in ${root}/fuzzers/*/fuzzer.py; do
  python3 ${fuzzer}
done
python3 -m util.genhtml
