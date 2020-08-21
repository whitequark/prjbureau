from collections import defaultdict
import re
import os, os.path
import gzip
import json

from . import root_dir, database


def natural_sort_key(input):
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r'(\d+)', input)]


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


def write_bitmap(f, columns, rows, bitmap, fuse_range, *,
                 compact=False, link_fn=lambda fuse: f"#L{fuse}"):
    f.write(f"<table style='font-size:12px'>\n")
    f.write(f"<tr><td width='70'></td>\n")
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
                    "C":  ("#666", "#aaf"),
                    "IO": ("#666", "#faa"),
                    "FF": ("#666", "#aaf"),
                    "M":  ("#666", "#afa"),
                    "R":  ("#666", "#faa"),
                    "A":  ("#666", "#fd0"),
                }[sigil]
                f.write(f"<td align='center' width='15' "
                        f"bgcolor='{bgcolor}' style='color:{fgcolor};'>")
                if not owner:
                    f.write(f"<abbr title='{fuse}' style='text-decoration:none'>")
                else:
                    f.write(f"<abbr title='{fuse} ({', '.join(owner)})' "
                            f"style='text-decoration:none'>")
                link = link_fn(fuse)
                if link and sigil not in "?1":
                    f.write(f"<a style='color:{fgcolor}; text-decoration:none' "
                            f"href='{link}'>{sigil}</a>")
                else:
                    f.write(f"{sigil}")
                f.write(f"</abbr>")
                f.write(f"</td>\n")
                fuse += 1
            f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_option(f, option_name, option, *, anchor=True, shared_with=()):
    f.write(f"<p>Fuse combinations for option \"{option_name}\"")
    if shared_with:
        f.write(f" (shared with ")
        f.write(", ".join(f"\"{shared_option_name}\"" for shared_option_name in shared_with))
        f.write(f")")
    f.write(f":</p>")
    f.write(f"<table>\n")
    f.write(f"<tr><td width='70' height='40'></td>")
    for fuse in option["fuses"]:
        f.write(f"<th width='21'>")
        if anchor:
            f.write(f"<a name='L{fuse}'></a>")
        f.write(f"<div style='width: 12px; transform: translate(4px, 10px) rotate(315deg);'>"
                f"<span style='font-size: 11px'>{fuse}</span>"
                f"</div></th>")
    f.write(f"</tr>\n")
    values = option['values'].items()
    if len(option['fuses']) > 1:
        values = sorted(values, key=lambda i: i[0])
    for name, value in values:
        f.write(f"<tr><td align='right' height='18'>{name}</td>")
        for n_fuse in range(len(option["fuses"])):
            f.write(f"<td align='center' bgcolor='#e8e8e8'>"
                    f"{(value >> n_fuse) & 1}"
                    f"</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_mux(f, mux_name, mux, *, sort_fn=lambda x: x, active_low=True, descr="mux"):
    base = min(mux['fuses'])
    f.write(f"<p>Fuse combinations for {descr} \"{mux_name}\", relative to offset {base}:</p>")
    f.write(f"<table style='font-size:12px'>\n")
    f.write(f"<tr><td width='70'></td>")
    for fuse in mux["fuses"]:
        f.write(f"<th width='16'>"
                f"<a name='L{fuse}'></a>"
                f"<abbr title='{fuse}'>{fuse - base}</abbr></th>")
    f.write(f"</tr>\n")
    for name, value in sorted(mux['values'].items(), key=lambda item: sort_fn(item[0])):
        f.write(f"<tr><td align='right' height='18'>{name}</td>")
        for n_fuse in range(len(mux['fuses'])):
            bgcolor = '#ccc' if (value >> n_fuse) & 1 == active_low else '#afa'
            fgcolor = '#666' if (value >> n_fuse) & 1 == active_low else '#666'
            f.write(f"<td align='center' bgcolor='{bgcolor}' style='color:{fgcolor};'>"
                    f"{(value >> n_fuse) & 1}"
                    f"</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_matrix(f, muxes, *, filter_fn=lambda x: True, sort_fn=lambda x: x):
    matrix = {}
    for mux_name, mux in muxes.items():
        if 'values' not in mux: continue
        for net_name, value in mux['values'].items():
            if not filter_fn(mux_name, net_name):
                continue
            if net_name not in matrix:
                matrix[net_name] = set()
            matrix[net_name].add(mux_name)
    f.write(f"<table style='font-size:12px'>\n")
    f.write(f"<tr><td width='70' height='40'></td>")
    for mux_name in sorted(muxes, key=natural_sort_key):
        f.write(f"<th width='16'>"
                f"<div style='width: 12px; transform: translate(4px, 10px) rotate(315deg);'>"
                f"<span style='font-size: 11px'>{mux_name}</span>"
                f"</div></th>")
    f.write(f"</tr>\n")
    for net_name, cross_mux_names in sorted(matrix.items(), key=lambda item: sort_fn(item[0])):
        f.write(f"<tr><td align='right' height='18'>{net_name}</td>")
        for mux_name in sorted(muxes, key=natural_sort_key):
            if mux_name in cross_mux_names:
                f.write(f"<td align='center' bgcolor='#faa' style='color:#666'>R</td>")
            else:
                f.write(f"<td align='center' bgcolor='#ccc' style='color:#666'>-</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


def write_points(f, points, *, filter_fn=lambda x: True, sort_fn=lambda x: x,
                 link_fn=lambda x: None):
    f.write(f"<table style='font-size:12px'>\n")
    f.write(f"<tr><td width='70' height='40'></td>")
    points = {name: offset for name, offset in points.items() if filter_fn(name)}
    fuse_offsets = list(sorted(points.values()))
    for fuse_offset in fuse_offsets:
        f.write(f"<th width='16'>"
                f"<div style='width: 12px; transform: translate(4px, 10px) rotate(315deg);'>"
                f"<span style='font-size: 11px'>{fuse_offset}</span>"
                f"</div></th>")
    f.write(f"</tr>\n")
    for net_name, cross_fuse_offset in sorted(points.items(), key=lambda item: sort_fn(item[0])):
        f.write(f"<tr><td align='right' height='18'>")
        link = link_fn(net_name)
        if link is None:
            f.write(f"{net_name}")
        else:
            f.write(f"<a href='{link}'>{net_name}</a>")
        f.write(f"</td>")
        for fuse_offset in fuse_offsets:
            if fuse_offset == cross_fuse_offset:
                f.write(f"<td align='center' bgcolor='#faa' style='color:#666'>"
                        f"<a name='PTL{fuse_offset}'></a>R"
                        f"</td>")
            else:
                f.write(f"<td align='center' bgcolor='#ccc' style='color:#666'>-</td>")
        f.write(f"</tr>\n")
    f.write(f"</table>\n")


macrocell_options = {
    "pt_power":         "C",
    "pt1_mux":          "M",
    "pt2_mux":          "M",
    "pt3_mux":          "M",
    "gclr_mux":         "M",
    "pt4_mux":          "M",
    "pt4_func":         "M",
    "gclk_mux":         "M",
    "pt5_mux":          "M",
    "pt5_func":         "M",
    "xor_a_mux":        "M",
    "xor_b_mux":        "M",
    "cas_mux":          "M",
    "d_mux":            "M",
    "dfast_mux":        "M",
    "storage":          "FF",
    "fb_mux":           "M",
    "o_mux":            "M",
    "o_invert":         "M",
    "oe_mux":           "M",
    "slow_output":      "IO",
    "open_collector":   "IO",
    "pull_up":          "IO",
    "schmitt_trigger":  "IO",
    "bus_keeper":       "IO",
    "io_standard":      "IO",
    "low_power":        "C",
}


macrocell_shared_options = {
    "dfast_mux",
    "cas_mux",
}


global_options = {
    "gclr_invert":      "M",
    "gclk1_invert":     "M",
    "gclk2_invert":     "M",
    "gclk3_invert":     "M",
    "goe1_invert":      "M",
    "goe2_invert":      "M",
    "goe3_invert":      "M",
    "goe4_invert":      "M",
    "goe5_invert":      "M",
    "goe6_invert":      "M",
    "gclk1_mux":        "M",
    "gclk2_mux":        "M",
    "gclk3_mux":        "M",
    "bus_keeper":       "IO",
    "pd1_pin_func":     "C",
    "pd2_pin_func":     "C",
    "gclk1_itd":        "C",
    "gclk2_itd":        "C",
    "gclk3_itd":        "C",
    "tdi_pull_up":      "IO",
    "tms_pull_up":      "IO",
    "r_pad_term":       "IO",
    "r_pad_schmitt_trigger": "IO",
    "c1_pad_term":      "IO",
    "c1_pad_schmitt_trigger": "IO",
    "c2_pad_term":      "IO",
    "c2_pad_schmitt_trigger": "IO",
    "e1_pad_term":      "IO",
    "e1_pad_schmitt_trigger": "IO",
    "power_reset":      "C",
    "jtag_pin_func":    "M",
    "arming_switch":    "A",
}


bitmap_layout = {
    "ATF1502AS": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (32, [(False,16), (True, 32), (True, 32)]),
        "uim_mux":   (5,  [(True,  5)]),
        "goe_mux":   (5,  [(True,  5)]),
        "device":    (32, [(True, 32), (True,  4)]),
    },
    "ATF1502BE": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (27, [(True, 27) for n in range(16)] + [(False, 48)]),
        "uim_mux":   (5,  [(True,  5)]),
        "goe_mux":   (5,  [(True,  5)]),
        "device":    (32, [(True, 32), (True,  8)]),
    },
    "ATF1504AS": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (32, [(False,16), (True, 32), (True, 32)]),
        "uim_mux":   (9,  [(True,  9)]),
        "goe_mux":   (9,  [(True,  9)]),
        "device":    (32, [(True, 32), (True,  4)]),
    },
    "ATF1504BE": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (27, [(True, 27) for n in range(16)] + [(False, 48)]),
        "uim_mux":   (9,  [(True, 9)]),
        "goe_mux":   (9,  [(True, 9)]),
        "device":    (32, [(True, 32), (True,  8)]),
    },
    "ATF1508AS": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (32, [(False,16), (True, 32), (True, 32)]),
        "uim_mux":   (27, [(True, 27)]),
        "goe_mux":   (27, [(True, 27)]),
        "device":    (32, [(True, 32), (True,  4)]),
    },
    "ATF1508BE": {
        "pterm":     (40, [(True, 16), (True, 40), (True, 40)]),
        "macrocell": (27, [(True, 27) for n in range(16)] + [(False, 48)]),
        "uim_mux":   (27, [(True, 27)]),
        "goe_mux":   (27, [(True, 27)]),
        "device":    (32, [(True, 32), (True,  8)]),
    },
}


