#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__ for dessia_common module
"""

import pkg_resources
from .core import *
from . import datatools

__version__ = pkg_resources.require("dessia_common")[0].version

FLOAT_TOLERANCE = 1e-9
