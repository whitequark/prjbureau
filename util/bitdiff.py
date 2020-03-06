import bitarray


def describe(expected, variants):
    bitstreams = list(variants.values())
    pairwise_xor = bitarray.bitarray(bitstreams[0])
    pairwise_xor.setall(0)
    for a, b in zip(bitstreams, bitstreams[1:]):
        pairwise_xor |= a ^ b
    fuses = pairwise_xor.search(bitarray.bitarray([1]))
    assert pairwise_xor.count(1) == expected, \
           f"{pairwise_xor.count(1)} bits differ ({expected} expected): {fuses}"
    values = {
        key: sum(variant[fuse] << n for n, fuse in enumerate(fuses))
        for key, variant in variants.items()
    }
    assert len(set(values.values())) == len(values.values()), \
           f"values not unique: {values}"
    return {"fuses": fuses, "values": values}