def update_fuse(bitmap, fuse, sigil, *, owner=None, conflict=True):
    if fuse in bitmap:
        old_sigil, old_owners = bitmap[fuse]
        if owner and old_owners:
            if conflict:
                bitmap[fuse] = ('!', (*old_owners, owner))
            else:
                assert old_sigil == sigil
                bitmap[fuse] = (old_sigil, (*old_owners, owner))
        else:
            bitmap[fuse] = ('!', None)
        return 0
    bitmap[fuse] = (sigil, (owner,))
    return 1


def update_option_bitmap(bitmap, option, sigil, *, owner=None, conflict=True):
    count = 0
    for n_fuse, fuse in enumerate(option['fuses']):
        if len(option['fuses']) > 1:
            fuse_owner = f"{owner}.{n_fuse}"
        else:
            fuse_owner = owner
        count += update_fuse(bitmap, fuse, sigil, owner=owner, conflict=conflict)
    return count


def update_macrocell_bitmap(bitmap, macrocell_name, macrocell, *, override=None):
    count = 0
    for option_name, sigil in macrocell_options.items():
        if option_name in macrocell_shared_options or option_name not in macrocell:
            continue
        count += update_option_bitmap(bitmap, macrocell[option_name], override or sigil,
            owner=f"{macrocell_name}.{option_name}")
    for option_name, sigil in macrocell_options.items():
        if option_name not in macrocell_shared_options or option_name not in macrocell:
            continue
        count += update_option_bitmap(bitmap, macrocell[option_name], override or sigil,
            owner=f"{macrocell_name}.{option_name}",
            conflict=False)
    return count


