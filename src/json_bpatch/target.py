import json, re
from .constrain import make_fit_map
from .main import get_json
from .freespace import Freespace


k, kb = 1024, 1000
suffixes = {
    '': 1, 'b': 1,
    'k': k, 'kb': kb,
    'm': k*k, 'mb': kb*kb,
    'g': k*k*k, 'gb': kb*kb*kb,
    't': k*k*k*k, 'tb': kb*kb*kb*kb,
    'p': k*k*k*k*k, 'pb': kb*kb*kb*kb*kb,
    'e': k*k*k*k*k*k, 'eb': kb*kb*kb*kb*kb*kb,
    'z': k*k*k*k*k*k*k, 'zb': kb*kb*kb*kb*kb*kb*kb,
    'y': k*k*k*k*k*k*k*k, 'yb': kb*kb*kb*kb*kb*kb*kb*kb
}
suffix_pattern = re.compile('(.*?)([a-zA-Z]*)$')


def parse_filesize(s):
     try:
         number, suffix = suffix_pattern.match(s).groups()
         return int(number) * suffixes[suffix]
     except Exception:
         raise ValueError("Invalid specification for maximum filesize.")


class Target:
    """Represents the file that will be patched,
    along with bookkeeping information about the patching process."""


    def __init__(self, patch_name, free_name, max_filesize):
        with open(patch_name, 'rb') as f:
            self._data = bytearray(f.read())
        self._free = Freespace()
        if free_name is not None:
            for start, end in get_json(free_name):
                self._free.add(start, end - start)
        if max_filesize is not None:
            size = parse_filesize(max_filesize)
            end = len(self._data)
            self._free.add(end, size - end)


    def write_patch(self, patch_map, roots=None):
        if roots is None:
            roots = [x for x in patch_map.keys() if x.startswith('_')]
        fit_map = make_fit_map(patch_map, roots, self._free)
        if fit_map is None:
            raise ValueError("Fitting failed.")
        for name, where in fit_map.items():
            what = patch_map[name]
            print(
                "Writing: {} in [{}:{}]".format(name, where, where + len(what))
            )
            what.write_into(self._data, where, fit_map)
            self._free.remove(where, len(what))


    def save(self, patch_name, free_name):
        with open(patch_name, 'wb') as f:
            f.write(self._data)
        if free_name is not None:
            with open(free_name, 'w') as f:
                json.dump(self._free.data, f)
