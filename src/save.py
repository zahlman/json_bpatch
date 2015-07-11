import load, constrain


def save(to_patch, patch_map, fit_map):
    for name, patch in patch_map.items():
        if name in fit_map:
            print(
                "Writing: {} in [{}:{}]".format(
                    name, fit_map[name], fit_map[name] + len(patch_map[name])
                )
            )
            patch.write_into(to_patch, fit_map[name], fit_map)


def write_patch(to_patch, patch_file, defaults_file, free_file, roots=None):
    freespace = [range(x, y) for x, y in load.get_json(free_file)]
    patch_map = load.load_files(patch_file, defaults_file)
    if roots is None:
        roots = [x for x in patch_map.keys() if x.startswith('_')]
    fit_map = constrain.make_fit_map(patch_map, roots, freespace)
    if fit_map is None:
        raise ValueError("Fitting failed.")
    else:
        save(to_patch, patch_map, fit_map)