def update_onehot_bitmap(bitmap, option_name, option, sigil, *, active_low=True):
    count = 0
    if 'fuses' not in option:
        return 0
    for n_fuse, fuse in enumerate(option['fuses']):
        for key, value in option['values'].items():
            if (~value if active_low else value) & (1 << n_fuse):
                count += update_fuse(bitmap, fuse, sigil, owner=f"{option_name}.{key}")
    return count


def update_pterm_bitmap(bitmap, pterm_name, pterm, xpoints, *, override=None):
    count = 0
    if pterm is None:
        return count
    fuse_range = range(*pterm)
    for fuse in fuse_range:
        fuse_offset = fuse - fuse_range.start
        if override or fuse_offset in xpoints:
            if fuse_offset in xpoints:
                fuse_owner = f"{pterm_name}.{xpoints[fuse_offset]}"
            else:
                fuse_owner = f"{pterm_name}"
            count += update_fuse(bitmap, fuse, override or 'R', owner=fuse_owner)
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
            shared_with = []
            for other_option_name in macrocell_options:
                if other_option_name not in macrocell or other_option_name == option_name:
                    continue
                if (set(macrocell[option_name]['fuses']) &
                        set(macrocell[other_option_name]['fuses'])):
                    shared_with.append(other_option_name)
            write_option(f, option_name, macrocell[option_name],
                         anchor=option_name not in macrocell_shared_options,
                         shared_with=shared_with)


