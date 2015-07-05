#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name = "sc3stuff",
    author = "Joachim Saul",
    author_email = "saul@gfz-potsdam.de",
    packages = ['sc3stuff'],
    package_data = {'sc3stuff' : ["__init__.py", "util.py"] }
#   scripts = [ "fdsnxml2sacpz.py" ]
)
