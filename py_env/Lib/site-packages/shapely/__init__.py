"""""" # start delvewheel patch
def _delvewheel_patch_1_10_0():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'shapely.libs'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-shapely-2.0.7')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-shapely-2.0.7')) as file:
                load_order = file.read().split()
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.LoadLibraryExW.restype = ctypes.wintypes.HMODULE
            kernel32.LoadLibraryExW.argtypes = ctypes.wintypes.LPCWSTR, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD
            for lib in load_order:
                lib_path = os.path.join(os.path.join(libs_dir, lib))
                if os.path.isfile(lib_path) and not kernel32.LoadLibraryExW(lib_path, None, 8):
                    raise OSError('Error loading {}; {}'.format(lib, ctypes.FormatError(ctypes.get_last_error())))


_delvewheel_patch_1_10_0()
del _delvewheel_patch_1_10_0
# end delvewheel patch

from shapely.lib import GEOSException  # NOQA
from shapely.lib import Geometry  # NOQA
from shapely.lib import geos_version, geos_version_string  # NOQA
from shapely.lib import geos_capi_version, geos_capi_version_string  # NOQA
from shapely.errors import setup_signal_checks  # NOQA
from shapely._geometry import *  # NOQA
from shapely.creation import *  # NOQA
from shapely.constructive import *  # NOQA
from shapely.predicates import *  # NOQA
from shapely.measurement import *  # NOQA
from shapely.set_operations import *  # NOQA
from shapely.linear import *  # NOQA
from shapely.coordinates import *  # NOQA
from shapely.strtree import *  # NOQA
from shapely.io import *  # NOQA

# Submodule always needs to be imported to ensure Geometry subclasses are registered
from shapely.geometry import (  # NOQA
    Point,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
    GeometryCollection,
    LinearRing,
)

from shapely import _version

__version__ = _version.get_versions()["version"]

setup_signal_checks()