def write_pterms(f, device_name, device, block_name):
    write_header(f, device_name, f"Logic Block {block_name} Product Terms")

    blocks = device['blocks']
    pterms_fuse_range = range(*device['ranges']['pterms'])

    xpoints = {}
    for point_net, point_fuse in blocks[block_name]['pterm_points'].items():
        assert point_fuse not in xpoints
        xpoints[point_fuse] = point_net

    bitmap = {}

    total_fuse_count = 0
    for macrocell_name in blocks[block_name]['macrocells']:
        macrocell = device['macrocells'][macrocell_name]
        for pterm_name, pterm in macrocell['pterm_ranges'].items():
            total_fuse_count += update_pterm_bitmap(bitmap, f"{macrocell_name}.{pterm_name}",
                                                    pterm, xpoints)

    for other_block_name, other_block in blocks.items():
        if block_name == other_block_name:
            continue

        other_xpoints = {}
        for point_net, point_fuse in blocks[other_block_name]['pterm_points'].items():
            assert point_fuse not in other_xpoints
            other_xpoints[point_fuse] = point_net

        other_macrocell_names = blocks[other_block_name]['macrocells']
        for other_macrocell_name in other_macrocell_names:
            other_macrocell = device['macrocells'][other_macrocell_name]
            for other_pterm_name, other_pterm in other_macrocell['pterm_ranges'].items():
                update_pterm_bitmap(bitmap, f"{other_macrocell_name}.{other_pterm_name}",
                                    other_pterm, other_xpoints, override='-')

    pterm_links = [f"<a href='#{macrocell_name}.{pterm_name}'>{macrocell_name}.{pterm_name}</a>"
                   for macrocell_name in blocks[block_name]['macrocells']
                   for pterm_name in device['macrocells'][macrocell_name]['pterm_ranges']]
    write_section(f, "Product Term Array Configuration Bitmap",
        f"Logic block {block_name} uses {total_fuse_count} (known) fuses within range "
        f"{pterms_fuse_range.start}..{pterms_fuse_range.stop} for product terms "
        f"{', '.join(pterm_links)}.")
    f.write(f"<p>They have a <a href='#PT'>common configuration bitmap</a>.</p>")
    pterm_size = sum(size for _, size in bitmap_layout[device_name]['pterm'][1])
    write_bitmap(f, *bitmap_layout[device_name]['pterm'], bitmap, pterms_fuse_range,
                 link_fn=lambda fuse: f"#PTL{fuse % pterm_size}")

    bitmap = {}
    pterm_fuse_count = 0
    for point_net, point_fuse in blocks[block_name]['pterm_points'].items():
        pterm_fuse_count += update_fuse(bitmap, point_fuse, 'R', owner=f"PTn.{point_net}")
    write_section(f, f"<a name='PT'></a>"
                     f"Product Term Configuration Bitmap",
        f"Logic block {block_name} product terms use the following {pterm_fuse_count} (known) "
        f"fuses for specifying inputs, relative to product term specific offset. All product "
        f"terms share the following fuse layout.")
    write_bitmap(f, *bitmap_layout[device_name]['pterm'], bitmap, range(pterm_fuse_count),
                 link_fn=lambda fuse: f"#PTL{fuse}")
    write_points(f, blocks[block_name]['pterm_points'],
                 filter_fn=lambda name: name.endswith("_FLB"), sort_fn=natural_sort_key)
    write_points(f, blocks[block_name]['pterm_points'],
                 filter_fn=lambda name: name.endswith("_P"), sort_fn=natural_sort_key,
                 link_fn=lambda name: f"uim{block_name}.html#{name[:-2]}")
    write_points(f, blocks[block_name]['pterm_points'],
                 filter_fn=lambda name: name.endswith("_N"), sort_fn=natural_sort_key,
                 link_fn=lambda name: f"uim{block_name}.html#{name[:-2]}")

    for macrocell_name in blocks[block_name]['macrocells']:
        for pterm_name, pterm in device['macrocells'][macrocell_name]['pterm_ranges'].items():
            if pterm is None: continue
            pterm_fuse_range = range(*pterm)
            write_section(f, f"<a name='{macrocell_name}.{pterm_name}'></a>"
                             f"Macrocell {macrocell_name} Product Term {pterm_name} Fuses",
                f"Macrocell {macrocell_name} product term {pterm_name} uses fuses within range "
                f"{pterm_fuse_range.start}..{pterm_fuse_range.stop}. "
                f"See the <a href='#PT'>common configuration bitmap</a> for details.")


