import re
import os, os.path

from . import root_dir, database


def write_header(f, device_name="", category="", *, index=False):
    if not (device_name or category):
        f.write(f"<title>Project Bureau</title>\n")
        f.write(f"<h1>Project Bureau</h1>\n")
    elif not category:
        f.write(f"<title>Project Bureau — {device_name}</title>\n")
        f.write(f"<h1><a href='../index.html'>Project Bureau</a> — {device_name}</h1>\n")
    else:
        f.write(f"<title>Project Bureau — {device_name} {category}</title>\n")
        f.write(f"<h1><a href='../index.html'>Project Bureau</a> — "
                f"<a href='index.html'>{device_name}</a> {category}</h1>\n")
    f.write(f"<i>Project Bureau aims at documenting the bitstream format of "
            f"Microchip ATF15xx CPLDs. This is a work in progress. See more "
            f"in the <a href='https://github.com/whitequark/prjbureau'>repository</a></i>\n")


def write_section(f, title, description):
    f.write(f"<h2>{title}</h2>\n")
    f.write(f"<p>{description}</p>\n")


def write_bitmap(f, columns, rows, bitmap, fuse_range, *, compact=False):
    f.write(f"<table style='font-size:12px'>\n")
    f.write(f"<tr><td width='60'></td>\n")
    for column in range(columns):
        f.write(f"<td align='center' width='16'>{column}</td>\n")
    f.write(f"</tr>\n")
    fuse = fuse_range.start
    while fuse < fuse_range.stop:
        for row_active, row_width in rows:
            if compact:
                for offset in range(row_width):
                    if row_active:
                        sigil, _ = bitmap.get(fuse + offset, ("?", None))
                        if sigil not in "1?-":
                            break
                else:
                    fuse += row_width
                    continue

            f.write(f"<tr>\n")
            f.write(f"<td align='right' height='18'>{fuse}</td>\n")
            for _ in range(row_width):
                sigil, owner = bitmap.get(fuse, ("?" if row_active else "1", None))
                fgcolor, bgcolor = {
                    "?": ("#666", "#ccc"), # unfuzzed
                    "!": ("#fff", "#f00"), # conflict
                    "1": ("#aaa", "#fff"), # always 1
                    "-": ("#aaa", "#fff"), # out of scope
                    "IO": ("#666", "#faa"),
                    "FF": ("#666", "#aaf"),
                    "M":  ("#666", "#afa"),
                    "R":  ("#666", "#faa"),
                }[sigil]
                f.write(f"<td align='center' width='15' "
                        f"bgcolor='{bgcolor}' style='color:{fgcolor};'>")
                if owner is None:
                    f.write(f"<abbr title='{fuse}' style='text-decoration:none'>")
                else:
                    f.write(f"<abbr title='{fuse} ({owner})' style='text-decoration:none'>")
                if sigil not in "?1":
                    f.write(f"<a style='color:{fgcolor}; text-decoration:none' "
                            f"href='#L{fuse}'>{sigil}</a>")
                else:
                    f.write(f"{sigil}")
                f.write(f"</abbr>")
                f.write(f"</td>\n")
                fuse += 1
            f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_option(f, option_name, option):
    f.write(f"<p>Fuse combinations for option \"{option_name}\":</p>")
    f.write(f"<table>\n")
    f.write(f"<tr><td width='60' height='40'></td>")
    for fuse in option["fuses"]:
        f.write(f"<th width='21'>"
                f"<a name='L{fuse}'></a>"
                f"<div style='width: 12px; transform: translate(4px, 10px) rotate(315deg);'>"
                f"<span style='font-size: 11px'>{fuse}</span>"
                f"</div></th>")
    f.write(f"</tr>\n")
    values = option["values"].items()
    if len(option["fuses"]) > 1:
        values = sorted(values, key=lambda i: i[0])
    for name, value in values:
        f.write(f"<tr><td align='right' height='18'>{name}</td>")
        for n_fuse in range(len(option["fuses"])):
            f.write(f"<td align='center' bgcolor='#e8e8e8'>"
                    f"{(value >> n_fuse) & 1}"
                    f"</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_mux(f, mux_name, mux, *, sort_fn=lambda x: x):
    base = min(mux['fuses'])
    f.write(f"<p>Fuse combinations for mux \"{mux_name}\", relative to offset {base}:</p>")
    f.write(f"<table style='font-size:12px'>\n")
    f.write(f"<tr><td width='60'></td>")
    for fuse in mux["fuses"]:
        f.write(f"<th width='16'>"
                f"<a name='L{fuse}'></a>"
                f"<abbr title='{fuse}'>{fuse - base}</abbr></th>")
    f.write(f"</tr>\n")
    for name, value in sorted(mux['values'].items(), key=lambda item: sort_fn(item[0])):
        f.write(f"<tr><td align='right' height='18'>{name}</td>")
        for n_fuse in range(len(mux['fuses'])):
            bgcolor = '#ccc' if (value >> n_fuse) & 1 else '#afa'
            fgcolor = '#666' if (value >> n_fuse) & 1 else '#666'
            f.write(f"<td align='center' bgcolor='{bgcolor}' style='color:{fgcolor};'>"
                    f"{(value >> n_fuse) & 1}"
                    f"</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_matrix(f, muxes, *, filter_fn=lambda x: True, sort_fn=lambda x: x):
    matrix = {}
    for mux_name, mux in muxes.items():
        for net_name, value in mux['values'].items():
            if not filter_fn(mux_name, net_name):
                continue
            if net_name not in matrix:
                matrix[net_name] = set()
            matrix[net_name].add(mux_name)
    f.write(f"<table style='font-size:12px'>\n")
    f.write(f"<tr><td width='60' height='40'></td>")
    for mux_name in muxes:
        f.write(f"<th width='16'>"
                f"<div style='width: 12px; transform: translate(4px, 10px) rotate(315deg);'>"
                f"<span style='font-size: 11px'>{mux_name}</span>"
                f"</div></th>")
    f.write(f"</tr>\n")
    for net_name, xpoint_names in sorted(matrix.items(), key=lambda item: sort_fn(item[0])):
        f.write(f"<tr><td align='right' height='18'>{net_name}</td>")
        for mux_name in muxes:
            if mux_name in xpoint_names:
                f.write(f"<td align='center' bgcolor='#faa' style='color:#666'>R</td>")
            else:
                f.write(f"<td align='center' bgcolor='#ccc' style='color:#666'>-</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


macrocell_options = {
    "pt2_mux":          "M",
    "pt3_mux":          "M",
    "pt4_mux":          "M",
    "pt5_mux":          "M",
    "global_reset":     "M",
    "pt4_func":         "M",
    "global_clock":     "M",
    "pt5_func":         "M",
    "xor_a_input":      "M",
    "d_mux":            "M",
    "storage":          "FF",
    "fb_mux":           "M",
    "o_mux":            "M",
    "o_inv":            "M",
    "oe_mux":           "M",
    "slow_output":      "IO",
    "open_collector":   "IO",
    "pull_up":          "IO",
    "schmitt_trigger":  "IO",
    "bus_keeper":       "IO",
    "low_power":        "IO",
}


bitmap_layout = {
    "ATF1502AS": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (32, [(False,16), (True, 32), (True, 32)]),
        "goe_mux":   (5,  [(True,  5)]),
    },
    "ATF1502BE": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (27, [(True, 27) for n in range(16)] + [(False, 48)]),
        "goe_mux":   (5,  [(True,  5)]),
    },
    "ATF1504AS": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (32, [(False,16), (True, 32), (True, 32)]),
        "goe_mux":   (9,  [(True,  9)]),
    },
    "ATF1504BE": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (27, [(True, 27) for n in range(16)] + [(False, 48)]),
        "goe_mux":   (9,  [(True, 9)]),
    },
    "ATF1508AS": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (32, [(False,16), (True, 32), (True, 32)]),
        "goe_mux":   (27, [(True, 27)]),
    },
    "ATF1508BE": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (27, [(True, 27) for n in range(16)] + [(False, 48)]),
        "goe_mux":   (27, [(True, 27)]),
    },
}


