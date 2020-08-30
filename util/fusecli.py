import argparse
import textwrap
from bitarray import bitarray
from contextlib import contextmanager

from . import database
from .fuseconv import read_jed, write_jed


db = database.load()


macrocell_options = [
    "pt_power",
    "pt1_mux",
    "pt2_mux",
    "pt3_mux",
    "gclr_mux",
    "pt4_mux",
    "pt4_func",
    "gclk_mux",
    "pt5_mux",
    "pt5_func",
    "xor_a_mux",
    "xor_b_mux",
    "cas_mux",
    "xor_invert",
    "d_mux",
    "dfast_mux",
    "reset",
    "storage",
    "fb_mux",
    "o_mux",
    "oe_mux",
    "slew_rate",
    "output_driver",
    "termination",
    "hysteresis",
    "io_standard",
    "low_power",
]


global_options = [
    "invert",
]


special_pin_options = [
    "standby_wakeup",
    "termination",
    "hysteresis",
]


config_options = [
    "arming_switch",
    "read_protection",
    "jtag_pin_func",
    "pd1_pin_func",
    "pd2_pin_func",
    "termination",
    "reset_hysteresis",
]


def extract_fuses(fuses, field, *, default=None):
    value = sum(fuses[fuse] << n_fuse for n_fuse, fuse in enumerate(field['fuses']))
    for key, key_value in field['values'].items():
        if value == key_value:
            return key
    if default is None:
        assert False, f"fuses {field['fuses']}: extracted {value}, known {field['values']}"
    return default


def replace_fuses(fuses, field, key):
    for value_key, value in field['values'].items():
        if value_key.upper() == key.upper():
            break
    else:
        assert False, f"fuses {field['fuses']}: replace with {key}, known {field['values']}"
    for n_fuse, fuse in enumerate(field['fuses']):
        fuses[fuse] = (value >> n_fuse) & 1


def parse_filters(selectors, history):
    filters = {}
    for selector in selectors:
        selector_filter = filters
        levels = selector.split('.')
        new_history = []
        for n_level, level in enumerate(levels):
            if not level and len(history) > n_level:
                level = history[n_level]
            new_history.append(level)
            level = level.upper()
            if level not in selector_filter:
                selector_filter[level] = {}
            selector_filter = selector_filter[level]
        history.clear()
        history.extend(new_history)
    return filters


def match_filters(filters, patterns):
    if not filters:
        return True, {}
    for pattern in patterns:
        pattern = pattern.upper()
        if pattern in filters:
            return True, filters[pattern]
    else:
        return False, {}


def match_filters_last(filters, patterns):
    if not filters:
        return True
    for pattern in patterns:
        pattern = pattern.upper()
        if pattern in filters:
            if filters[pattern]:
                raise SystemExit(f"Cannot drill down into {pattern}")
            return True
    else:
        return False


