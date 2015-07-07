def save(rom, patch_map, fit_map):
    for name, patch in patch_map.items():
        if name in fit_map:
            patch.write_into(rom, fit_map[name], fit_map)
