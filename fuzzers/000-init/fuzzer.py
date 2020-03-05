from util import database


def macrocells(count):
    return {
        "macrocells": {
            f"MC{1+mi}": {
                "pad": f"M{1+mi}"
            } for mi in range(32)
        }
    }


def globals(gclk3):
    return {
        "clocks": {
            "1": {"pad": "C1"},
            "2": {"pad": "C2"},
            "3": {"pad": "M17"},
        },
        "enables": {
            "1": {"pad": "E1"},
            "2": {"pad": "C2"},
        },
        "clear": {"pad": "R"},
    }


def pins(Mn, C1, E1, R, C2):
    return {
        **{
            f"M{1+mi}": pin
            for mi, pin in enumerate(Mn.split())
        },
        **{
            "C1": C1,
            "E1": E1,
            "R":  R,
            "C2": C2,
        }
    }


def atf1502():
    return {
        "blocks": {
            bn: {
                "macrocell_fuse_range": [15360+480*bi, 15360+480*(bi+1)],
                "macrocells": [f"MC{1+16*bi+mi}" for mi in range(16)],
            } for bi, bn in enumerate("AB")
        },
        **macrocells(32),
        "goe_muxes": {
            **{
                f"GOE{6-n}": {
                    "fuses": list(range(16720+5*n, 16720+5*(n+1)))
                } for n in reversed(range(6))
            }
        },
        **globals(gclk3="M17"),
        "pins": {
            "TQFP44": pins(
                Mn="42 43 44  1  2  3  5  6  7  8 10 11 12 13 14 15 "
                   "35 34 33 32 31 30 28 27 26 25 23 22 21 20 19 18 ",
                C1="37",
                E1="38",
                R ="39",
                C2="40"),
        }
    }


database.save({
    "ATF1502AS": atf1502(),
    "ATF1502BE": atf1502(),
})
