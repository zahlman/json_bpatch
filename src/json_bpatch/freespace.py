from collections import deque
from .constrain import range_intersect


class Freespace:
    """Represents a set of "free" locations in the file to be patched."""
    def __init__(self):
        self._ranges = []


    @property
    def data(self):
        return [[r.start, r.stop] for r in self._ranges]


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
            else:
                candidate_ranges.rotate(-1) # Move to the next chunk.


    def __len__(self):
        return sum(map(len, self._ranges))
