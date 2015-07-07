from collections import defaultdict
from functools import partial
from pointer import range_intersect


class CandidateSet:
    """Represents a set of locations where a given Patch might be written."""
    def __init__(self, freespace):
        self._set(freespace)


    def _set(self, freespace):
        self._locations = list(filter(None, freespace))


    def constrain(self, gamut):
        """Restrict the locations to ones found within the `gamut`."""
        self._set(range_intersect(x, gamut) for x in self._locations)


    def not_overlapping(self, low, high):
        """Return a new CandidateSet based off this one, with no candidates
        in [`low`, `high`)."""
        return CandidateSet(
            range(
                high if low <= r.start < high else r.start,
                low if low <= r.stop < high else r.stop,
                r.step
            ) for r in self._locations
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
