class Pointer:
    def __init__(self, offset, size, align, stride, signed, bigendian):
        self._offset = offset
        self._mask = align - 1
        bits = size * 8 
        low = -((1 << bits) >> 1) if signed else 0
        high = 0 if size == 0 else ((1 << bits) - 1 + low)
        self._gamut = range(
            stride * (low if stride > 0 else high) + offset,
            stride * (high if stride > 0 else low) + offset + 1,
            abs(stride) * align
        )
        s = range(0, size * 8, 8)
        self._shifts = reversed(s) if bigendian else s
        self._stride = stride
        self._size = size


    def __len__(self):
        return self._size


    @property
    def gamut(self):
        """A range object containing all addresses that can be represented,
        in ascending order."""
        return self._gamut


    def data(self, address):
        """The bytes used by a pointer of this type to the given address."""
        if not self._gamut.start <= address < self._gamut.stop:
            raise ValueError("Address out of bounds")
        if address not in self._gamut:
            raise ValueError("Improperly aligned address")
        value = (address - self._offset) // self._stride
        return bytes((value >> shift) & 0xff for shift in self._shifts)


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
    if x.start > y.start: # Normalize.
        x, y = y, x

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
