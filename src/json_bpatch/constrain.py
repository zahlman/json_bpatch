from collections import deque
from functools import partial
from itertools import chain
from .pointer import range_intersect


class Freespace:
    """Represents a set of "free" locations in the file to be patched."""
    def __init__(self):
        self._ranges = []


    def _ranges_with(self, start, size):
        merged_start = start
        merged_stop = start + size
        merged_written = False
        for r in self._ranges:
            if r.stop < merged_start:
                # Completely before the inserted range.
                yield r
            elif r.start > merged_stop:
                # Completely after the inserted range.
                # Ensure that the merged chunk is written first.
                if not merged_written:
                    yield range(merged_start, merged_stop)
                merged_written = True
                yield r
            else:
                # Overlaps; do merging.
                merged_start = min(merged_start, r.start)
                merged_stop = max(merged_stop, r.stop)
        # Ensure merged chunk is written if there's nothing after it.
        if not merged_written:
            yield range(merged_start, merged_stop)


    def including(self, start, size):
        result = Freespace()
        result._ranges = list(self._ranges_with(start, size))
        return result


    def add(self, start, size):
        self._ranges = list(self._ranges_with(start, size))


    def _ranges_without(self, start, size):
        removed_start = start
        removed_stop = start + size
        for r in self._ranges:
            if r.stop <= removed_start or r.start >= removed_stop:
                # No overlap.
                yield r
            else:
                # Do the appropriate clipping.
                # May produce 0-2 clips.
                if r.start < removed_start:
                    yield range(r.start, removed_start)
                if r.stop > removed_stop:
                    yield range(removed_stop, r.stop)


    def excluding(self, start, size):
        result = Freespace()
        result._ranges = list(self._ranges_without(start, size))
        return result


    def remove(self, start, size):
        self._ranges = list(self._ranges_without(start, size))


    def _candidate_ranges(self, size, pointer_gamut):
        for r in self._ranges:
            if size == 0:
                # Special case: zero-length patch items can go anywhere.
                yield range(0, 1)
            else:
                yield range_intersect(
                    range(r.start, r.stop - size + 1), pointer_gamut
                )


    def candidates(self, size, pointer_gamut):
        """Iterable of places where a patch item of the specified `size`
        could be written in this Freespace, subject to the `pointer_gamut`."""
        return Candidates(tuple(self._candidate_ranges(size, pointer_gamut)))


class Candidates:
    def __init__(self, ranges):
        self._ranges = ranges


    def __iter__(self):
        candidate_ranges = deque(map(iter, self._ranges))
        while candidate_ranges:
            try:
                yield next(candidate_ranges[0])
            except StopIteration:
                candidate_ranges.popleft() # Exhausted options in this chunk.
            candidate_ranges.rotate(-1) # Try a candidate from the next chunk.


    def __len__(self):
        return sum(map(len, self._ranges))


def make_gamut_map(patch_map, roots):
    """Produce a map from patch items that will be included in patching,
    to the pointer constraints placed upon their patch locations.

    `roots` -> names of patches whose inclusion should be forced.
    Other patches will be transitively included as required by pointers.
    """
    processed = set()
    to_process = set(roots)
    # Ensure that the roots appear in the result.
    result = {r: None for r in to_process}
    # Iteratively apply constraints from "discovered" pointers.
    while to_process:
        p = to_process.pop()
        patch_map[p].constrain(result, processed, to_process)
        processed.add(p)
    return result


def make_fit_map_rec(patch_map, gamut_map, freespace, fits, unfitted):
    if not unfitted:
        return fits # reached end of recursion

    # Recompute candidates for each unfitted item, and select the
    # most constrained.
    candidate_mapping = {
        name: freespace.candidates(len(patch_map[name]), gamut_map[name])
        for name in unfitted
    }
    name = min(unfitted, key=lambda n: (len(candidate_mapping[n]), n))

    for candidate in candidate_mapping[name]:
        recurse = make_fit_map_rec(
            patch_map,
            gamut_map,
            freespace.excluding(candidate, len(patch_map[name])),
            fits + ((name, candidate),),
            tuple(x for x in unfitted if x != name)
        )
        if recurse is not None: # This candidate value works.
            return recurse
    # Found no solution; propagate None up the recursion.


def make_fit_map(patch_map, roots, freespace):
    gamut_map = make_gamut_map(patch_map, roots)
    fits = make_fit_map_rec(
        patch_map, gamut_map, freespace, (), gamut_map.keys()
    )
    if fits is not None:
        fits = dict(fits)
    return fits