class FuseTool:
    def __init__(self, device, fuses, *, verbose=False):
        self.device = device
        self.fuses = fuses
        self.verbose = verbose
        self._level = 0

    def print(self, *args, **kwargs):
        print(self._level * '  ', end='')
        print(*args, **kwargs)

    @contextmanager
    def hierarchy(self, name):
        self.print(f"{name}:")
        self._level += 1
        yield
        self._level -= 1

    def get_option(self, option_name, option):
        value = extract_fuses(self.fuses, option)
        if self.verbose:
            self.print("{:14} = {:5} {:8} [{}]".format(
                option_name,
                '(' + ''.join(str(self.fuses[n]&1) for n in option['fuses']) + ')',
                value,
                ','.join(map(str, option['fuses']))))
        else:
            self.print("{:14} = {}".format(option_name, value))

    def get_pterm(self, pterm_name, pterm, pterm_points):
        pterm_fuse_range = range(*pterm)
        pterm_fuses = self.fuses[pterm_fuse_range.start:pterm_fuse_range.stop]
        if not pterm_fuses.count(0):
            value = 'VCC'
        elif not pterm_fuses.count(1):
            value = 'GND'
        else:
            expr = []
            for point_net, point_fuse in pterm_points.items():
                if pterm_fuses[point_fuse] == 0:
                    expr.append(point_net)
                    pterm_fuses[point_fuse] = 1
            for unknown_fuse in pterm_fuses.search(bitarray([0])):
                expr.append(f"_{unknown_fuse}")
            value = ' & '.join(expr)
        if self.verbose:
            self.print("{}: {:6} [{:5}..{:5}]".format(
                pterm_name, value, pterm_fuse_range.start, pterm_fuse_range.stop))
        else:
            self.print("{}: {}".format(pterm_name, value))

    def get_macrocell_config(self, macrocell, filters):
        with self.hierarchy('CFG'):
            for option_name in macrocell_options:
                if option_name not in macrocell:
                    continue
                if match_filters_last(filters, (option_name,)):
                    self.get_option(option_name, macrocell[option_name])

    def get_macrocell(self, macrocell_name, filters):
        for option_name in map(str.upper, macrocell_options):
            if option_name in filters:
                if 'CFG' not in filters:
                    filters['CFG'] = {}
                filters['CFG'][option_name] = filters.pop(option_name)

        with self.hierarchy(macrocell_name):
            macrocell = self.device['macrocells'][macrocell_name]

            pterm_points = self.device['blocks'][macrocell['block']]['pterm_points']
            for pterm_name, pterm in macrocell['pterm_ranges'].items():
                if match_filters_last(filters, ('PT', pterm_name)):
                    self.get_pterm(pterm_name, pterm, pterm_points)

            matched, subfilters = match_filters(filters, ('CFG',))
            if matched:
                self.get_macrocell_config(macrocell, subfilters)

    def get_switch_mux(self, mux):
        cross_mux_net = extract_fuses(self.fuses, mux, default='(unknown)')
        if self.verbose:
            return "({}) {:6} [{:5}..{:5}]".format(
                ''.join(str(self.fuses[n]&1) for n in mux['fuses']),
                cross_mux_net,
                min(mux['fuses']), max(mux['fuses']))
        else:
            return cross_mux_net

    def get_switch_option(self, option_name, option):
        option_value = extract_fuses(self.fuses, option)
        if self.verbose:
            return "{}={} {} [{}]".format(
                option_name,
                '(' + ''.join(str(self.fuses[n]&1) for n in option['fuses']) + ')',
                option_value,
                ','.join(map(str, option['fuses'])))
        else:
            return "{}={}".format(option_name, option_value)

    def get_switch(self, switch_name, switch, filters):
        descr = []

        if 'mux' in switch:
            if match_filters_last(filters, ()):
                descr.append(self.get_switch_mux(switch['mux']))

        for option_name in global_options:
            if option_name not in switch:
                continue
            if match_filters_last(filters, (option_name,)):
                descr.append(self.get_switch_option(option_name, switch[option_name]))

        self.print("{}: {}".format(switch_name, ' '.join(descr)))

    def get_special_pin(self, pin, pin_config, filters):
        with self.hierarchy(pin):
            for option_name in special_pin_options:
                if option_name not in pin_config:
                    continue
                if match_filters_last(filters, (option_name,)):
                    self.get_option(option_name, pin_config[option_name])

    def get_special_pins(self, filters):
        with self.hierarchy('PIN'):
            for pin, pin_config in self.device['config']['pins'].items():
                matched, subfilters = match_filters(filters, (pin,))
                if matched:
                    self.get_special_pin(pin, pin_config, subfilters)

    def get_config(self, filters):
        with self.hierarchy('CFG'):
            for config_name in config_options:
                if match_filters_last(filters, (config_name,)):
                    self.get_option(config_name, self.device['config'][config_name])

    def get_user(self, index):
        field = self.device['user'][index]
        value = sum(self.fuses[fuse] << n_fuse for n_fuse, fuse in enumerate(field['fuses']))
        if self.verbose:
            self.print("USR{}: ({}) {:02x} [{:5}..{:5}]".format(
                index,
                ''.join(str(self.fuses[n]&1) for n in field['fuses']),
                value,
                min(field['fuses']), max(field['fuses'])))
        else:
            self.print("USR{}: {:02x}".format(index, value))

    def get_device(self, filters):
        for macrocell_name in self.device['macrocells']:
            matched, subfilters = match_filters(filters, ('MC', macrocell_name))
            if matched:
                self.get_macrocell(macrocell_name, subfilters)

        for switch_name, switch in self.device['switches'].items():
            matched, subfilters = match_filters(filters, ('UIM', switch_name))
            if matched:
                self.get_switch(switch_name, switch, subfilters)

        for prefix in ('GCLR', 'GCLK', 'GOE'):
            for switch_name, switch in self.device['globals'].items():
                if not switch_name.startswith(prefix): continue
                matched, subfilters = match_filters(filters, (prefix, switch_name))
                if matched:
                    self.get_switch(switch_name, switch, subfilters)

        matched, subfilters = match_filters(filters, ('PIN',))
        if matched:
            self.get_special_pins(subfilters)

        matched, subfilters = match_filters(filters, ('CFG',))
        if matched:
            self.get_config(subfilters)

        for index, user_byte in enumerate(self.device['user']):
            if match_filters_last(filters, ('USR', f"USR{index}")):
                self.get_user(index)

    def set_option(self, option_name, option, value):
        self.print("{:14s} = {}".format(option_name, value))

        if value not in option['values']:
            raise SystemExit(f"Option {option_name} cannot be set to '{value}'; "
                             f"choose one of: {', '.join(option['values'])}")

        replace_fuses(self.fuses, option, value)
        return 1

    def set_pterm(self, pterm_name, pterm, pterm_points, value):
        value = value.upper()
        self.print(f"{pterm_name}: {value}")

        pterm_fuse_range = range(*pterm)
        pterm_fuses = self.fuses[pterm_fuse_range.start:pterm_fuse_range.stop]
        if value == 'VCC':
            pterm_fuses.setall(1)
        elif value == 'GND':
            pterm_fuses.setall(0)
        else:
            def apply_net(net, value):
                if net in pterm_points:
                    point_fuse = pterm_points[net]
                elif net.startswith('_'):
                    point_fuse = int(net[1:])
                else:
                    raise SystemExit(f"Product term cannot contain net '{net}'; "
                                     f"choose one of: {', '.join(pterm_points)}")
                pterm_fuses[point_fuse] = value

            expr = value.split(',')
            if all(net.startswith('+') or net.startswith('-') for net in expr):
                for net in expr:
                    if net[0] == '+':
                        apply_net(net[1:], 0)
                    elif net[0] == '-':
                        apply_net(net[1:], 1)
                    else:
                        assert False
            elif any(net.startswith('+') or net.startswith('-') for net in expr):
                raise SystemExit(f"An expression should either modify existing product term "
                                 f"(using '+net,-net,...' syntax) or replace entire product "
                                 f"term (using 'net,net,...' syntax")
            else:
                pterm_fuses.setall(1)
                for net in expr:
                    apply_net(net, 0)

        self.fuses[pterm_fuse_range.start:pterm_fuse_range.stop] = pterm_fuses
        return 1

    def set_macrocell_config(self, macrocell, filters, value):
        changed = 0

        with self.hierarchy('CFG'):
            for option_name in macrocell_options:
                if option_name not in macrocell:
                    continue
                if match_filters_last(filters.get('CFG', filters), (option_name,)):
                    changed += self.set_option(option_name, macrocell[option_name], value)

        return changed

    def set_macrocell(self, macrocell_name, filters, value):
        changed = 0

        for option_name in map(str.upper, macrocell_options):
            if option_name in filters:
                if 'CFG' not in filters:
                    filters['CFG'] = {}
                filters['CFG'][option_name] = filters.pop(option_name)

        with self.hierarchy(macrocell_name):
            macrocell = self.device['macrocells'][macrocell_name]

            pterm_points = self.device['blocks'][macrocell['block']]['pterm_points']
            for pterm_name, pterm in macrocell['pterm_ranges'].items():
                if match_filters_last(filters, ('PT', pterm_name)):
                    changed += self.set_pterm(pterm_name, pterm, pterm_points, value)

            matched, subfilters = match_filters(filters, ('CFG',))
            if matched:
                changed += self.set_macrocell_config(macrocell, subfilters, value)

        return changed

    def set_switch_mux(self, switch_name, switch, value):
        self.print(f"{switch_name}: {value}")

        mux = switch['mux']
        if value not in mux['values']:
            raise SystemExit(f"Switch {switch_name} cannot select net '{value}'; "
                             f"choose one of: {', '.join(mux['values'])}")

        replace_fuses(self.fuses, mux, value)
        return 1

    def set_switch_option(self, switch_name, option_name, option, value):
        self.print(f"{switch_name}: {option_name}={value}")

        if value not in option['values']:
            raise SystemExit(f"Option {option_name} cannot be set to '{value}'; "
                             f"choose one of: {', '.join(option['values'])}")

        replace_fuses(self.fuses, option, value)
        return 1

    def set_switch(self, switch_name, switch, filters, value):
        changed = 0

        if 'mux' in switch:
            if match_filters_last(filters, ()):
                changed += self.set_switch_mux(switch_name, switch, value)

        for option_name in global_options:
            if option_name not in switch:
                continue
            if match_filters_last(filters, (option_name,)):
                changed += self.set_switch_option(switch_name, option_name, switch[option_name],
                                                  value)

        return changed

    def get_special_pin(self, pin, pin_config, filters):
        with self.hierarchy(pin):
            for option_name in special_pin_options:
                if option_name not in pin_config:
                    continue
                if match_filters_last(filters, (option_name,)):
                    self.get_option(option_name, pin_config[option_name])

    def get_special_pins(self, filters):
        with self.hierarchy('PIN'):
            for pin, pin_config in self.device['config']['pins'].items():
                matched, subfilters = match_filters(filters, (pin,))
                if matched:
                    self.get_special_pin(pin, pin_config, subfilters)

    def set_config(self, filters, value):
        changed = 0

        with self.hierarchy('CFG'):
            for config_name in config_options:
                if match_filters_last(filters.get('CFG', filters), (config_name,)):
                    changed += self.set_option(config_name, self.device['config'][config_name],
                                               value)

        return changed

    def set_user(self, index, value):
        self.print(f"USR{index}: {value}")

        field = self.device['user'][index]
        try:
            value = int(value, 16)
        except ValueError:
            raise SystemExit(f"'{value}' is not a hexadecimal number")
        if value not in range(256):
            raise SystemExit(f"'{value}' is not in 0..256 range")

        for n_fuse, fuse in enumerate(field['fuses']):
            self.fuses[fuse] = (value >> n_fuse) & 1
        return 1

    def set_special_pin(self, pin, pin_config, filters, value):
        changed = 0

        with self.hierarchy(pin):
            for option_name in special_pin_options:
                if option_name not in pin_config:
                    continue
                if match_filters_last(filters, (option_name,)):
                    changed += self.set_option(option_name, pin_config[option_name], value)

        return changed

    def set_special_pins(self, filters, value):
        changed = 0

        with self.hierarchy('PIN'):
            for pin, pin_config in self.device['config']['pins'].items():
                matched, subfilters = match_filters(filters, (pin,))
                if matched:
                    changed += self.set_special_pin(pin, pin_config, subfilters, value)

        return changed

    def set_device(self, filters, value):
        changed = 0

        for macrocell_name in self.device['macrocells']:
            matched, subfilters = match_filters(filters, ('MC', macrocell_name))
            if matched:
                changed += self.set_macrocell(macrocell_name, subfilters, value)

        for switch_name, switch in self.device['switches'].items():
            matched, subfilters = match_filters(filters, ('UIM', switch_name))
            if matched:
                changed += self.set_switch(switch_name, switch, subfilters, value)

        for prefix in ('GCLR', 'GCLK', 'GOE'):
            for switch_name, switch in self.device['globals'].items():
                if not switch_name.startswith(prefix): continue
                matched, subfilters = match_filters(filters, (prefix, switch_name))
                if matched:
                    changed += self.set_switch(switch_name, switch, subfilters, value)

        matched, subfilters = match_filters(filters, ('PIN',))
        if matched:
            changed += self.set_special_pins(subfilters, value)

        matched, subfilters = match_filters(filters, ('CFG',))
        if matched:
            changed += self.set_config(subfilters, value)

        for index, user_byte in enumerate(self.device['user']):
            if match_filters_last(filters, ('USR', f"USR{index}")):
                changed += self.set_user(index, value)

        return changed


