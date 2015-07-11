from base64 import b64decode
from collections import ChainMap
from functools import partial
import json
from .constrain import make_fit_map
from .patch import Datum, Patch
from .pointer import Pointer


def get_param(params, expected_type, name):
    value = params[name]
    # Strict type checks, because we don't want the incoming JSON
    # to use integers and booleans interchangeably.
    if type(value) != expected_type:
        raise TypeError('{} must be a {}'.format(name, expected_type.__name__))
    return value


def make_pointer(defaults, settings):
    params = ChainMap(settings, defaults)
    offset = get_param(params, int, 'offset')
    size = get_param(params, int, 'size')
    align = get_param(params, int, 'align')
    stride = get_param(params, int, 'stride')
    signed = get_param(params, bool, 'signed')
    bigendian = get_param(params, bool, 'bigendian')
    if size < 0:
        raise ValueError('size cannot be negative')
    if align < 1 or (align & (align - 1)):
        raise ValueError('align must be a power of two')
    # Should not appear in the `defaults`, and always be specified.
    referent = get_param(params, str, 'referent')
    return Pointer(referent, offset, size, align, stride, signed, bigendian)


def make_datum(s):
    if s.startswith('@'):
        filename = s[1:]
        with open(filename, 'rb') as f:
            data = f.read()
    elif s.startswith('='):
        data = b64decode(s) # the '=' will be handled automatically.
    else:
        # hex dump; expect a space after every digit pair.
        data = bytes(int(_, 16) for _ in s.split())
    return Datum(data)


def make_item_with_defaults(defaults, data):
    if isinstance(data, str):
        return make_datum(data)
    elif isinstance(data, dict):
        return make_pointer(defaults, data)
    else:
        raise ValueError('Patch item must be a Datum or a Pointer')


def item_factory(defaults):
    # Sanitize defaults.
    if 'referent' in defaults:
        raise ValueError('default value for referent may not be specified')
    return partial(make_item_with_defaults, {
        'offset': get_param(defaults, int, 'offset'),
        'size': get_param(defaults, int, 'size'),
        'align': get_param(defaults, int, 'align'),
        'stride': get_param(defaults, int, 'stride'),
        'signed': get_param(defaults, bool, 'signed'),
        'bigendian': get_param(defaults, bool, 'bigendian'),
    })


def load(parsed_json, defaults):
    if not isinstance(parsed_json, dict):
        raise ValueError('data must be a JSON object with Patches as values')
    make_item = item_factory(defaults)
    return {k: load_patch(make_item, v) for k, v in parsed_json.items()}


def load_patch(item_loader, patch):
    if not isinstance(patch, list):
        raise ValueError('Patch must be a JSON array of Patch items')
    return Patch(list(map(item_loader, patch)))


def get_json(filename):
    with open(filename) as f:
        return json.load(f)


def load_files(patch_file, defaults_file):
    return load(get_json(patch_file), get_json(defaults_file))


def save(to_patch, patch_map, fit_map):
    for name, patch in patch_map.items():
        if name in fit_map:
            print(
                "Writing: {} in [{}:{}]".format(
                    name, fit_map[name], fit_map[name] + len(patch_map[name])
                )
            )
            patch.write_into(to_patch, fit_map[name], fit_map)


def write_patch(to_patch, patch_file, defaults_file, free_file, roots=None):
    freespace = [range(x, y) for x, y in get_json(free_file)]
    patch_map = load_files(patch_file, defaults_file)
    if roots is None:
        roots = [x for x in patch_map.keys() if x.startswith('_')]
    fit_map = make_fit_map(patch_map, roots, freespace)
    if fit_map is None:
        raise ValueError("Fitting failed.")
    else:
        save(to_patch, patch_map, fit_map)


def do_patching(
    in_file, out_file, patch_file, defaults_file, free_file, roots=None
):
    with open(in_file, 'rb') as f:
        data = bytearray(f.read())
    write_patch(data, patch_file, defaults_file, free_file, roots)
    with open(out_file, 'wb') as f:
        f.write(data)
