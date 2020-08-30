from collections import defaultdict
from bitarray import bitarray


def _pairwise_difference(bitstreams, expected, *, scope):
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
           f"{pairwise_xor.count(1)} fuses differ ({expected} expected): {fuses}"
    return fuses


def describe(expected, variants, *, scope=None):
    bitstreams = list(variants.values())
    fuses = _pairwise_difference(bitstreams, expected, scope=scope)

    values = {
        key: sum(variant[fuse] << n for n, fuse in enumerate(fuses))
        for key, variant in sorted(variants.items())
    }
    assert len(set(values.values())) == len(values.values()), \
           f"values not unique: {values}"
    return {"fuses": fuses, "values": values}


def correlate(expected, variants, *, scope=None):
    bitstreams = [bitstream for mapping, bitstream in variants]
    fuses = _pairwise_difference(bitstreams, sum(expected.values()), scope=scope)

    lattice = defaultdict(lambda: set())
    for mapping, bitstream in variants:
        for option_name, key in mapping.items():
            assert option_name in expected
            for fuse in fuses:
                fuse_bit_set = lattice[(option_name, key, fuse)]
                fuse_bit_set.add(bitstream[fuse] & 1)

    matrix = {fuse: set(expected) for fuse in fuses}
    for (option_name, key, fuse), fuse_bit_set in lattice.items():
        if len(fuse_bit_set) > 1:
            # If we've observed this fuse take two different values for the same option-key
            # pair, this fuse is definitely not a part of this option.
            matrix[fuse].discard(option_name)
    assert all(len(possible) == 1 for fuse, possible in matrix.items()), \
           f"{len(len(possible) != 1 for fuse, possible in matrix.items())} fuses ambiguous: " \
           f"{ {fuse: possible for fuse, possible in matrix.items() if len(possible != 1)} }"

    options = {}
    for option_name, option_expected in sorted(expected.items()):
        option_fuses = [fuse for fuse, fuse_options in matrix.items()
                        if fuse_options == {option_name}]
        assert len(option_fuses) == option_expected, \
               f"option {option_name}: {len(option_fuses)} fuses differ " \
               f"({option_expected} expected): {option_fuses}"
        option_values = defaultdict(lambda: 0)
        for option_n_fuse, option_fuse in enumerate(option_fuses):
            for (lattice_option_name, lattice_key, lattice_fuse), fuse_bit_set in lattice.items():
                if lattice_option_name == option_name and lattice_fuse == option_fuse:
                    assert len(fuse_bit_set) == 1, \
                           f"option {option_name}: fuse {option_fuse} ambiguous for " \
                           f"key {lattice_key}"
                    option_values[lattice_key] |= int(any(fuse_bit_set)) << option_n_fuse
        options[option_name] = {
            'fuses': option_fuses,
            'values': {key: value for key, value in sorted(option_values.items())},
        }
    return options
