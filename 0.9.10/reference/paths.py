"""Where things are, resolved from the repository rather than hard coded.

Every path in the toolchain used to be absolute and pointed at a container
that gets reclaimed. This is the one place that knows the layout.
"""
import os

ROOT = os.environ.get('CEOM_ROOT') or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

SPEC = os.path.join(ROOT, 'spec')
ENGAGEMENTS = os.path.join(ROOT, 'engagements')
SUBJECTS = os.path.join(ROOT, 'subjects')
OUT = os.environ.get('CEOM_OUT') or os.path.join(ROOT, 'out')

VERSION = os.environ.get('CEOM_VERSION', '0.9.10')
DICT = os.environ.get('CEOM_DICT') or os.path.join(
    SPEC, 'ceom-%s-field-dictionary.csv' % VERSION)
DB = os.environ.get('CEOM_DB') or os.path.join(OUT, 'ceom.db')
