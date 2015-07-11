from .constrain import range_intersect


class Datum:
    def __init__(self, raw):
        self._raw = raw


    def __len__(self):
        return len(self._raw)


    def data(self, fit_map):
        return self._raw


    def constrain(self, candidate_map, processed, to_process):
        pass


    def __repr__(self):
        return '<Datum: "{}">'.format(self._raw)


class Pointer:
    def __init__(self, ref, offset, size, align, stride, signed, bigendian):
        self._referent = ref
        self._offset = offset
        self._mask = align - 1
        bits = size * 8
        low = -((1 << bits) >> 1) if signed else 0
        high = 0 if size == 0 else ((2 << bits) - 1 + low)
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


    def data(self, fit_map):
        """The bytes used by this pointer, given the specified `fit_map`.
        The referent of this pointer must be mentioned in the map."""
        address = fit_map[self._referent]
        if not self._gamut.start <= address < self._gamut.stop:
            raise ValueError("Address out of bounds")
        if address not in self._gamut:
            raise ValueError("Improperly aligned address")
        value = (address - self._offset) // self._stride
        return bytes((value >> shift) & 0xff for shift in self._shifts)


    def constrain(self, gamut_map, processed, to_process):
        """Apply constraint implied by this pointer to the `gamut_map`."""
        gamut_map[self._referent] = range_intersect(
            gamut_map.get(self._referent, None),
            self.gamut
        )
        if self._referent not in processed:
            to_process.add(self._referent)


    def __repr__(self):
        return '<Pointer to "{}", in {}>'.format(self._referent, self.gamut)


class Patch:
    """Represents a contiguous chunk of data to be written by the patcher,
    specified as a sequence of either Datum objects (representing fixed byte
    sequences) or Pointer objects (whose value encodes the location of
    another Patch)."""
    def __init__(self, components):
        self._components = components


    def __len__(self):
        return sum(len(component) for component in self._components)


    def constrain(self, candidate_map, processed, to_process):
        """Iterate over components and have each apply its constraints
        to the `candidate_map`. As a side effect, update the "open" set
        for the transitive cover operation."""
        for component in self._components:
            component.constrain(candidate_map, processed, to_process)


    def write_into(self, to_patch, where, fit_map):
        """Write the data represented by this Patch, into `to_patch`.
        `to_patch` -> `bytearray` representing the entire file being patched.
        `where` -> int location where this patch goes.
        `fit_map` -> map of (str: name of patch) -> (int: location to write).
        Used by Pointers to compute their values."""
        assert where >= 0
        # Ensure the array is long enough that we can start writing at 'where'.
        # Multiplying a list by a negative value produces an empty list, so
        # the resulting behaviour is what we want.
        to_patch.extend([0] * (where - len(to_patch)))
        # Write the individual components.
        for component in self._components:
            data = component.data(fit_map)
            end = where + len(data)
            # This works regardless of whether the write is in the middle,
            # overlapping the end or at the end. Because of the initial padding,
            # it cannot be past the end; and because `where >= 0`, it cannot
            # overlap the beginning.
            to_patch[where:end] = data
            where = end


    def __repr__(self):
        return '<Patch: {}>'.format(self._components)