def write_uim(f, device_name, device, block_name):
    write_header(f, device_name, f"Logic Block {block_name} Interconnect Muxes")

    blocks = device['blocks']
    block_uim_muxes = {uim_name: device['uim_muxes'][uim_name]
                       for uim_name in blocks[block_name]['uim_muxes']}
    uim_fuse_range = range(*device['ranges']['uim_muxes'])

    bitmap = {}
    total_fuse_count = 0
    for mux_name, mux in block_uim_muxes.items():
        total_fuse_count += update_onehot_bitmap(bitmap, mux_name, mux, 'R')

    for other_block_name, other_block in blocks.items():
        if block_name == other_block_name:
            continue

        other_mux_names = blocks[other_block_name]['uim_muxes']
        for other_mux_name in other_mux_names:
            update_onehot_bitmap(bitmap, other_mux_names, device['uim_muxes'][other_mux_name], '-')

    mux_links = [f"<a href='#{name}'>{name}</a>"
                 for name in sorted(block_uim_muxes, key=natural_sort_key)]
    write_section(f, "Interconnect Mux Configuration Bitmap",
        f"Logic block {block_name} uses {total_fuse_count} (known) fuses within range "
        f"{uim_fuse_range.start}..{uim_fuse_range.stop} for interconnect muxes "
        f"{', '.join(mux_links)}.")
    write_bitmap(f, *bitmap_layout[device_name]['uim_mux'], bitmap, uim_fuse_range)

    def filter_fn(mux_name, net_name):
        return net_name not in ('GND1', 'GND0')

    def sort_fn(net_name):
        if net_name.endswith('_FB'): # gross.
            return int(net_name[2:-3])
        if net_name.startswith('M') and net_name.endswith('_PAD'):
            return int(net_name[1:-4])
        return {'GND1':-5,'GND0':-4,'R_PAD':-3,'C1_PAD':-2,'C2_PAD':-1,'E1_PAD':0}[net_name]

    write_section(f, "Interconnect Mux Connectivity",
        f"Interconnect muxes provide the following possible (known) connection points.")
    write_matrix(f, block_uim_muxes, filter_fn=filter_fn, sort_fn=sort_fn)

    for mux_name, mux in sorted(block_uim_muxes.items(),
                                key=lambda x: natural_sort_key(x[0])):
        if 'fuses' not in mux:
            continue
        bitmap = {}
        mux_fuse_count = update_onehot_bitmap(bitmap, mux_name, mux, 'R')
        write_section(f, f"<a name='{mux_name}'></a>Interconnect Mux {mux_name} Fuses",
            f"Interconnect mux {mux_name} uses the following {mux_fuse_count} (known) fuses "
            f"for configuration.")
        write_bitmap(f, *bitmap_layout[device_name]['uim_mux'], bitmap, uim_fuse_range,
                     compact=True)
        write_mux(f, mux_name, mux, sort_fn=sort_fn)


