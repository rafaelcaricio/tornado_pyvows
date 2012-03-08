#!/usr/bin/python
# -*- coding: utf-8 -*-

# tornado-pyvows extensions
# https://github.com/rafaelcaricio/tornado-pyvows

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com rafael@caricio.com

import os
from setuptools import setup
from imp import load_source

version = load_source('version', os.path.join("tornado_pyvows", "version.py"))

setup(
    name = 'tornado_pyvows',
    version = '.'.join([str(item) for item in version.__version__]),
    description = "tornado_pyvows are pyvows extensions to tornado web framework.",
    long_description = """
tornado_pyvows are pyvows extensions to tornado web framework.
""",
    keywords = 'testing vows test tdd',
    author = u'Rafael Caricio',
    author_email = 'rafael@caricio.com',
    #Contributors
    #contributor = 'Bernardo Heynemann',
    #contributor_email = 'heynemann@gmail.com',
    #contributor = 'Daniel Truemper',
    #contributor_email = 'truemped@googlemail.com',
    #contributor = 'Norman Rosner',
    #contributor_email = 'norman@rosner.io',
    url = 'https://github.com/rafaelcaricio/tornado_pyvows',
    license = 'MIT',
    classifiers = ['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Operating System :: MacOS',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 2.6',
                   'Topic :: Software Development :: Testing'
    ],
    packages = ['tornado_pyvows'],
    package_dir = {"tornado_pyvows": "tornado_pyvows"},

    install_requires=[
        "pyvows",
        "tornado",
        "pycurl",
        "urllib3"
    ],

)


