"""Install grafanalib."""
# pylint: skip-file
import os

import setuptools


def local_file(name):
    return os.path.relpath(os.path.join(os.path.dirname(__file__), name))


SOURCE = local_file("src")
README = local_file("README.rst")

setuptools_version = tuple(map(int, setuptools.__version__.split(".")[:2]))

# Assignment to placate pyflakes. The actual version is from the exec that
# follows.
__version__ = None

with open(local_file("src/grafanalib/version.py")) as o:
    exec(o.read())

setuptools.setup(
    name="grafanalib",
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=__version__,
    description="Library for building Grafana dashboards",
    long_description=open(README).read(),
    url="https://github.com/jml/grafanalib",
    author="Jonathan M. Lange",
    author_email="jml@mumak.net",
    license="Apache",
    packages=setuptools.find_packages(),
    package_dir={"": SOURCE},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: System :: Monitoring",
    ],
    install_requires=["attrs", "typing-extensions"],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "generate-dashboard=grafanalib._gen:generate_dashboard_script",
            "generate-dashboards=grafanalib._gen:generate_dashboards_script",
        ]
    },
)
