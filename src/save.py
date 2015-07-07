def save(rom, patch_map, fit_map):
    for patch in patch_map.items():
        patch.write_into(rom, fit_map)

