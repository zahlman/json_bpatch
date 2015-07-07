from collections import ChainMap
from functools import partial
import json
from patch import Datum, NamedPointer, Patch
from pointer import Pointer


def get_param(params, expected_type, name):
    value = params[name]
    # Strict type checks, because we don't want the incoming JSON
    # to use integers and booleans interchangeably.
    if type(value) != expected_type:
        raise TypeError('{} must be a {}'.format(name, expected_type.__name__))
    return value


def make_named_pointer(defaults, settings):
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
    return NamedPointer(
        referent, Pointer(offset, size, align, stride, signed, bigendian)
    )


def make_item_with_defaults(defaults, data):
    if isinstance(data, str):
        return Datum(bytes(data, 'ascii')) # temporary!
    elif isinstance(data, dict):
        return make_named_pointer(defaults, data)
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
    return {k: load_patch(make_item, k, v) for k, v in parsed_json.items()}


def load_patch(item_loader, name, patch):
    if not isinstance(patch, list):
        raise ValueError('Patch must be a JSON array of Patch items')
    return Patch(name, list(map(item_loader, patch)))


def get_json(filename):
    with open(filename) as f:
        return json.load(f)


def load_files(patch_file, defaults_file):
    return load(get_json(patch_file), get_json(defaults_file))
