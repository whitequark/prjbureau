import bitarray, bitarray.util


def find_one(a, b):
    x = a ^ b
    assert x.count(1) == 1, f"{x.count(1)} bits differ: {x.search(bitarray.bitarray([1]))}"
    return x.index(1)
