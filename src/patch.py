class Datum:
    def __init__(self, raw):
        self._raw = raw


    def __len__(self):
        return len(self._raw)


    def data(self, fit_map):
        return self._raw


    def constrain(self, candidate_map):
        pass


    def __repr__(self):
        return '<Datum: "{}">'.format(self._raw)


class Patch:
    """Represents a contiguous chunk of data to be written by the patcher,
    specified as a sequence of either Datum objects (representing fixed byte
    sequences) or Pointer objects (whose value encodes the location of
    another Patch)."""
    def __init__(self, name, components):
        self._name = name
        self._components = components


    def __len__(self):
        return sum(len(component) for component in self._components)


    def constrain(self, candidate_map, processed, to_process):
        """Iterate over components and have each apply its constraints
        to the `candidate_map`. As a side effect, update the "open" set
        for the transitive cover operation."""
        for component in self._components:
            result = component.constrain(candidate_map)
            if result not in processed:
                to_process.add(result)


    def write_into(self, rom, fit_map):
        """Write the patch data to the `rom`, if it's part of the `fit_map`.
        `rom` -> `bytearray` representing the entire file being written into.
        `fit_map` -> map of (str: name of patch) -> (int: location to write).
        The `fit_map` is also used by Pointers to compute their values."""
        try:
            where = fit_map[self._name]
        except KeyError:
            return
        assert where >= 0
        # Ensure the rom is long enough that we can start writing at 'where'.
        # Multiplying a list by a negative value produces an empty list, so
        # the resulting behaviour is what we want.
        rom.extend([0] * (where - len(rom)))
        # Write the individual components.
        for component in self._components:
            data = component.data(fit_map)
            end = where + len(data)
            # This works regardless of whether the write is in the middle,
            # overlapping the end or at the end. Because of the initial padding,
            # it cannot be past the end; and because `where >= 0`, it cannot
            # overlap the beginning.
            rom[where:end] = data
            where = end


    def __repr__(self):
        return '<Patch: {}>'.format(self._components)