def write_goe(f, device_name, device):
    write_header(f, device_name, f"Global OE Muxes")

    goe_fuse_range = range(*device['ranges']['goe_muxes'])

    bitmap = {}
    total_fuse_count = 0
    for mux_name, mux in device['goe_muxes'].items():
        total_fuse_count += update_onehot_bitmap(bitmap, mux_name, mux, 'R')

    mux_links = [f"<a href='#{name}'>{name}</a>"
                 for name in sorted(device['goe_muxes'], key=natural_sort_key)]
    write_section(f, "Global OE Mux Configuration Bitmap",
        f"Device uses {total_fuse_count} (known) fuses within range "
        f"{goe_fuse_range.start}..{goe_fuse_range.stop} for global OE muxes "
        f"{', '.join(mux_links)}.")
    write_bitmap(f, *bitmap_layout[device_name]['goe_mux'], bitmap, goe_fuse_range)

    def filter_fn(mux_name, net_name):
        return net_name not in ('GND1', 'GND0')

    def sort_fn(net_name):
        if net_name.endswith('_FB'): # gross.
            return int(net_name[2:-3])
        if net_name.startswith('M') and net_name.endswith('_PAD'):
            return int(net_name[1:-4])
        return {'GND1':-5,'GND0':-4,'R_PAD':-3,'C1_PAD':-2,'C2_PAD':-1,'E1_PAD':0}[net_name]

    write_section(f, "Global OE Mux Connectivity",
        f"Global OE muxes provide the following possible (known) connection points.")
    write_matrix(f, device['goe_muxes'], filter_fn=filter_fn, sort_fn=sort_fn)

    for mux_name, mux in sorted(device['goe_muxes'].items(),
                                key=lambda x: natural_sort_key(x[0])):
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


