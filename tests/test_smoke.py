import sys

import src


def test_package_imports():
    """TC-SMK-01: the src package can be imported."""
    assert src is not None


def test_python_version():
    """TC-SMK-02: tests run on Python 3.12 or newer."""
    assert sys.version_info >= (3, 12)
