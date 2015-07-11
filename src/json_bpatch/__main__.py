from .target import Target
from .main import load_patch_file
import argparse


def do_patching(
    target, patch, output,
    free_input, free_output,
    defaults, roots, limit
):
    print("Setting up patch target...")
    patch_target = Target(target, free_input, limit)
    print("Reading patch...")
    patch_map = load_patch_file(patch, defaults)
    print("Writing patch data...")
    patch_target.write_patch(patch_map, roots)
    print("Saving output files...")
    patch_target.save(
        target if output is None else output,
        free_input if free_output is None else free_output
    )
    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        prog='json_bpatch',
        description='Binary patcher using a JSON-based patch format.',
        epilog="""If an output filename is not specified, output will be
        written to the input file, if any, and otherwise suppressed.
        By default, the patch items written are those with names starting with
        an underscore, along with anything included from those "roots".
        The `limit` argument allows for specifying "virtual freespace" between
        the end of the file and the specified maximum filesize. It may be
        specified as a raw number of bytes, or with a case-insensitive
        size postfix (like the `du` linux command)."""
    )
    parser.add_argument('target', help='name of file to patch')
    parser.add_argument('patch', help='name of patch file')
    parser.add_argument('-o', '--output', help='name to use for patched result')
    parser.add_argument('-f', '--free-input', help='freespace file to read')
    parser.add_argument('-F', '--free-output', help='freespace file to write')
    parser.add_argument('-d', '--defaults', help='pointer defaults filename')
    parser.add_argument('-r', '--roots', nargs='+', help='roots for patching'),
    parser.add_argument('-l', '--limit', help='maximum filesize when appending')
    do_patching(**vars(parser.parse_args()))


if __name__ == '__main__':
    main()
