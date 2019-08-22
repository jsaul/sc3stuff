#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.extension import Extension

setup(
    name = "seiscomp",
    py_modules = [
        "seiscomp.client",
        "seiscomp.communication",
        "seiscomp.config",
        "seiscomp.core",
        "seiscomp.datamodel",
        "seiscomp.geo",
        "seiscomp.helpers",
        "seiscomp.io",
        "seiscomp.kernel",
        "seiscomp.logging",
        "seiscomp.math",
        "seiscomp.seismology",
        "seiscomp.setup",
        "seiscomp.shell",
        "seiscomp.system",
        "seiscomp.utils"
    ]
)