def arg_parser():
    parser = argparse.ArgumentParser(description=textwrap.dedent("""
    Examine and modify fuses using symbolic names and values.

    The set of fuses to operate on is specified using a set of hierarchical selectors.
    Each level of the selector can match either a single numbered entity (e.g. ``MC3``, ``PT1``),
    or all numbered entities on the same level (e.g. ``PT``, ``GOE``).

    If the requested operation is to examine fuses, the names and values of all selected fuses
    are printed to standard output. If no selector is specified, all fuses are selected.

    If the requested operation is to modify fuses, the values of all selected fuses are changed
    to the value specified on the command line.

    When modifying product term fuses, multiple choices can be specified as a single
    comma-separated value. It is possible to modify (rather than replace) product term fuses
    by prefixing all choices with ``+`` or ``-``. The special value ``VCC`` sets all fuses to 1,
    and the special value ``GND`` sets all fuses to 0.
    """))
    parser.add_argument(
        '-v', '--verbose', default=False, action='store_true',
        help='Show fuse indexes and states next to the symbolic value.')
    parser.add_argument(
        '-d', '--device', metavar='DEVICE', choices=db, default='ATF1502AS',
        help='Select the device to use.')
    parser.add_argument(
        'mangle', metavar='MANGLE', type=argparse.FileType('r+'),
        help='Manipulate fuses in JED file MANGLE.')
    subparsers = parser.add_subparsers(
        metavar='COMMAND', dest='command', required=True,
        help='Operation to perform.')

    get_parser = subparsers.add_parser('get', help='Examine fuse states.')
    get_parser.add_argument(
        'selectors', metavar='SELECTOR', type=str, nargs='*',
        help='Print values of fuses that match SELECTOR.')

    set_parser = subparsers.add_parser('set', help='Modify fuse states.')
    set_parser.add_argument(
        'actions', metavar='SELECTOR VALUE', type=str, nargs=argparse.REMAINDER,
        help='Change values of fuses that match SELECTOR to be VALUE.')

    return parser


