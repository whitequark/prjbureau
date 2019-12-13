import os, os.path

from . import root_dir, database


def write_header(f, title):
    f.write(f"<title>Project Bureau — {title}</title>\n")
    f.write(f"<h1>Project Bureau — {title}</h1>\n")
    f.write(f"<i><a href='https://github.com/whitequark/prjbureau'>Project Bureau</a> "
            f"aims at documenting the bitstream format of Microchip ATF150x CPLDs. "
            f"This is a work in progress.</i>\n")


def write_section(f, title, description):
    f.write(f"<h2>{title}</h2>\n")
    f.write(f"<p>{description}</p>\n")


def write_bitmap(f, columns, rows, start, bitmap):
    f.write(f"<table style='font-size:11px'>\n")
    f.write(f"<tr>\n")
    column = 0
    for width in columns:
        f.write(f"<td></td>\n")
        for _ in range(width):
            f.write(f"<td align='center' width='15'>{column}</td>\n")
            column += 1
    f.write(f"</tr>\n")
    offset = start
    for row in rows:
        f.write(f"<tr>\n")
        for row_name, width in row:
            f.write(f"<td align='right'>{row_name}</td>\n")
            for _ in range(width):
                sigil = bitmap.get(offset, "1" if not row_name else "?")
                fgcolor, bgcolor = {
                    "1": ("#aaa", "#fff"),
                    "?": ("#666", "#aaa"),
                    "IO": ("#666", "#faa"),
                    "FF": ("#666", "#aaf"),
                }[sigil]
                f.write(f"<td align='center' bgcolor='{bgcolor}' style='color:{fgcolor};'>")
                f.write(f"<abbr title='+{offset - start}' style='text-decoration:none'>")
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


def write_options(f, entities, names, offset):
    f.write(f"<table border='1'>\n")
    f.write(f"<tr><td></td>\n")
    for entity_name in entities:
        f.write(f"<th width='40' style='font-size:13px'>{entity_name}</th>")
    f.write(f"</tr>")
    for name in names:
        f.write(f"<tr><td align='right'>{name}</td>\n")
        for entity in entities.values():
            f.write(f"<td align='center'>"
                    f"<a name='L{entity[name + '_fuse']}'></a>"
                    f"{entity[name + '_fuse'] - offset}"
                    f"</td>")
        f.write(f"</tr>")
    f.write(f"</table>\n")


def write_block(f, device, block_name, bitmap):
    block = device["blocks"][block_name]
    macrocell_fuses = range(*block["macrocell_fuses"])

    write_section(f, "Macrocell Configuration Bitmap",
        f"Logic block {block_name} uses {len(macrocell_fuses)} fuses at "
        f"{macrocell_fuses.start}..{macrocell_fuses.stop} for macrocells "
        f"{', '.join(block['macrocells'])}.")

    write_bitmap(f, (16,16), [
        [("",16)],[("S16",16),("S12",16)],[("S14",16),("S11",16)],
        [("",16)],[("S9",16) ,("S6",16)],[("S13",16),("S10",16)],
        [("",16)],[("S20",16),("S18",16)],[("S8",16) ,("S21",16)],
        [("",16)],[("S7",16) ,("S19",16)],[("S22",16),("S5",16)],
        [("",16)],[("S23",16),("S4",16)],[("S3",16) ,("S15",16)],
        [("",16)],[("S0",16) ,("S1",16)],[("S17",16),("S2",16)],
    ], start=macrocell_fuses.start, bitmap=bitmap)

    write_section(f, "Macrocell Option Fuses",
        f"Macrocells use the following fuses for non-routing options, starting at offset "
        f"{macrocell_fuses.start}.")

    write_options(f, {name[2:]: device["macrocells"][name] for name in block["macrocells"]},
        names=["slow", "open_collector", "toggle", "latch"],
        offset=macrocell_fuses.start)


db = database.load()
for device_name, device in db.items():
    html_dir = os.path.join(root_dir, "htmldoc", device_name)
    os.makedirs(html_dir, exist_ok=True)

    bitmap = {}
    for macrocell_name, macrocell in device["macrocells"].items():
        bitmap[macrocell["slow_fuse"]] = "IO"
        bitmap[macrocell["open_collector_fuse"]] = "IO"
        bitmap[macrocell["toggle_fuse"]] = "FF"
        bitmap[macrocell["latch_fuse"]] = "FF"

    for block_name in device["blocks"]:
        with open(os.path.join(html_dir, f"block{block_name}.html"), "w") as f:
            write_header(f, f"{device_name} Logic Block {block_name}")
            write_block(f, device, block_name, bitmap)
