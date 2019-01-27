#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import sys
import subprocess
from pathlib import Path

from . import logger


__version__ = '0.1.2'
_logger = logger.create_logger()
PARDIR = Path(__file__).parent
MIN_PYTHON = (3, 7)
MIN_GIT = (2, 20, 0)


if sys.version_info < MIN_PYTHON:
    sys.exit('Python %s.%s or later is required.\n' % MIN_PYTHON)

try:
    p = subprocess.run(('git', '--version'), shell=True, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

    m = re.search(r'(\d+)\.(\d+)\.(\d+)', p.stdout)
    if m:
        git_version = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if git_version < MIN_GIT:
            sys.exit(f'Git {git_version[0].git_version[1].git_version[2]} or later is required.\n')
    else:
        sys.exit(f'Error occured when check git version: {p.stdout}\n')
except subprocess.CalledProcessError as e:
    sys.exit(f'Error occured when check git version: {e.output}\n')
