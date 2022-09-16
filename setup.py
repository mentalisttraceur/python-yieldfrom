#!/usr/bin/env python

import errno
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from normal import __doc__, __version__

project_directory = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(project_directory, 'README.rst')

readme_file = open(readme_path)
try:
    long_description = readme_file.read()
finally:
    readme_file.close()


def bdist_wheel_tag_check(tag, args=sys.argv):
    if 'bdist_wheel' not in args:
        return False
    if '--python-tag' in args and tag in args:
        return True
    if ('--python-tag=' + tag) in args:
        return True
    return False


if 'sdist' in sys.argv:
    # When building a source distribution, include all variants:
    modules = ['normal', 'no_except_as']
else:
    # When not building a source distribution, we select
    # just the file for the matching Python version:
    modules = ['yieldfrom']

    path_setup_py_uses = os.path.join(project_directory, 'yieldfrom.py')
    if bdist_wheel_tag_check('py26.py3'):
        source_path = os.path.join(project_directory, 'normal.py')
    elif bdist_wheel_tag_check('py20'):
        source_path = os.path.join(project_directory, 'no_except_as.py')
    elif sys.version_info >= (2, 6):
        source_path = os.path.join(project_directory, 'normal.py')
    else:
        source_path = os.path.join(project_directory, 'no_except_as.py')
    try:
        os.unlink(path_setup_py_uses)
    except OSError as error:
        if error.errno != errno.ENOENT:
            raise
    try:
        link = os.link
    except AttributeError:
        link = os.symlink
    link(source_path, path_setup_py_uses)

setup(
    name='yield-from-as-an-iterator',
    version=__version__,
    description=__doc__.split('\n')[0],
    long_description=long_description,
    license='0BSD',
    url='https://github.com/mentalisttraceur/python-yieldfrom',
    author='Alexander Kozhevnikov',
    author_email='mentalisttraceur@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2',
        'Operating System :: OS Independent',
    ],
    py_modules=modules,
)
