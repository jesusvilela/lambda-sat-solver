import os
from setuptools import setup, Extension
from Cython.Build import cythonize

import sys
# Ensure compilation with C++17 or higher for modern STL features
if sys.platform == "win32":
    extra_compile_args = ['/std:c++17', '/O2', '/openmp:experimental']
else:
    extra_compile_args = ['-std=c++17', '-O3', '-fopenmp']

extensions = [
    Extension(
        "tribridge",
        sources=["backend/cython/tribridge.pyx"],
        language="c++",
        include_dirs=["backend/cpp"],
        extra_compile_args=extra_compile_args,
    )
]

setup(
    name="tribridge_hybrid_solver",
    packages=["backend"],
    ext_modules=cythonize(extensions, compiler_directives={'language_level': "3"}),
)
