#!/usr/bin/python

from distutils.core import setup

setup(name='jlink',
      version='0.1',
      description='Python wrapper for jlink closed libraries',
      author='Mark Rages',
      author_email='markrages@gmail.com',
      url='https://github.com/markrages/jlinkpy',
      packages=['jlink'],
      package_data={'jlink': ['lib32/*','lib64/*']},
      scripts=['nrfjprog'],
)
