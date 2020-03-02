from bitarray import bitarray


__all__ = ['ATF1502Bitmap']


class ATF15xxBitmap:
    count  = None # int
    layout = None # dict(range/tuple,range)

    @classmethod
    def word_size(cls, svf_row):
        for svf_rows, svf_cols in cls.layout:
            if svf_row in svf_rows:
                return len(svf_cols)
        assert False

    @classmethod
    def jed_to_svf_coords(cls, jed_index):
        raise NotImplementedError

    @classmethod
    def jed_to_svf(cls, jed_bits):
        svf_bits = {}
        for jed_index, jed_bit in enumerate(jed_bits):
            svf_index = cls.jed_to_svf_coords(jed_index)
            if svf_index is None: continue
            svf_row, svf_col = svf_index
            if svf_row not in svf_bits:
                svf_bits[svf_row] = bitarray(cls.word_size(svf_row))
                svf_bits[svf_row].setall(1)
            svf_bits[svf_row][svf_col] = jed_bit
        return svf_bits

    @classmethod
    def svf_to_jed_coords(cls, svf_row, svf_col):
        raise NotImplementedError

    @classmethod
    def svf_to_jed(cls, svf_bits):
        jed_bits = bitarray(cls.count)
        jed_bits.setall(0)
        for svf_row, svf_word in svf_bits.items():
            for svf_col, svf_bit in enumerate(svf_word):
                jed_index = cls.svf_to_jed_coords(svf_row, svf_col)
                if jed_index is None: continue
                jed_bits[jed_index] = svf_bit
        return jed_bits


class ATF1502Bitmap(ATF15xxBitmap):
    count  = 16808
    layout = {
        range(  0, 108): range(86),
        range(128, 229): range(86),
        (256,): range(32),
        (512,): range(4),
        (768,): range(16),
    }

    @classmethod
    def jed_to_svf_coords(cls, jed_index):
        if jed_index in range(    0,  7680):
            return  12 + (jed_index -     0)  % 96, 79 - (jed_index -     0) // 96
        if jed_index in range( 7680, 15360):
            return 128 + (jed_index -  7680)  % 96, 79 - (jed_index -  7680) // 96
        if jed_index in range(15360, 16320):
            return   0 + (jed_index - 15360) // 80, 79 - (jed_index - 15360)  % 80
        if jed_index in range(16320, 16720):
            return 224 + (jed_index - 16320)  %  5, 79 - (jed_index - 16320) // 5
        if jed_index in range(16720, 16750):
            return 224 + (jed_index - 16320)  %  5, 85 - (jed_index - 16320) // 5 + 80
        if jed_index in range(16750, 16782):
            return 256, 31 - (jed_index - 16750)
        if jed_index in range(16782, 16786):
            return 512,  3 - (jed_index - 16782)
        if jed_index in range(16786, 16802):
            return 768, 15 - (jed_index - 16786)
        if jed_index in range(16802, 16808):
            return # reserved
        assert False

    @classmethod
    def svf_to_jed_coords(cls, svf_row, svf_col):
        if svf_row in range(  0,  12):
            if svf_col in range(0, 80):
                return 15360 + (svf_row -   0) * 80 + (79 - svf_col)
            else:
                return # always 1
        if svf_row in range( 12, 108):
            if svf_col in range(0, 80):
                return     0 + (svf_row -  12) + (79 - svf_col) * 96
            else:
                return # always 1
        if svf_row in range(128, 224):
            if svf_col in range(0, 80):
                return  7680 + (svf_row - 128) + (79 - svf_col) * 96
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
            return 16782 + ( 3 - svf_col)
        if svf_row == 768:
            return 16786 + (15 - svf_col)
        assert False


if __name__ == '__main__':
    with open('atf1502as_svf2jed.csv', 'w') as f:
        f.write('SVF ROW,SVF COL,JED\n')
        for svf_rows, svf_cols in ATF1502Bitmap.layout.items():
            for svf_row in svf_rows:
                for svf_col in svf_cols:
                    jed_index = ATF1502Bitmap.svf_to_jed(svf_row, svf_col)
                    if jed_index is None: jed_index = 0x7fff
                    f.write('{},{},{}\n'.format(svf_row, svf_col, jed_index))

    with open('atf1502as_jed2svf.csv', 'w') as f:
        f.write('JED,SVF ROW,SVF COL\n')
        for jed_index in range(ATF1502Bitmap.count):
            svf_index = ATF1502Bitmap.jed_to_svf(jed_index)
            if svf_index is None: continue
            f.write('{},{},{}\n'.format(jed_index, *svf_index))
