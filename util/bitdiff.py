from bitarray import bitarray


def describe(expected, variants, *, scope=None):
    bitstreams = list(variants.values())
    pairwise_xor = bitarray(bitstreams[0], endian=bitstreams[0].endian())
    pairwise_xor.setall(0)
    for a, b in zip(bitstreams, bitstreams[1:]):
        pairwise_xor |= a ^ b
    if scope is not None:
        mask = bitarray(len(pairwise_xor), endian=pairwise_xor.endian())
        mask.setall(0)
        for n in scope:
            mask[n] = 1
        pairwise_xor &= mask
    fuses = pairwise_xor.search(bitarray([1]))
    assert pairwise_xor.count(1) == expected, \
           f"{pairwise_xor.count(1)} bits differ ({expected} expected): {fuses}"
    values = {
        key: sum(variant[fuse] << n for n, fuse in enumerate(fuses))
        for key, variant in variants.items()
    }
    assert len(set(values.values())) == len(values.values()), \
           f"values not unique: {values}"
    return {"fuses": fuses, "values": values}
