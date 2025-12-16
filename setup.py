import os
from setuptools import setup
from django_o365 import __version__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Framework :: Django",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
]

REQUIREMENTS = [
    "django~=4.2.27",
    "o365~=2.1.8",
]

setup(
    name="django-o365",
    packages=["django_o365"],
    version=__version__,
    description="EmailBackend for Django to work with Microsoft Exchange Online, via o365 package",
    long_description=read("README.md"),
    license="MIT",
    author="Robert Gutschale",
    author_email="r.gutschale@blueshoe.de",
    url="https://github.com/Blueshoe/django-o365",
    install_requires=REQUIREMENTS,
    keywords=["django", "Outlook", "Microsoft", "Exchange", "Blueshoe", "O365"],
    classifiers=CLASSIFIERS,
    include_package_data=True,
    zip_safe=False,
)
