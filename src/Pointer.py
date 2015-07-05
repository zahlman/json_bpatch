class Pointer:
    def __init__(self, offset, size, stride, signed, bigendian):
        self._offset = offset
        bits = size * 8
        low = -((1 << bits) >> 1) if signed else 0
        high = 0 if size == 0 else ((1 << bits) - 1 + low)
        self._gamut = range(
            stride * (low if stride > 0 else high) + offset,
            stride * (high if stride > 0 else low) + offset + 1,
            abs(stride)
        )
        s = range(0, bits, 8)
        self._shifts = reversed(s) if bigendian else s
        self._stride = stride


    @property
    def gamut(self):
        """A range object containing all addresses that can be represented,
        in ascending order."""
        return self._gamut


    def data(self, address):
        """The bytes used by a pointer of this type to the given address."""
        if not self._gamut.start <= address < self._gamut.stop:
            raise ValueError("Address out of bounds")
        value, remainder = divmod((address - self._offset), self._stride)
        if remainder:
            raise ValueError("Improperly aligned address")
        return bytes((value >> shift) & 0xff for shift in self._shifts)
