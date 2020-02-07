import re
from setuptools import setup

with open("moduledev/__init__.py") as f:
    version = re.search(r"__version__ = '(.*?)'", f.read()).group(1)

setup(
    name='moduledev',
    version=version,
    packages=['moduledev'],
    license='MIT',
    install_requires=['click', 'PyYAML', 'colorama'],
    entry_points={
        'console_scripts': ['moduledev=moduledev.cli:mdcli']
    },
    options={
        'build_scripts': {
            'executable': '/usr/bin/env python3',
        },
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    author='Bob Zimmermann',
    author_email='robert.paul.zimmermann@gmail.com',
    description='''
A set of utilities for developing environment modules
'''
)
