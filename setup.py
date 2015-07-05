from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages
from os import path, chdir, remove
import subprocess


def interpret_dev_status(status):
    names = 'Planning Pre-Alpha Alpha Beta Production/Stable Mature Inactive'
    mapping = {}
    for i, name in enumerate(names.split(), 1):
        k, v = name.lower(), '{} - {}'.format(i, name)
        mapping[k] = v
        mapping[i] = v
        mapping[k.replace('-', '')] = v
        for c in k.split('/'):
            mapping[c] = v

    try:
        status = int(status[0]) # string starting with a digit?
    except:
        pass

    try:
        return mapping[status]
    except KeyError:
        raise ValueError(''.join(
            'invalid development status: must be integer 1-7,',
            'or string beginning with digit 1-7,',
            'or valid development status name'
        ))


def make_classifiers_gen(breadcrumb, *options):
    prefix = ' :: '.join(breadcrumb)
    for option in options:
        if option is None:
            yield prefix
        # Since strings are iterable, they need to be handled separately.
        elif isinstance(option, str):
            yield prefix + ' :: ' + option
        else:
            try:
                i = iter(option)
                n = next(i)
            except TypeError: # Not a sequence.
                yield '{} :: {}'.format(prefix, option)
            except StopIteration:
                raise ValueError("Empty sequences not permitted")
            else:
                yield from make_classifiers_gen(breadcrumb + (n,), *i)


def make_classifiers(breadcrumb, *options):
    return list(make_classifiers_gen(breadcrumb, *options))


def make_version(*args, **kwargs):
    result = '.'.join(str(a) for a in args)
    if 'epoch' in kwargs:
        result = '{}!{}'.format(kwargs['epoch'], result)
    def single_key(normalize, *names):
        canonical = names[0]
        found = False
        for name in names:
            if name in kwargs:
                if found:
                    raise ValueError("please specify only one of {}".format(names))
                found = True
                if normalize and name != canonical:
                    kwargs[canonical] = kwargs[name]
                    del kwargs[name]
    single_key(True, 'c', 'rc', 'preview', 'pre')
    single_key(True, 'b', 'beta')
    single_key(True, 'a', 'alpha')
    single_key(False, 'a', 'b', 'c')
    single_key(True, 'post', 'r', 'rev')
    for segment in ('a', 'b', 'c', 'post', 'dev'):
        if segment in kwargs:
            result = '{}.{}{}'.format(result, segment, kwargs[segment])
    return result


def do_setup(here, config):
    packages = find_packages(
        config.source_dir,
        exclude = config.exclude_packages,
        include = config.include_packages
    )

    version = make_version(*config.version, **config.version_qualifiers)

    # Write a __version__.py file to each package.
    for package in packages:
        with open(path.join(here, 'src', package, '__version__.py'), mode='w') as f:
            f.write('__version__ = {!r}'.format(version))

    # Get the long description from the relevant file.
    with open(path.join(here, 'DESCRIPTION.rst')) as f:
        long_description = f.read()

    # Enumerate files to include.
    with open(path.join(here, 'MANIFEST.in'), 'w') as f:
        chdir(here)
        git = subprocess.Popen(['git', 'ls-files'], stdout=subprocess.PIPE)
        # FIXME: This doesn't actually properly handle Unicode, because git
        # does some weird re-encoding thing with Unicode filenames.
        # FIXME: Filenames with special characters (ones used for globbing)
        # need to be properly escaped.
        for line in git.stdout:
            f.write('include {}'.format(line.decode('utf-8')))
        # Don't include the auto-generated MANIFEST.in itself.
        f.write('exclude MANIFEST.in\n')
        for line in config.extra_manifest:
            f.write(line + '\n')

    # Set basic options.
    options = {
        'name': config.project_name,
        'version': version,
        'description': config.description,
        'long_description': long_description,
        'url': config.url,
        'author': config.author,
        'author_email': config.author_email,
        'license': config.license,
        'classifiers': make_classifiers(
            ('Development Status', interpret_dev_status(config.development_status))
        ) + make_classifiers(
            (), *config.additional_classifiers
        ) + make_classifiers(
            ('License',), config.license_long
        ) + make_classifiers(
            ('Programming Language', 'Python'), *config.supported_versions
        ),
        'keywords': config.keywords,
        'package_dir': {'': config.source_dir},
        'packages': packages,
        'install_requires': config.dependencies,
        'include_package_data': True
    }

    entry_points = {}
    for script_type in ('console_scripts', 'gui_scripts'):
        scripts = [
            '{}={}'.format(k, v)
            for k, v in getattr(config, script_type, {}).items()
        ]
        if scripts:
            entry_points[script_type] = scripts

    if entry_points:
        options['entry_points'] = entry_points

    # Add anything else explicitly specified by the user.
    options.update(config.extra_options)

    # Finally ready.
    setup(**options)
    remove('MANIFEST.in')


if __name__ == '__main__':
    import setup_config
    do_setup(path.dirname(path.abspath(__file__)), setup_config)
