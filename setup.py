import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-npm-mjs',
    version='0.6.1',
    packages=find_packages(),
    include_package_data=True,
    license='LGPL License',
    description=(
        'A Django package to use npm.js dependencies and transpile ES2015+',
    ),
    long_description=README,
    url='https://github.com/fiduswriter/django-npm-mjs',
    author='Johannes Wilm',
    author_email='johannes@fiduswriter.org',
    install_requires=['Django >= 1.11',
                      'JSON_minify == 0.3.0'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ' +
        'GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
