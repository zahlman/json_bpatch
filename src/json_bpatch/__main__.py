from .main import do_patching
import argparse


def main():
    parser = argparse.ArgumentParser(prog='json_bpatch', description='Binary patcher using a JSON-based patch format.')
    parser.add_argument('target', help='name of file to patch')
    parser.add_argument('output', help='name to use for patched result')
    parser.add_argument('patch', help='name of patch file')
    parser.add_argument('config', help='name of configuration file')
    parser.add_argument('freespace', help='name of freespace listing file')
    data = parser.parse_args()
    do_patching(data.target, data.output, data.patch, data.config, data.freespace)


if __name__ == '__main__':
    main()
