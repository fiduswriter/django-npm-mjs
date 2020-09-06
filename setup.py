import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-npm-mjs',
    version='2.0.5',
    packages=find_packages(),
    include_package_data=True,
    license='LGPL License',
    description=(
        'A Django package to use npm.js dependencies and transpile ES2015+',
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/fiduswriter/django-npm-mjs',
    author='Johannes Wilm',
    author_email='johannes@fiduswriter.org',
    install_requires=['Django >= 2.2',
                      'JSON_minify == 0.3.0'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ' +
        'GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
