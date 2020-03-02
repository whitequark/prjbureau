__all__ = ['svf_to_jed_atf1502']


def svf_to_jed_atf1502(svf_row, svf_col):
    if svf_row in range(0, 12):
        if svf_col in range(0, 80):
            return 16240 - (11 - svf_row) * 80 + (79 - svf_col)
        else:
            return # always 1
    if svf_row in range(12, 108):
        if svf_col in range(0, 80):
            return (svf_row - 12) + (79 - svf_col) * 96
        else:
            return # always 1
    if svf_row in range(128, 224):
        if svf_col in range(0, 80):
            return 7680 + (svf_row - 128) + (79 - svf_col) * 96
        else:
            return # always 1
    if svf_row in range(224, 229):
        if svf_col in range(0, 80):
            return 16320 + (svf_row - 224) + (79 - svf_col) * 5
        else:
            return 16720 + (svf_row - 224) + (85 - svf_col) * 5
    if svf_row == 256:
        return 16750 + (31 - svf_col)
    if svf_row == 512:
        return 16782 + (3 - svf_col)
    if svf_row == 768:
        return 16786 + (15 - svf_col)
    assert False


if __name__ == '__main__':
    with open('atf1502as_svf2jed.csv', 'w') as f:
        f.write('SVF ROW,SVF COL,JED\n')
        for svf_rows, svf_cols in {
            range(  0, 108): range(86),
            range(128, 229): range(86),
            (256,): range(32),
            (512,): range(4),
            (768,): range(16),
        }.items():
            for svf_row in svf_rows:
                for svf_col in svf_cols:
                    jed_bit = svf_to_jed_atf1502(svf_row, svf_col)
                    if jed_bit is None: jed_bit = 0x7fff
                    f.write('{},{},{}\n'.format(svf_row, svf_col, jed_bit))
