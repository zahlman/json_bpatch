def gcd(x, y):
    """Iterative implementation of Euclid's algorithm."""
    if x < y:
        x, y = y, x
    while x > y and y != 0:
        x, y = y, x % y
    return x


def range_intersect(x, y):
    """Compute a range containing values only seen in both input range objects.
    The result range may be empty. Step values must be positive."""

    # First, some normalization. We treat `None` as equivalent to a range from
    # -infinity to +infinity with a step of 1.
    if x is None: return y
    if y is None: return x
    if x.start > y.start: x, y = y, x

    stop = min(x.stop, y.stop)
    # Check that the start points are congruent modulo the gcd of strides.
    stride_gcd = gcd(x.step, y.step)
    step = x.step * y.step // stride_gcd # lcm
    start = stop # default result: empty range
    if x.start % stride_gcd == y.start % stride_gcd:
        # The sequences line up eventually; check values from y until we find
        # one that's in x, or exceed the stopping point.
        # There doesn't seem to be a neater approach; in the worst case, this
        # is apparently equivalent to decrypting RSA.
        try:
            start = next(v for v in range(y.start, stop, y.step) if v in x)
        except StopIteration:
            pass # couldn't find a start point.
    return range(start, stop, step)


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
