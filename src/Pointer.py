class Pointer:
    def __init__(self, offset, size, stride, signed, bigendian):
        self.offset = offset
        self.size = size
        self.stride = stride
        self.signed = signed
        self.bigendian = bigendian


    def _deref(self, value):
        return self.offset + self.stride * value


    def _ref(self, address):
        return divmod((address - self.offset), self.stride)


    @property
    def bits(self):
        return self.size * 8


    @property
    def low_value(self):
        return -(1 << (self.bits - 1)) if self.signed else 0


    @property
    def high_value(self):
        return (1 << (self.bits - (1 if self.signed else 0))) - 1


    def _low_address(self):
        return self._deref(self.low_value)


    def _high_address(self):
        return self._deref(self.high_value)


    @property
    def low_address(self):
        return self._low_address() if self.stride > 0 else self._high_address()


    @property
    def high_address(self):
        return self._high_address() if self.stride > 0 else self._low_address()


    @property
    def gamut(self):
        """A range object containing all addresses that can be represented,
        in ascending order."""
        return range(self.low_address, self.high_address + 1, abs(self.stride))


    def data(self, address):
        """The bytes used by a pointer of this type to the given address."""
        value, remainder = self._ref(address)
        if remainder:
            raise ValueError("Improperly aligned address")
        if not self.low_value <= value <= self.high_value:
            raise ValueError("Address out of bounds")
        shifts = range(0, 8 * self.size, 8)
        if self.bigendian:
            shifts = reversed(shifts)
        return bytes((value >> shift) & 0xff for shift in shifts)