def update_fuse(bitmap, fuse, sigil, *, owner=None):
    if fuse in bitmap:
        old_sigil, old_owner = bitmap[fuse]
        if owner and old_owner:
            bitmap[fuse] = ('!', ', '.join((owner, old_owner)))
        else:
            bitmap[fuse] = ('!', None)
        return 0
    bitmap[fuse] = (sigil, owner)
    return 1


def update_option_bitmap(bitmap, option, sigil, *, owner=None):
    count = 0
    for n_fuse, fuse in enumerate(option['fuses']):
        if len(option['fuses']) > 1:
            fuse_owner = f"{owner}.{n_fuse}"
        else:
            fuse_owner = owner
        count += update_fuse(bitmap, fuse, sigil, owner=owner)
    return count


def update_macrocell_bitmap(bitmap, macrocell_name, macrocell, *, override=None):
    count = 0
    for option_name, sigil in macrocell_options.items():
        if option_name not in macrocell:
            continue
        count += update_option_bitmap(bitmap,
            macrocell[option_name], override or sigil, owner=f"{macrocell_name}.{option_name}")
    return count


def update_onehot_bitmap(bitmap, option_name, option, sigil):
    count = 0
    if 'fuses' not in option:
        return 0
    for n_fuse, fuse in enumerate(option['fuses']):
        for key, value in option['values'].items():
            if ~value & (1 << n_fuse):
                count += update_fuse(bitmap, fuse, sigil, owner=f"{option_name}.{key}")
    return count


