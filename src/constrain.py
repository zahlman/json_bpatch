from collections import defaultdict
from functools import partial
from itertools import chain
from pointer import range_intersect


def range_exclude(r, low, high):
    start, stop, step = r.start, r.stop, r.step
    if low <= r.start < high:
        start = high + (r.start - high) % r.step
    if low <= r.stop < high:
        stop = low
    return range(start, stop, step)


class CandidateSet:
    """Represents a set of locations where a given Patch might be written."""
    def __init__(self, freespace):
        self._set(freespace)


    def _set(self, freespace):
        self._locations = list(filter(None, freespace))


    def __iter__(self):
        return chain.from_iterable(self._locations)


    def __len__(self):
        return sum(map(len, self._locations))


    def constrain(self, gamut):
        """Restrict the locations to ones found within the `gamut`."""
        self._set(range_intersect(x, gamut) for x in self._locations)


    def not_overlapping(self, low, high):
        """Return a new CandidateSet based off this one, with no candidates
        in [`low`, `high`)."""
        return CandidateSet(
            range_exclude(r, low, high) for r in self._locations
        )


    def __repr__(self):
        return repr(self._locations)


def make_candidate_map(patch_map, roots, freespace):
    # Elegant hack: Datum objects will identify their "referent" as None,
    # so exclude that from consideration right away.
    processed = {None} 
    to_process = set(roots)
    result = defaultdict(partial(CandidateSet, freespace))
    while to_process:
        p = to_process.pop()
        patch_map[p].constrain(result, processed, to_process)
        processed.add(p)
    return result


def freedom(item):
    """Measure of how constrained an `item` in a candidate map is.
    The most constrained items are fit first, in general."""
    key, value = item
    return len(value), key


def make_fit_map_rec(patch_map, candidate_map, fits):
    if not candidate_map:
        return fits # reached end of recursion
    name, candidate_set = min(candidate_map.items(), key=freedom)
    for candidate in candidate_set:
        recurse = make_fit_map_rec(
            patch_map,
            {
                k: v.not_overlapping(
                    candidate - len(patch_map[k]),
                    candidate + len(patch_map[name])
                )
                for k, v in candidate_map.items()
                if k != name
            },
            fits + ((name, candidate),)
        )
        if recurse is not None: # This candidate value works.
            return recurse
    # Found no solution; propagate None up the recursion.


def make_fit_map(patch_map, roots, freespace):
    candidate_map = make_candidate_map(patch_map, roots, freespace)
    fits = make_fit_map_rec(patch_map, candidate_map, ())
    if fits is not None:
        fits = dict(fits)
    return fits
