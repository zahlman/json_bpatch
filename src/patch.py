class NamedPointer:
    def __init__(self, name, pointer):
        self._name = name
        self._pointer = pointer


    def __len__(self):
        return len(self._pointer)


    def data(self, fit):
        return self._pointer.data(fit[self._name])


class Datum:
    def __init__(self, raw):
        self._raw = raw


    def __len__(self):
        return len(self._raw)


    def data(self, fit):
        return self._raw


class Patch:
    """Represents a contiguous chunk of data to be written by the patcher,
    specified as a sequence of either Datum objects (representing fixed byte
    sequences) or NamedPointer objects (whose value encodes the location of
    another Patch)."""
    def __init__(self, name, components):
        self._name = name
        self._components = components


    def __len__(self):
        return sum(len(component) for component in self._components)


    def write_into(self, rom, fit):
        """Write the patch data to the `rom`, if it's part of the `fit`.
        `rom` -> `bytearray` representing the entire file being written into.
        `fit` -> map of (str: name of patch) -> (int: location to write).
        The `fit` is also used by NamedPointers to compute their values."""
        try:
            where = fit[self._name]
        except KeyError:
            return
        assert where >= 0
        # Ensure the rom is long enough that we can start writing at 'where'.
        # Multiplying a list by a negative value produces an empty list, so
        # the resulting behaviour is what we want.
        print("WRITING AT:", where)
        rom.extend([0] * (where - len(rom)))
        print("ROM NOW:", rom)
        # Write the individual components.
        for component in self._components:
            data = component.data(fit)
            end = where + len(data)
            # This works regardless of whether the write is in the middle,
            # overlapping the end or at the end. Because of the initial padding,
            # it cannot be past the end; and because `where >= 0`, it cannot
            # overlap the beginning.
            rom[where:end] = data
            where = end

