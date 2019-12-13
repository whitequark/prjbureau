#!/bin/sh -ex

export PYTHONPATH=$(dirname $0)
for fuzzer in $(dirname $0)/fuzzers/*/fuzzer.py; do
  python3 ${fuzzer}
done
python3 -m util.genhtml
