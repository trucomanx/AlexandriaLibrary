#!/usr/bin/python3
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

from clipboard_text_translate.about import __version__
from clipboard_text_translate.about import __package__
from clipboard_text_translate.about import __linux_indicator__
from clipboard_text_translate.about import __author__
from clipboard_text_translate.about import __email__
from clipboard_text_translate.about import __description__
from clipboard_text_translate.about import __url_source__
from clipboard_text_translate.about import __url_funding__
from clipboard_text_translate.about import __url_bugs__

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8");

setup(
    name=__package__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__email__,
    maintainer=__author__,
    maintainer_email=__email__,
    url=__url_source__,
    keywords="writing, translate",  # Optional
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",  # Optional (see note above)
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        'deep-translator'
    ],
    entry_points={
        'console_scripts': [
            __linux_indicator__+'='+__package__+'.indicator:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    package_data={
        __package__: ['icons/logo.png'],
    },
    include_package_data=True, 
    project_urls={  # Optional
        "Bug Reports": __url_bugs__,
        "Funding": __url_funding__,
        "Source": __url_source__,
    },
)