def write_config(f, device_name, device):
    fuse_range = range(*device['ranges']['config'])

    bitmap = {}
    total_fuse_count = 0
    for option_name, option in device['config'].items():
        total_fuse_count += update_option_bitmap(bitmap, option, global_options[option_name],
                                                 owner=f"CFG.{option_name}")

    write_section(f, "Device Configuration Bitmap",
        f"Device uses {total_fuse_count} (known) fuses within range "
        f"{fuse_range.start}..{fuse_range.stop} for global feature and JTAG configuration.")
    write_bitmap(f, *bitmap_layout[device_name]['device'],
                 bitmap, fuse_range)

    for option_name, option in device['config'].items():
        write_option(f, option_name, option)


def write_user(f, device_name, device):
    fuse_range = range(*device['ranges']['user'])

    bitmap = {}
    total_fuse_count = 0
    for byte_index, user_byte in enumerate(device['user']):
        total_fuse_count += update_onehot_bitmap(
            bitmap, f"USR{byte_index}", user_byte, 'C', active_low=False)

    write_section(f, "User Signature Bitmap",
        f"Device uses {total_fuse_count} (known) fuses within range "
        f"{fuse_range.start}..{fuse_range.stop} for user signature.")
    write_bitmap(f, len(fuse_range), [(True, len(fuse_range))],
                 bitmap, fuse_range)

    for byte_index, user_byte in enumerate(device['user']):
        bitmap = {}
        fuse_count = update_onehot_bitmap(
            bitmap, f"USR{byte_index}", user_byte, 'C', active_low=False)

        for other_byte_index, other_sig in enumerate(device['user']):
            if byte_index != other_byte_index:
                update_onehot_bitmap(
                    bitmap, f"USR{other_byte_index}", other_sig, '-', active_low=False)

        write_section(f, f"<a name='USR{byte_index}'></a>User Signature Byte {byte_index} Fuses",
            f"User signature byte {byte_index} uses the following {fuse_count} (known) fuses "
            f"for configuration.")
        write_bitmap(f, len(fuse_range), [(True, len(fuse_range))],
                     bitmap, fuse_range, compact=True)
        write_mux(f, f"{byte_index}", user_byte, active_low=False, descr="byte")


def write_pins(f, device_name, device):
    write_header(f, device_name, f"Pinout")

    f.write(f"<p>Device {device_name} is available in packages "
            f"{', '.join(device['pins'])}.</p>")

    columns = [
        'Macrocell', 'Logic Block', 'Special Function',
        'Device Pad', *[f"{package} Pin" for package in device['pins']],
    ]
    rows_by_pad = defaultdict(lambda: {})

    for macrocell_name, macrocell in device['macrocells'].items():
        row = rows_by_pad[macrocell['pad']]
        row['Macrocell'] = f"<a href='mc{macrocell['block']}.html#{macrocell_name}'>" \
                           f"{macrocell_name}</a>"
        row['Logic Block'] = f"<a href='mc{macrocell['block']}.html'>{macrocell['block']}</a>"
        row['Device Pad'] = macrocell['pad']

    for special_name, special_macrocell_name in device['specials'].items():
        row = rows_by_pad[device['macrocells'][special_macrocell_name]['pad']]
        if 'Special Function' not in row:
            row['Special Function'] = f"<b>{special_name}</b>"
        else:
            row['Special Function'] += f", <b>{special_name}</b>"

    for pad, special_func in (
        ('C1', '<b>GCLK1</b>'),
        ('E1', '<b>OE1</b>'),
        ('R',  '<b>GCLR</b>'),
        ('C2', '<b>OE2</b>, <b>GCLK2</b>'),
    ):
        rows_by_pad[pad] = {
            'Macrocell': '—',
            'Logic Block': '—',
            'Device Pad': pad,
            'Special Function': special_func,
        }

    for package, pinout in device['pins'].items():
        for pad, row in rows_by_pad.items():
            row[f"{package} Pin"] = pinout.get(pad, '—')

    for row in rows_by_pad.values():
        if 'Special Function' not in row: continue
        row['Special Function'] = re.sub(r"(GCLK\d</b>)", r"\1†", row['Special Function'])

    first_package = next(iter(device['pins']))
    rows = list(sorted(rows_by_pad.values(),
                       key=lambda row: natural_sort_key(row[f"{first_package} Pin"])))
    f.write(f"<table><tr>")
    for column in columns:
        f.write(f"<th bgcolor='#ddd' style='color:#333; max-width: 90px'>{column}</th>")
    f.write(f"</tr>")
    for row in rows:
        f.write(f"<tr>")
        for column in columns:
            f.write(f"<td align='center' style='border-bottom: 1px solid #ddd'>"
                    f"{row.get(column, '')}</td>")
        f.write(f"</tr>")
    f.write(f"</table>")

    f.write(f"<p>† Any of the three on-chip global clock networks <b>GCLK1</b>, <b>GCLK2</b>, "
            f"and <b>GCLK3</b> can be driven by any of the three pads with global clock input "
            f"capability, <b>C1</b>, <b>C2</b>, and <b>{device['specials']['GCLK3']}</b>. "
            f"The name of the special function merely illustrates the typical application.</p>")