def main():
    args = arg_parser().parse_args()

    device = db[args.device]
    device_fuse_count = list(device['ranges'].values())[-1][-1]

    orig_fuses, jed_comment = read_jed(args.mangle)
    fuses = bitarray(orig_fuses)
    if device_fuse_count != len(fuses):
        raise SystemExit(f"Device has {device_fuse_count} fuses, JED file "
                         f"has {len(fuses)}; wrong --device option?")

    history = []
    tool = FuseTool(device, fuses, verbose=args.verbose)

    if args.command == 'get':
        tool.get_device(parse_filters(args.selectors, history))

    if args.command == 'set':
        if len(args.actions) % 2 != 0:
            raise SystemExit(f"Actions must be specified in pairs")

        changed = 0
        for selector, value in zip(args.actions[0::2], args.actions[1::2]):
            action_changed = tool.set_device(parse_filters((selector,), history), value)
            if action_changed == 0:
                raise SystemExit(f"Filter '{selector}' does not match anything")
            changed += action_changed
        changed_fuses = (orig_fuses ^ fuses).count(1)
        print(f"Changed {changed} fields, {changed_fuses} fuses.")

        jed_comment += f"Edited: set {' '.join(args.actions)}\n"

    if fuses != orig_fuses:
        args.mangle.seek(0)
        args.mangle.truncate()
        write_jed(args.mangle, fuses, comment=jed_comment)


if __name__ == '__main__':
    main()