def update_pterm_bitmap(bitmap, pterm_name, pterm, *, override=None):
    count = 0
    if 'fuse_range' not in pterm:
        return 0
    for fuse in range(*pterm['fuse_range']):
        count += update_fuse(bitmap, fuse, override or 'R', owner=pterm_name) # stub
    return count


def write_macrocells(f, device_name, device, block_name):
    write_header(f, device_name, f"Logic Block {block_name} Macrocells")

    block = device["blocks"][block_name]
    macrocell_fuse_range = range(*device["ranges"]["macrocells"])
    macrocells = {name: device["macrocells"][name] for name in block["macrocells"]}

    bitmap = {}
    total_fuse_count = 0
    for macrocell_name, macrocell in macrocells.items():
        total_fuse_count += update_macrocell_bitmap(bitmap, macrocell_name, macrocell)
    for other_block_name, other_block in device["blocks"].items():
        if block_name == other_block_name:
            continue
        other_macrocells = {name: device["macrocells"][name] for name in other_block["macrocells"]}
        for other_macrocell_name, other_macrocell in other_macrocells.items():
            update_macrocell_bitmap(bitmap, other_macrocell_name, other_macrocell, override="-")

    macrocell_links = [f"<a href='#{name}'>{name}</a>" for name in block["macrocells"]]
    write_section(f, "Macrocell Configuration Bitmap",
        f"Logic block {block_name} uses {total_fuse_count} (known) fuses within range "
        f"{macrocell_fuse_range.start}..{macrocell_fuse_range.stop} for macrocells "
        f"{', '.join(macrocell_links)}.")
    write_bitmap(f, *bitmap_layout[device_name]['macrocell'], bitmap, macrocell_fuse_range)

    for macrocell_name, macrocell in macrocells.items():
        bitmap = {}
        macrocell_fuse_count = update_macrocell_bitmap(bitmap, macrocell_name, macrocell)
        for other_macrocell_name, other_macrocell in macrocells.items():
            if macrocell_name == other_macrocell_name:
                continue
            update_macrocell_bitmap(bitmap, other_macrocell_name, other_macrocell, override="-")

        write_section(f, f"<a name='{macrocell_name}'></a>Macrocell {macrocell_name} Fuses",
            f"Macrocell {macrocell_name} uses the following {macrocell_fuse_count} (known) fuses "
            f"for configuration.")
        write_bitmap(f, *bitmap_layout[device_name]['macrocell'], bitmap, macrocell_fuse_range,
                     compact=True)

        for option_name in macrocell_options:
            if option_name not in macrocell:
                continue
            write_option(f, option_name, macrocell[option_name])