devices = database.load()
docs_dir = os.path.join(root_dir, "docs", "database")
with open(os.path.join(docs_dir, f"index.html"), "w") as fi:
    write_header(fi)

    with gzip.open(os.path.join(docs_dir, "database.json.gz"), "wt") as fj:
        json.dump(devices, fj, indent=2)
    fi.write(f"<p>This HTML documentation has been automatically generated from a structured chip "
             f"database. The complete chip database can be "
             f"<a href='database.json.gz'>downloaded as a JSON file</a>.</p>")

    fi.write(f"<p>Device index:</p>\n")
    fi.write(f"<ul>\n")
    for device_name, device in devices.items():
        dev_docs_dir = os.path.join(docs_dir, device_name)
        os.makedirs(dev_docs_dir, exist_ok=True)

        fi.write(f"<li><a href='{device_name}/index.html'>"
                 f"Device {device_name}</a></li>\n")

        with open(os.path.join(dev_docs_dir, f"index.html"), "w") as fd:
            write_header(fd, f"{device_name}")

            with gzip.open(os.path.join(dev_docs_dir,
                                        f"database-{device_name}.json.gz"), "wt") as fj:
                json.dump({device_name: device}, fj, indent=2)
            fd.write(f"<p>This HTML documentation has been automatically generated from "
                     f"a structured chip database. A subset of the chip database that describes "
                     f"only {device_name} can be "
                     f"<a href='database-{device_name}.json.gz'>downloaded as a JSON file</a>."
                     f"</p>")

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

                fd.write(f"<li><a href='uim{block_name}.html'>"
                         f"Logic Block {block_name} Interconnect Muxes</a></li>\n")
                with open(os.path.join(dev_docs_dir, f"uim{block_name}.html"), "w") as fb:
                    write_uim(fb, device_name, device, block_name)

            fd.write(f"<li><a href='goe.html'>Global OE Muxes</a></li>\n")
            with open(os.path.join(dev_docs_dir, f"goe.html"), "w") as fg:
                write_goe(fg, device_name, device)

            fd.write(f"<li><a href='cfg.html'>Global Configuration</a></li>\n")
            with open(os.path.join(dev_docs_dir, f"cfg.html"), "w") as fg:
                write_header(fg, device_name, f"Global Configuration")

                write_config(fg, device_name, device)
                write_user(fg, device_name, device)

            fd.write(f"<li><a href='pins.html'>Pinout</a></li>\n")
            with open(os.path.join(dev_docs_dir, f"pins.html"), "w") as fg:
                write_pins(fg, device_name, device)

            fd.write(f"</ul>\n")

    fi.write(f"</ul>\n")
