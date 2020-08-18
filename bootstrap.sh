#!/bin/sh -ex

root=$(dirname $0)
export PYTHONPATH=${root}
export PYTHONHASHSEED=0 # for deterministic fuzzing
export LANG=en_US.UTF-8 # for the UES fuzzer
mv -f database.json database.json.bak
for fuzzer in ${root}/fuzzers/*/fuzzer.py; do
  python3 ${fuzzer}
done
python3 -m util.genhtml
