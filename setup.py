#!/usr/bin/env python

from setuptools import setup

setup(name='BZRFlag',
      version='1.0',
      description='BZRFlag: BZFlag with Robotic Tanks!',
      author='BYU AML Lab',
      author_email='kseppi@byu.edu',
      url='http://aml.cs.byu.edu/',
      packages=['bzrflag', 'bzagents'],
      package_data = {'': ['*.png', '*.txt', '*.ttf']},
      test_suite = "tests",
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: POSIX :: Linux',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Natural Language :: English',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering :: Artificial Intelligence'],
     )
