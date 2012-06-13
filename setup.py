#!/usr/bin/env
import os
from distutils.core import setup


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

packages = []
package_data_files = {"spank": []}
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
spank_dir = 'spank'

for dirpath, dirnames, filenames in os.walk(spank_dir):
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        package_data_files["spank"] += [os.path.relpath(os.path.join(dirpath, f), "spank") for f in filenames]

setup(
    name="spank",
    author="Matias Surdi",
    author_email="matiassurdi@gmail.com",
    description="Spank",
    version="0.1",
    packages=packages,
    package_data=package_data_files,
    scripts=[
        "spank/bin/spank_webserver",
        "spank/bin/spank_forwarder"]
)