def write_pterms(f, device_name, device, block_name):
    write_header(f, device_name, f"Logic Block {block_name} Product Terms")

    pterm_fuse_range = range(*device['ranges']['pterms'])
    macrocell_names = device['blocks'][block_name]['macrocells']
    pterms = device['pterms']

    bitmap = {}
    total_fuse_count = 0
    for macrocell_name in macrocell_names:
        for pterm_name, pterm in pterms[macrocell_name].items():
            update_pterm_bitmap(bitmap, f"{macrocell_name}.{pterm_name}", pterm)
    for other_block_name, other_block in device["blocks"].items():
        if block_name == other_block_name:
            continue
        other_macrocell_names = device['blocks'][other_block_name]['macrocells']
        for other_macrocell_name in other_macrocell_names:
            for other_pterm_name, other_pterm in pterms[other_macrocell_name].items():
                update_pterm_bitmap(bitmap, f"{other_macrocell_name}.{other_pterm_name}",
                                    other_pterm, override='-')

    pterm_links = [f"<a href='#{macrocell_name}.{pterm_name}'>{macrocell_name}.{pterm_name}</a>"
                   for macrocell_name in macrocell_names
                   for pterm_name in device['pterms'][macrocell_name]]
    write_section(f, "Product Term Configuration Bitmap",
        f"Logic block {block_name} uses {total_fuse_count} (known) fuses within range "
        f"{pterm_fuse_range.start}..{pterm_fuse_range.stop} for product terms "
        f"{', '.join(pterm_links)}.")
    write_bitmap(f, *bitmap_layout[device_name]['pterm'], bitmap, pterm_fuse_range)

    for macrocell_name in macrocell_names:
        for pterm_name, pterm in pterms[macrocell_name].items():
            bitmap = {}
            pterm_fuse_count = update_pterm_bitmap(bitmap, f"{macrocell_name}.{pterm_name}", pterm)
            write_section(f, f"<a name='{macrocell_name}.{pterm_name}'></a>"
                             f"Macrocell {macrocell_name} Product Term {pterm_name} Fuses",
                f"Macrocell {macrocell_name} product term {pterm_name} uses the following "
                f"{pterm_fuse_count} (known) fuses for configuration.")
            write_bitmap(f, *bitmap_layout[device_name]['pterm'], bitmap, pterm_fuse_range,
                         compact=True)


def write_global_oe(f, device_name, device):
    write_header(f, device_name, f"Global OE Muxes")

    goe_fuse_range = range(*device['ranges']['goe_muxes'])

    bitmap = {}
    total_fuse_count = 0
    for mux_name, mux in device['goe_muxes'].items():
        total_fuse_count += update_onehot_bitmap(bitmap, mux_name, mux, 'R')

    mux_links = [f"<a href='#{name}'>{name}</a>" for name in device['goe_muxes']]
    write_section(f, "Global OE Mux Configuration Bitmap",
        f"Device uses {total_fuse_count} (known) fuses within range "
        f"{goe_fuse_range.start}..{goe_fuse_range.stop} for global OE muxes "
        f"{', '.join(mux_links)}.")
    write_bitmap(f, *bitmap_layout[device_name]['goe_mux'], bitmap, goe_fuse_range)

    def filter_fn(mux_name, net_name):
        return net_name != 'GND'

    def sort_fn(net_name):
        if net_name.endswith("_FB"): # gross.
            return int(net_name[2:-3])
        if net_name.endswith("_PAD"):
            return int(net_name[1:-4])
        return {"GND": 0, "C1_PAD":512,"E1_PAD":513,"C2_PAD":514}[net_name]

    write_section(f, "Global OE Mux Connectivity",
        f"Global OE muxes provide the following possible (known) connection points.")
    write_matrix(f, device['goe_muxes'], filter_fn=filter_fn, sort_fn=sort_fn)

    for mux_name, mux in device['goe_muxes'].items():
        if 'fuses' not in mux:
            continue
        bitmap = {}
        mux_fuse_count = update_onehot_bitmap(bitmap, mux_name, mux, 'R')
        write_section(f, f"<a name='{mux_name}'></a>Global OE Mux {mux_name} Fuses",
            f"Global OE mux {mux_name} uses the following {mux_fuse_count} (known) fuses "
            f"for configuration.")
        write_bitmap(f, *bitmap_layout[device_name]['goe_mux'], bitmap, goe_fuse_range,
                     compact=True)
        write_mux(f, mux_name, mux, sort_fn=sort_fn)


docs_dir = os.path.join(root_dir, "docs", "genhtml")
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
                fd.write(f"<li><a href='mc{block_name}.html'>"
                         f"Logic Block {block_name} Macrocells</a></li>\n")
                with open(os.path.join(dev_docs_dir, f"mc{block_name}.html"), "w") as fb:
                    write_macrocells(fb, device_name, device, block_name)

                fd.write(f"<li><a href='pt{block_name}.html'>"
                         f"Logic Block {block_name} Product Terms</a></li>\n")
                with open(os.path.join(dev_docs_dir, f"pt{block_name}.html"), "w") as fb:
                    write_pterms(fb, device_name, device, block_name)

            fd.write(f"<li><a href='goe.html'>Global OE Muxes</a></li>\n")
            with open(os.path.join(dev_docs_dir, f"goe.html"), "w") as fg:
                write_global_oe(fg, device_name, device)

            fd.write(f"</ul>\n")

    fi.write(f"</ul>\n")
