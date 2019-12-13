import os, os.path

from . import root_dir, database


def write_header(f, title=""):
    if title:
        title = f" — {title}"
    f.write(f"<title>Project Bureau{title}</title>\n")
    f.write(f"<h1>Project Bureau{title}</h1>\n")
    f.write(f"<i><a href='https://github.com/whitequark/prjbureau'>Project Bureau</a> "
            f"aims at documenting the bitstream format of Microchip ATF150x CPLDs. "
            f"This is a work in progress.</i>\n")


def write_section(f, title, description):
    f.write(f"<h2>{title}</h2>\n")
    f.write(f"<p>{description}</p>\n")


def write_bitmap(f, columns, rows, bitmap, base):
    f.write(f"<table style='font-size:11px'>\n")
    f.write(f"<tr>\n")
    column = 0
    for width in columns:
        f.write(f"<td></td>\n")
        for _ in range(width):
            f.write(f"<td align='center' width='15'>{column}</td>\n")
            column += 1
    f.write(f"</tr>\n")
    offset = base
    for row in rows:
        f.write(f"<tr>\n")
        for row_name, width in row:
            f.write(f"<td align='right'>{row_name}</td>\n")
            for _ in range(width):
                sigil = bitmap.get(offset, "1" if not row_name else "?")
                fgcolor, bgcolor = {
                    "?": ("#666", "#aaa"), # unfuzzed
                    "1": ("#aaa", "#fff"), # always 1
                    "-": ("#aaa", "#fff"), # out of scope
                    "IO": ("#666", "#faa"),
                    "FF": ("#666", "#aaf"),
                }[sigil]
                f.write(f"<td align='center' width='15' "
                        f"bgcolor='{bgcolor}' style='color:{fgcolor};'>")
                f.write(f"<abbr title='+{offset - base}' style='text-decoration:none'>")
                if sigil not in "?1":
                    f.write(f"<a style='color:{fgcolor}; text-decoration:none' "
                            f"href='#L{offset}'>{sigil}</a>")
                else:
                    f.write(f"{sigil}")
                f.write(f"</abbr>")
                f.write(f"</td>\n")
                offset += 1
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_option(f, option_name, option, base):
    f.write(f"<p>Fuse combinations for option \"{option_name}\":</p>")
    f.write(f"<table border='1'>\n")
    f.write(f"<tr><td width='60'></td>")
    for fuse in option["fuses"]:
        f.write(f"<th width='40' style='font-size: 13px'>"
                f"<a name='L{fuse}'></a>+{fuse - base}</th>")
    f.write(f"</tr>\n")
    for name, value in option["values"].items():
        f.write(f"<tr><td align='right'>{name}</td>")
        for n_fuse in range(len(option["fuses"])):
            f.write(f"<td align='center'>{(value >> n_fuse) & 1}</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


macrocell_options = {
    "slew_rate": "IO",
    "open_collector": "IO",
    "low_power": "IO",
    "pull_up": "IO",
    "schmitt_trigger": "IO",
    "bus_keeper": "IO",
    "ff_type": "FF",
}


macrocell_bitmap_layout = {
    "ATF1502AS": (
        (16,16), [
            [("",16)],[("S16",16),("S12",16)],[("S14",16),("S11",16)],
            [("",16)],[("S9", 16),("S6", 16)],[("S13",16),("S10",16)],
            [("",16)],[("S20",16),("S18",16)],[("S8", 16),("S21",16)],
            [("",16)],[("S7", 16),("S19",16)],[("S22",16),("S5", 16)],
            [("",16)],[("S23",16),("S4", 16)],[("S3", 16),("S15",16)],
            [("",16)],[("S0", 16),("S1", 16)],[("S17",16),("S2", 16)],
        ]
    ),
    "ATF1502BE": (
        (27,), [
            *[[(f"MC+{1+n}",27)] for n in range(16)[::-1]],
            [("",48)],
        ]
    ),
}


def update_macrocell_bitmap(bitmap, macrocell, override=None):
    for option_name, sigil in macrocell_options.items():
        if option_name not in macrocell:
            continue
        for fuse in macrocell[option_name]["fuses"]:
            bitmap[fuse] = override or sigil


def write_block(f, device_name, device, block_name):
    write_header(f, f"{device_name} Logic Block {block_name}")

    block = device["blocks"][block_name]
    macrocell_fuses = range(*block["macrocell_fuses"])

    macrocell_links = [f"<a href='#{name}'>{name}</a>" for name in block["macrocells"]]
    write_section(f, "Macrocell Configuration Bitmap",
        f"Logic block {block_name} uses {len(macrocell_fuses)} fuses at "
        f"{macrocell_fuses.start}..{macrocell_fuses.stop} for macrocells "
        f"{', '.join(macrocell_links)}.")

    macrocells = {name: device["macrocells"][name] for name in block["macrocells"]}
    bitmap = {}
    for macrocell in macrocells.values():
        update_macrocell_bitmap(bitmap, macrocell)
    write_bitmap(f, *macrocell_bitmap_layout[device_name], bitmap, base=macrocell_fuses.start)

    for macrocell_name, macrocell in macrocells.items():
        write_section(f, f"<a name='{macrocell_name}'></a>Macrocell {macrocell_name} Fuses",
            f"Macrocell {macrocell_name} uses the following fuses for configuration, "
            f"relative to offset {macrocell_fuses.start}.")

        bitmap = {}
        update_macrocell_bitmap(bitmap, macrocell)
        for other_macrocell_name, other_macrocell in macrocells.items():
            if macrocell_name == other_macrocell_name:
                continue
            update_macrocell_bitmap(bitmap, other_macrocell, override="-")
        write_bitmap(f, *macrocell_bitmap_layout[device_name], bitmap, base=macrocell_fuses.start)

        for option_name in macrocell_options:
            if option_name not in macrocell:
                continue
            write_option(f, option_name, macrocell[option_name], base=macrocell_fuses.start)


docs_dir = os.path.join(root_dir, "docs")
with open(os.path.join(docs_dir, f"index.html"), "w") as fi:
    write_header(fi)
    fi.write(f"<p>Device index:</p>\n")
    fi.write(f"<ul>\n")

    for device_name, device in database.load().items():
        dev_docs_dir = os.path.join(docs_dir, device_name)
        os.makedirs(dev_docs_dir, exist_ok=True)

        fi.write(f"<li><a href='{device_name}/index.html'>"
                 f"Device {device_name}</a></li>\n")

        with open(os.path.join(dev_docs_dir, f"index.html"), "w") as fd:
            write_header(fd, f"{device_name}")
            fd.write(f"<p>Device {device_name} documentation index:</p>\n")
            fd.write(f"<ul>\n")

            for block_name in device["blocks"]:
                fd.write(f"<li><a href='block{block_name}.html'>"
                         f"Logic Block {block_name}</a></li>\n")

                with open(os.path.join(dev_docs_dir, f"block{block_name}.html"), "w") as fb:
                    write_block(fb, device_name, device, block_name)

            fd.write(f"</ul>\n")

    fi.write(f"</ul>\n")
